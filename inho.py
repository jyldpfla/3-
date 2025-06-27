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
    session["user_id"] = "6854be67f50a270da74cb6d3"
    user_id = session.get("user_id")
    user = None
    notifications = []
    has_notification = False
    if user_id:
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        unread_notes = list(db.notifications.find({
            "user_id": ObjectId(user_id),
            "read": False
        }))
        notifications = [
            {
                "message": n.get("message", ""),
                "link": n.get("notification_link")
            }
            for n in unread_notes
        ]
        has_notification = len(notifications) > 0

    return dict(
        user_info=user,
        notifications=notifications,
        has_notification=has_notification,
        current_page=request.endpoint
    )

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
        for p in project_timeline:
            if p["status"] in ["미완료", "지연", "중단"]:
                p["status"] = "To do"
            elif p["status"] == "진행중":
                p["status"] = "In Progress"
            else:
                p["status"] = "Done"
        
        return render_template("/my_page.html", todo=todo, done=done, doing=doing, personal_timeline=personal_timeline, project_timeline=project_timeline)
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
    status = request.get_json()["status"]
    date = request.get_json()["date"]
    personal_todo_collection.update_one({"_id": ObjectId(id)}, {"$set": {"status": status, "end_date": date}})
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

    notification_docs = db.notifications.find({
        "user_id": user_id
    }).sort("created_at", -1)
    notifications = [
        {
            "message": note.get("message", ""),
            "link": note.get("notification_link"),
            "created_at": note.get("created_at")
        }
        for note in notification_docs
    ]   

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

