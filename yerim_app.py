from collections import defaultdict
from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime, timedelta
from pytz import timezone
from math import ceil
import json

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
# session_key = os.getenv("SECRET_KEY")
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
    session["user_id"] = "6853aebf690a71fa9ad4b6e3"
    user_id = session.get("user_id")
    if user_id:
        user = user_collection.find_one({"_id": ObjectId(user_id)})

        # 안 읽은 알림 불러오기
        unread_notes = list(db.notifications.find({
            "user_id": ObjectId(user_id),
            "read": False
        }))
        messages = [n["message"] for n in unread_notes]
        has_notification = len(messages) > 0

        return dict(
            user_info=user,
            notifications=messages,
            has_notification=has_notification
        )
    return dict()

@app.context_processor
def inject_global_context():
    user_id = session.get("user_id")
    if user_id:
        user = user_collection.find_one({"_id": ObjectId(user_id)})

        # 안 읽은 알림 불러오기
        unread_notes = list(db.notifications.find({
            "user_id": ObjectId(user_id),
            "read": False
        }))
        messages = [n["message"] for n in unread_notes]
        has_notification = len(messages) > 0

        return dict(
            user_info=user,
            notifications=messages,
            has_notification=has_notification
        )
    return dict()


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
            
        try:
            p["manager_name"] = user_collection.find_one({"_id": p["project_manager"]})["name"]
        except Exception as e:
            p["manager_name"] = "-"
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
    try:
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
        other_timeline = list(timeline_collection.find({
            "$and": [
                { "project_id": { "$nin": project_id_list } }, 
                { "project_id": { "$ne": None } },
                {
                    "$or": [
                        { "member": user['_id'] },           # 배열 안에 포함된 경우
                        { "user_id": user['_id'] }
                    ]
                }
            ]
        }))
        for t in other_timeline:
            t["start_date"] = datetime.strftime(t["start_date"], "%Y-%m-%d")
            t["end_date"] = datetime.strftime(t["end_date"], "%Y-%m-%d")
        for p in project_timeline:
            if p["status"] in ["미완료", "지연", "중단"]:
                p["status"] = "To do"
            elif p["status"] == "진행중":
                p["status"] = "In Progress"
            else:
                p["status"] = "Done"
        all_projects = list(project_collection.find({"_id": {"$nin": project_id_list}}))
        return render_template("/my_page.html", todo=todo, done=done, doing=doing, all_projects=all_projects, personal_timeline=personal_timeline, project_timeline=project_timeline, other_timeline=other_timeline)
    except Exception as e:
        print(f"유저 정보를 찾을 수 없습니다: {e}")
        return redirect("/login")

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
    content = request.get_json()["content"]
    status = request.get_json()["status"]
    date = request.get_json()["date"]
    personal_todo_collection.update_one({"_id": ObjectId(id)}, {"$set": {"content": content, "status": status, "end_date": date}})
    return redirect("/mypage")

@app.route("/mypage/del_task", methods=['POST'])
def del_task():
    id = request.get_json()["_id"]
    personal_todo_collection.delete_one({"_id": ObjectId(id)})
    return redirect("/mypage")

# ===== inho.py에서 가져온 라우트 및 함수 추가 =====
@app.route("/notifications")
def show_notifications():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    kst = timezone("Asia/Seoul")

    notifications = list(db.notifications.find({"user_id": user_id}).sort("created_at", -1))

    for note in notifications:
        if "created_at" in note and isinstance(note["created_at"], datetime):
            note["created_at_kst"] = note["created_at"].replace(tzinfo=timezone("UTC")).astimezone(kst)
        else:
            note["created_at_kst"] = "시간 없음"

    # 페이지네이션을 위한 코드 추가
    per_page = 10  # 한 페이지에 보여줄 알림 수
    page = int(request.args.get("page", 1))
    total_notifications = len(notifications)
    total_pages = ceil(total_notifications / per_page)

    # 현재 페이지에 해당하는 알림만 추출
    start = (page - 1) * per_page
    end = start + per_page
    notifications = notifications[start:end]

    return render_template(
        'notifications.html',
        notifications=notifications,
        page=page,
        total_pages=total_pages,
        current_page='notifications'
    )

@app.route("/notifications/read/<notification_id>", methods=["POST"])
def mark_single_notification_read(notification_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True}}
    )
    return redirect(url_for("show_notifications"))

@app.route("/notifications/read", methods=["POST"])
def mark_notifications_as_read():
    if "user_id" not in session:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    current_user_id = ObjectId(session["user_id"])

    db.notifications.update_many(
        {"user_id": current_user_id, "read": False},
        {"$set": {"read": True}}
    )
    return jsonify({"success": True})

@app.route("/board")
def board():
    posts = list(board_collection.find({"category": "자유"}))
    user_id = ObjectId(session.get("user_id"))
    
    for p in posts:
        if p["title"] == "" or p["title"] == None:
            p["title"] = "-"
        p["writer"] = user_collection.find_one({"_id": user_id})["name"]
        
        p["update_date"] = p["update_date"].strftime("%Y-%m-%d %H:%M")
    
    posts.sort(key=lambda x: x.get("no", 0), reverse=True)
    return render_template("freeboard_main.html", posts=posts)

@app.route("/board/detail/<id>")
def freeboard_detail(id):
    post = board_collection.find_one({"_id": ObjectId(id)}) 
    post["writer"] = user_collection.find_one({"_id": post["user_id"]})["name"]

    # 2. 원하는 형식으로 다시 문자열로 저장
    post["update_date"] = post["update_date"].strftime("%Y-%m-%d %H:%M")
    return render_template("freeboard_detail.html", post=post)

@app.route('/board_insert', methods=['GET', 'POST'])
def insert_form():
    user_id = session.get("user_id")
    if request.method == 'GET':
        return render_template('/freeboard_insert.html')
    title = request.form.get("title")
    content = request.form.get("content")

    board_collection.insert_one({
        "title": title,
        "category": "자유",
        "user_id": ObjectId(user_id),
        "content": content,
        "create_date": datetime.now(),
        "update_date": datetime.now()
    })

    return redirect(url_for("board"))

@app.route('/board_delete', methods=['POST'])
def delete():
    id = request.get_json()["_id"]
    board_collection.delete_one({"_id": ObjectId(id)})

    return redirect(url_for("board"))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)