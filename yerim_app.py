from collections import defaultdict
from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime, timedelta, timezone

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
session_key = os.getenv("SECRET_KEY")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

client = MongoClient(uri)
db = client['team3']

project_collection = db["projects"]
user_collection = db["users"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]
timeline_collection = db["timeline"]

@app.context_processor
def inject_user():
    session["user_id"] = "6854be045d8c554194fe197b"
    user_id = session.get("user_id")
    if user_id:
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        return dict(user_info=user)
    else:
        return redirect(url_for("/"))

@app.route("/")
def home():
    projects = list(project_collection.find({}))
    project_pipeline = [
        {
            "$match": {
                "project_id": { "$ne": None }
            }
        },
        {
            "$project": {
                "project_id": 1,
                "status": 1,
                "is_done": {
                    "$cond": [{ "$eq": ["$status", "완료"] }, 1, 0]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "project_id": "$project_id",
                    "status": "$status"
                },
                "count": { "$sum": 1 },
                "done_count": { "$sum": "$is_done" }  
            }
        },
        {
            "$group": {
                "_id": "$_id.project_id",
                "statuses": {
                    "$push": {
                        "status": "$_id.status",
                        "count": "$count"
                    }
                },
                "total": { "$sum": "$count" },
                "done": { "$sum": "$done_count" } 
            }
        },
        {
            "$addFields": {
                "percentage": {
                    "$cond": [
                        { "$eq": ["$total", 0] },
                        0,
                        { "$multiply": [ { "$divide": ["$done", "$total"] }, 100 ] }
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "project_id": "$_id",
                "percentage": 1,
                "total": "$total"
            }
        }
    ]
    
    project_statuses = list(timeline_collection.aggregate(project_pipeline))
    # 딕셔너리로 변환
    status_map = {s["project_id"]: round(s["percentage"], 1) for s in project_statuses}
    team_map = {t["project_id"]: t["member"] for t in team_collection.find({})}

    # percent 붙이기
    for p in projects:
        if p["status"] == "완료":
            p["percentage"] = 100
        else:
            p["percentage"] = 0 if status_map.get(p["_id"], 0) == 0.0 else status_map.get(p["_id"], 0)
        p["manager_name"] = user_collection.find_one({"_id": p["project_manager"]})["name"]
        p["team"] = [
            user["name"] for user in user_collection.find(
                { "_id": { "$in": team_map.get(p["_id"], []) } },
                {"_id": 0, "name": 1}
            )
        ]
    
    # 일정 가져오기
    target_date = datetime.strptime("2025-06-24", "%Y-%m-%d")

    # 날짜 범위 설정
    start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=2)
    timeline = list(timeline_collection.find({"end_date": {"$gte": start, "$lte": end}, "project_id": { "$ne": None }}))
    grouped_timeline = defaultdict(list) # defaultdict: key값 없을 때도 바로 append 가능하도록 설정
    
    for t in timeline:
        t["start_date"] = datetime.strftime(t["start_date"], "%m월 %d일 (%a)")
        t["end_date"] = datetime.strftime(t["end_date"], "%m월 %d일 (%a)")
        
        grouped_timeline[t["end_date"]].append(t)
    
    return render_template("/index.html", projects=projects, timeline=grouped_timeline, today=target_date.strftime("%m월 %d일 (%a)"))

@app.route("/example")
def example():
    return render_template("/example.html")

@app.route("/mypage")
def mypage():
    user_id = ObjectId(session.get("user_id"))
    # user 개인 정보 구성
    user = user_collection.find_one({"_id": user_id})

    # 개인 프로젝트 개수
    team_pipeline = [
        {
            "$match": {
                "member": user['_id']
            }
        },
        {
            "$project": {
                "_id": 0,
                "project_id": 1
            }
        }
    ]
    manager_pipeline = [
        {
            "$match": {
                "project_manager": user['_id']
            }
        },
        {
            "$project": {
                "_id": 1
            }
        }
    ]
    project_id_list = [data["project_id"] for data in team_collection.aggregate(team_pipeline)]
    project_collection.aggregate(manager_pipeline)
    for data in project_collection.aggregate(manager_pipeline):
        project_id_list.append(data["_id"])
    
    # 진행중, 완료 프로젝트 분류
    project_pipeline = [
        {
            "$match": {
                "_id": {"$in": project_id_list}
            }
        },
        {
            "$project": {
                "_id": 1,
                "project_id": 1,
                "title": 1,
                "status": 1
            }
        }
    ]
    project_list = list(project_collection.aggregate(project_pipeline))
    done = [t for t in project_list if t['status'] == '완료']
    doing = [t for t in project_list if t['status'] in ['진행중', '진행 대기']]
    
    # user별 할 일 데이터
    todo = list(personal_todo_collection.find({"user_id": user["_id"]}).sort("end_date", 1))  
    today_str = datetime.today().strftime("%Y-%m-%d")
    for t in todo:
        t["end_date"] = "오늘" if t["end_date"] == today_str else t["end_date"]
    
    # user별 일정
    timeline_pipeline = [
        {
            "$match": {
                "$or": [
                {
                    "$and": [
                    { "project_id": None },
                    { "user_id": user['_id'] }  # 예: ObjectId("...") 또는 문자열
                    ]
                },
                {
                    "$and": [
                    { "project_id": { "$in": project_id_list } },  # project_ids는 리스트
                    {
                        "$or": [
                        { "member": user['_id'] },           # 배열 안에 포함된 경우
                        { "user_id": user['_id'] }
                        ]
                    }
                    ]
                }
                ]
            }
        },
        { "$sort": { "end_date": 1 } }
    ]
    timeline = list(timeline_collection.aggregate(timeline_pipeline))
    for t in timeline:
        t["start_date"] = datetime.strftime(t["start_date"], "%Y-%m-%d")
        t["end_date"] = datetime.strftime(t["end_date"], "%Y-%m-%d")
    personal_timeline = [t for t in timeline if t['project_id'] == None] # 개인 일정
    project_timeline = [t for t in timeline if t['project_id'] in project_id_list]# 프로젝트 내 일정
    for p in project_timeline:
        if p["status"] in ["미완료", "지연", "중단"]:
            p["status"] = "To do"
        elif p["status"] == "진행중":
            p["status"] = "In Progress"
        else:
            p["status"] = "Done"
    
    return render_template("/my_page.html", todo=todo, done=done, doing=doing, personal_timeline=personal_timeline, project_timeline=project_timeline)

@app.route("/mypage/add_task", methods=["POST"])
def add_task():
    user_id = request.form.get("user_id")
    content = request.form.get("content")
    end_date = request.form.get("date")
    status = "To do"
    personal_todo_collection.insert_one({
        "user_id": ObjectId(user_id),
        "content": content,
        "end_date": end_date,
        "status": status
    })
    return redirect("/mypage")

@app.route("/mypage/update_task", methods=['POST'])
def update_task():
    id = request.get_json()["_id"]
    status = request.get_json()["status"]
    date = request.get_json()["date"]
    personal_todo_collection.update_one({"_id": ObjectId(id)}, {"$set": {"status": status, "end_date": date}})
    return redirect("/mypage")

@app.route("/mypage/del_task", methods=['POST'])
def del_task():
    id = request.get_json()["_id"]
    personal_todo_collection.delete_one({"_id": ObjectId(id)})
    return redirect("/mypage")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)