@app.route('/teamMemberAdd/<project_id>', methods=["GET", "POST"])
def teamMemberAdd(project_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_user_id = ObjectId(session["user_id"])
    project_doc = project_collection.find_one({"_id": ObjectId(project_id)})

    if not project_doc:
        return "해당 프로젝트를 찾을 수 없습니다.", 404

    if project_doc.get("project_manager") != current_user_id:
        manage_url = url_for('teamMemberManage', project_id=project_id)
        return f"<h1><a href='{manage_url}'>팀원 등록은 프로젝트 관리자만 가능합니다.</a></h1>", 403


    if request.method == "POST":
        user_ids = request.form.getlist("_id")
        status_list = request.form.getlist("status")
        object_ids = [ObjectId(uid) for uid in user_ids]

        team_doc = team_collection.find_one({"project_id": ObjectId(project_id)})
        project_doc = project_collection.find_one({"_id": ObjectId(project_id)})
        project_manager_id = ObjectId(session["user_id"])

        if team_doc:
            members = team_doc["member"]
            statuses = team_doc["status"]
            for uid, status in zip(object_ids, status_list):
                if uid in members:
                    index = members.index(uid)
                    del members[index]
                    del statuses[index]
                members.append(uid)
                statuses.append(status)
            team_collection.update_one(
                {"project_id": ObjectId(project_id)},
                {"$set": {"member": members, "status": statuses}}
            )
        else:
            team_collection.insert_one({
                "project_id": ObjectId(project_id),
                "member": object_ids,
                "status": status_list
            })

        # 알림 생성
        manager = user_collection.find_one({"_id": current_user_id})
        for uid in object_ids:
            user = user_collection.find_one({"_id": uid})
            message = f"{manager['name']}님이 프로젝트 '{project_doc['title']}'에 팀원으로 {user['name']}님을 추가했습니다."
            notification_link = url_for('projectDetail', project_id=str(project_doc['_id']))
            notification = {
                "user_id": uid,
                "sender_id": current_user_id,
                "message": message,
                "project_id": ObjectId(project_id),
                "read": False,
                "created_at": datetime.utcnow(),
                "notification_link": url_for('projectDetail', project_id=str(project_doc['_id']))
            }
            db.notifications.insert_one(notification)

        return redirect(url_for("teamMemberManage", project_id=project_id))

    users = list(user_collection.find({"position": {"$ne": "팀장"}}))
    for u in users:
        u["_id"] = str(u["_id"])
    return render_template("teamMemberAdd.html", users=users, project_id=project_id)


@app.route('/teamMemberManage/<project_id>')
def teamMemberManage(project_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    current_user_id = ObjectId(session["user_id"])
    project_obj_id = ObjectId(project_id)
    project_doc = project_collection.find_one({"_id": project_obj_id})
    is_manager = (project_doc.get("project_manager") == current_user_id)
    if not project_doc:
        return "해당 프로젝트를 찾을 수 없습니다.", 404
    project_manager_id = project_doc.get("project_manager")
    
    team_doc = team_collection.find_one({"project_id": project_obj_id})
    member_ids = team_doc.get("member", []) if team_doc else []
    status_list = team_doc.get("status", []) if team_doc else []
    
    if project_manager_id not in member_ids:
        member_ids.insert(0, project_manager_id)
        status_list.insert(0, "팀장")
    user_info_map = {
        str(user["_id"]): user
        for user in user_collection.find(
            {"_id": {"$in": member_ids}}, {"name": 1, "email": 1, "role": 1}
        )
    }
    
    query = request.args.get("q", "").lower()
    
    members = []
    for i, member_id in enumerate(member_ids):
        user = user_info_map.get(str(member_id))
        if user:
            if query and query not in user.get("name", "").lower() and query not in user.get("email", "").lower():
                continue
            members.append({
                "_id": str(member_id),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "status": status_list[i],
                "is_manager": member_id == project_manager_id
            })
        elif member_id == project_manager_id:
            members.append({
                "_id": "",
                "name": "",
                "email": "",
                "role": "",
                "status": status_list[i],
                "is_manager": True
            })

    if not members:
        members.append({
            "_id": "",
            "name": "",
            "email": "",
            "role": "",
            "status": "-",
            "is_manager": True
        })

    notification_docs = db.notifications.find({
        "user_id": current_user_id,
        "read": False
    })
    notifications = [
        {
            "message": doc.get("message", ""),
            "link": doc.get("notification_link")
        }
        for doc in notification_docs
    ]
    has_notification = len(notifications) > 0
    return render_template(
        'teamMemberManage.html',
        project_id=project_id,
        team_members=members,
        notifications=notifications,
        has_notification=has_notification,
        is_manager=is_manager
    )

@app.route('/teamMemberUpdate/<project_id>/<member_id>', methods=["POST"])
def teamMemberUpdate(project_id, member_id):
    new_status = request.form.get("status")
    team_doc = team_collection.find_one({"project_id": ObjectId(project_id)})
    if not team_doc:
        return redirect(url_for("teamMemberManage", project_id=project_id))
    try:
        index = team_doc["member"].index(ObjectId(member_id))
    except ValueError:
        return redirect(url_for("teamMemberManage", project_id=project_id))
    team_doc["status"][index] = new_status
    team_collection.update_one(
        {"project_id": ObjectId(project_id)},
        {"$set": {"status": team_doc["status"]}}
    )

    # --- 알림 생성 코드 추가 ---
    project_doc = project_collection.find_one({"_id": ObjectId(project_id)})
    manager_id = project_doc.get("project_manager")
    manager = user_collection.find_one({"_id": manager_id})
    member = user_collection.find_one({"_id": ObjectId(member_id)})
    message = f"{manager['name']}님이 프로젝트 '{project_doc['title']}'에서 {member['name']}님의 상태를 '{new_status}'(으)로 변경했습니다."
    notification_link = url_for('projectDetail', project_id=str(project_doc['_id']))
    notification = {
        "user_id": ObjectId(member_id),
        "sender_id": manager_id,
        "message": message,
        "project_id": ObjectId(project_id),
        "read": False,
        "created_at": datetime.utcnow(),
        "notification_link": url_for('projectDetail', project_id=str(project_doc['_id']))
    }
    db.notifications.insert_one(notification)

    return redirect(url_for("teamMemberManage", project_id=project_id))

@app.route('/teamMemberDelete/<project_id>/<member_id>', methods=["POST"])
def teamMemberDelete(project_id, member_id):
    team_doc = team_collection.find_one({"project_id": ObjectId(project_id)})
    if not team_doc:
        return redirect(url_for("teamMemberManage", project_id=project_id))
    try:
        index = team_doc["member"].index(ObjectId(member_id))
    except ValueError:
        return redirect(url_for("teamMemberManage", project_id=project_id))
    del team_doc["member"][index]
    del team_doc["status"][index]
    team_collection.update_one(
        {"project_id": ObjectId(project_id)},
        {"$set": {"member": team_doc["member"], "status": team_doc["status"]}}
    )
    return redirect(url_for("teamMemberManage", project_id=project_id))

# ===== wonji_app.py에서 가져온 프로젝트 관리 라우트 및 함수 추가 =====
def to_str(date):
    if not date:
        return ""
    if isinstance(date, str):
        return date  # 이미 문자열이면 그대로 반환
    return date.strftime("%Y-%m-%d")  # datetime → 문자열

@app.route("/projectList")
def projectList():
    project_list = list(project_collection.find())
    done = [t for t in project_list if t['status'] == '완료']
    doing = [t for t in project_list if t['status'] == '진행중']
    wait = [t for t in project_list if t['status'] == '진행 대기']
    for project in project_list:
        manager = user_collection.find_one({"_id": project["project_manager"]})
        project["project_manager"] = manager["name"] if manager else "-"
        project["start_date"] = to_str(project.get("start_date"))
        project["end_date"] = to_str(project.get("end_date"))
    status_order = {"진행 대기": 0, "진행중": 1, "완료": 2}
    project_list.sort(key=lambda x: status_order.get(x["status"], 99))
    return render_template("/projectList.html", project_list=project_list, done=done, doing=doing, wait=wait)

@app.route("/projectAdd", methods=["GET", "POST"])
def projectAdd():
    if request.method == "POST":
        # 📥 값 수집
        title = request.form.get("name")
        client = request.form.get("client")
        manager_id = request.form.get("project_manager")
        start_str = request.form.get("start")
        end_str = request.form.get("end")
        status = request.form.get("status")
        description = request.form.get("description")

        # 📅 날짜 변환
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")

        # 📌 프로젝트 문서 저장
        project = {
            "title": title,
            "client": client,
            "project_manager": ObjectId(manager_id),
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "description": description,
            "schedule_id": None
        }
        result = project_collection.insert_one(project)
        new_project_id = result.inserted_id

        # ✅ timeline 일정 자동 생성
        timeline_doc = {
            "title": f"[{title}] 프로젝트 일정",
            "user_id": ObjectId(manager_id),
            "start_date": start_date,
            "end_date": end_date,
            "type": "프로젝트",
            "status": status,
            "content": description,
            "project_id": new_project_id,
            "member": [],
            "updated_at": datetime.utcnow()
        }
        timeline_collection.insert_one(timeline_doc)

        return redirect(url_for('projectList'))

    # GET 요청 - 폼 렌더링
    user_list = list(user_collection.find({"position": "팀장"}))
    return render_template("/projectAdd.html", user_list=user_list)

@app.route("/projectUpdate/<project_id>", methods=["GET", "POST"])
def projectUpdate(project_id):
    if request.method == "POST":
        # 📥 값 받아오기
        name = request.form.get("name")
        client = request.form.get("client")
        start_date_str = request.form.get("start")
        end_date_str = request.form.get("end")
        status = request.form.get("status")
        description = request.form.get("description")

        # 📅 문자열 → 날짜 변환
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 📌 프로젝트 DB 업데이트
        project_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {
                "title": name,
                "client": client,
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "description": description,
                "schedule_id": None
            }}
        )

        # 🔁 타임라인 일정도 함께 수정
        timeline_collection.update_many(
            {"project_id": ObjectId(project_id)},
            {"$set": {
                "start_date": start_date,
                "end_date": end_date
            }}
        )

        return redirect(url_for('projectDetail', project_id=project_id))

    # ✅ 여기가 GET 요청 처리
    project = project_collection.find_one({"_id": ObjectId(project_id)})
    manager_doc = user_collection.find_one({"_id": project.get("project_manager")})
    manager = manager_doc["name"] if manager_doc else "알 수 없음"
    project["manager_name"] = manager
    user_list = list(user_collection.find({"position": "팀장"}))
    
    # 📅 날짜 포맷 처리
    def to_str(date):
        if not date:
            return ""
        if isinstance(date, str):
            return date  # 문자열이면 그대로 반환
        return date.strftime("%Y-%m-%d")  # datetime 객체면 포맷팅

    project["start_date"] = to_str(project.get("start_date"))
    project["end_date"] = to_str(project.get("end_date"))

    return render_template("/projectUpdate.html", project=project, user_list=user_list)

