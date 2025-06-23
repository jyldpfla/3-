from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime

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

@app.route("/")
def home():
    session["user_id"] = "6853aebf690a71fa9ad4b6e3"
    user_id = ObjectId(session.get("user_id"))
    
    project = list(project_collection.find({}))
    project_pipeline = [
        {
            "$match": {
                "project_id": { "$ne": None } 
            }
        },
        {
            "$group": {
                "_id": {
                    "project_id": "$project_id",
                    "status": "$status"
                },
                "count": { "$sum": 1 }
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
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "project_id": "$_id",
                "statuses": 1
            }
        }
    ]
    project_status = list(timeline_collection.aggregate(project_pipeline))
    
    return render_template("/index.html")

@app.route("/example")
def example():
    return render_template("/example.html")

@app.route("/mypage")
def mypage():
    session["user_id"] = "6853aebf690a71fa9ad4b6e3"
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
    todo = list(personal_todo_collection.find({"user_id": ObjectId("6853aebf690a71fa9ad4b6e3")}).sort("end_date", 1))  
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
    personal_timeline = [t for t in timeline if t['project_id'] == None] # 개인 일정
    project_timeline = [t for t in timeline if t['project_id'] in project_id_list]# 프로젝트 내 일정
    print(personal_timeline)
    
    return render_template("/my_page.html", user_info=user, todo=todo, done=done, doing=doing, personal_timeline=personal_timeline, project_timeline=project_timeline)

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
    print(request.data)
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