@app.route('/projectDetail/<project_id>')
def projectDetail(project_id):
    project = project_collection.find_one({"_id": ObjectId(project_id)})
    try:
        manager = user_collection.find_one({"_id": project["project_manager"]})["name"]
    except Exception as e:
        manager = "-"
    project["manager_name"] = manager
    project["start_date"] = to_str(project.get("start_date"))
    project["end_date"] = to_str(project.get("end_date"))
    team_map = {t["project_id"]: t["member"] for t in team_collection.find({})}
    project["team"] = [
        user["name"] for user in user_collection.find(
            {"_id": {"$in": team_map.get(ObjectId(project_id), [])}},
            {"_id": 0, "name": 1}
        )
    ]
    return render_template("/projectDetail.html", project=project)

@app.route("/faq")
def faq_main():
    faqs = list(board_collection.find().sort("create_date", -1))
    return render_template("faq_main.html", faqs=faqs)

@app.route("/faq/insert", methods=["POST"])
def faq_insert():
    title = request.form.get("title")
    content = request.form.get("content")
    category = request.form.get("category")
    now = datetime.now(timezone('Asia/Seoul'))
    if title and content and category:
        board_collection.insert_one({
            "title": title,
            "content": content,
            "category": category,
            "create_date": now,
            "update_date": now
        })
    return redirect(url_for("faq_main"))

@app.route("/faq/update/<faq_id>", methods=["GET", "POST"])
def faq_update(faq_id):
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")
        now = datetime.now(timezone('Asia/Seoul'))
        if title and content and category:
            board_collection.update_one(
                {"_id": ObjectId(faq_id)},
                {"$set": {
                    "title": title,
                    "content": content,
                    "category": category,
                    "update_date": now
                }}
            )
        return redirect(url_for("faq_main"))
    else:
        faq = board_collection.find_one({"_id": ObjectId(faq_id)})
        return render_template("faq_update.html", faq=faq)

@app.route("/faq/delete/<faq_id>", methods=["POST"])
def faq_delete(faq_id):
    board_collection.delete_one({"_id": ObjectId(faq_id)})
    return redirect(url_for("faq_main"))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)