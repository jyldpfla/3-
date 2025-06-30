from collections import defaultdict
from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime, timedelta, date, time
from pytz import timezone
from math import ceil
import json
from functools import wraps
from collections import OrderedDict
import re

# env 파일 로드
load_dotenv()
id = os.getenv("USER_ID")
pw = os.getenv("USER_PW")
uri = f"mongodb+srv://{id}:{pw}@team3.fxbwcnh.mongodb.net/"

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
def inject_user_context():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return dict()

        # 사용자 정보 (이름, 직급, 부서만)
        user = user_collection.find_one(
            {"_id": ObjectId(user_id)},
            {"name": 1, "position": 1, "department": 1}
        )

        # 알림 가져오기
        notifications = []
        messages = []
        has_notification = False

        if "notifications" in db.list_collection_names():
            unread_notes = list(db.notifications.find({
                "user_id": ObjectId(user_id),
                "read": False
            }))
            notifications = [
                {
                    "message": n.get("message", ""),
                    "link": n.get("notification_link")
                } for n in unread_notes
            ]
            messages = [n.get("message", "") for n in unread_notes]
            has_notification = len(messages) > 0

        return dict(
            user_info=user,
            notifications=notifications,
            has_notification=has_notification,
            current_page=request.endpoint
        )
    except Exception as e:
        print(f"[inject_user_context] Error: {e}")
        return dict()



# ========== yerim - main page ==========
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
    status_map = {s["project_id"]: int(round(s["percentage"], 0)) for s in project_statuses}
    team_map = {t["project_id"]: t["member"] for t in team_collection.find({})}

    # percent 붙이기
    for p in projects:
        if p["status"] == "완료":
            p["percentage"] = 100
        else:
            p["percentage"] = 0 if status_map.get(p["_id"], 0) == 0 else status_map.get(p["_id"], 0)
            
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
    target_date = datetime.today()


    # 날짜 범위 설정
    start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=2)
    timeline = list(timeline_collection.find({"end_date": {"$gte": start, "$lte": end}, "project_id": { "$ne": None }}).sort("end_date", 1))
    grouped_timeline = defaultdict(list) # defaultdict: key값 없을 때도 바로 append 가능하도록 설정
    
    for t in timeline:
        t["start_date"] = datetime.strftime(t["start_date"], "%m월 %d일 (%a)")
        t["end_date"] = datetime.strftime(t["end_date"], "%m월 %d일 (%a)")
        
        grouped_timeline[t["end_date"]].append(t)
    
    board_time = start - timedelta(days=-5)
    board = board_collection.find({"update_date": {"$lte": board_time}})
    
    return render_template("/index.html", projects=projects, timeline=grouped_timeline, today=target_date.strftime("%m월 %d일 (%a)"), board=board)

@app.route("/example")
def example():
    return render_template("/example.html")

# ========== yerim - mypage ==========
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

# ========== inho - notification ==========
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

    per_page = 10
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

# ========== inho - team ==========
@app.route('/teamMemberAdd/<project_id>', methods=["GET", "POST"])
def teamMemberAdd(project_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_user_id = ObjectId(session["user_id"])
    project_doc = project_collection.find_one({"_id": ObjectId(project_id)})

    if not project_doc:
        return "해당 프로젝트를 찾을 수 없습니다.", 404

    if request.method == "POST":
        user_ids = request.form.getlist("_id")
        status_list = request.form.getlist("status")
        object_ids = [ObjectId(uid) for uid in user_ids]

        team_doc = team_collection.find_one({"project_id": ObjectId(project_id)})
        project_doc = project_collection.find_one({"_id": ObjectId(project_id)})

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
            {"_id": {"$in": member_ids}}, {"name": 1, "email": 1, "position": 1}
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
                "position": user.get("position"),
                "status": status_list[i],
                "is_manager": member_id == project_manager_id
            })
        elif member_id == project_manager_id:
            members.append({
                "_id": "",
                "name": "",
                "email": "",
                "position": "",
                "status": status_list[i],
                "is_manager": True
            })

    if not members:
        members.append({
            "_id": "",
            "name": "",
            "email": "",
            "position": "",
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

# ========== wonji - project ==========
# ✅ 로그인 제한용 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def to_str(date):
    if not date:
        return ""
    if isinstance(date, str):
        return date  # 이미 문자열이면 그대로 반환
    return date.strftime("%Y-%m-%d")  # datetime → 문자열

@app.route("/projectList")
def projectList():
    def to_str(date):
        if not date:
            return ""
        return date[:10] if isinstance(date, str) else date.strftime("%Y-%m-%d")

    page = int(request.args.get('page', 1))
    per_page = 10
    skip = (page - 1) * per_page

    total_projects = project_collection.count_documents({})
    total_pages = (total_projects + per_page - 1) // per_page

    project_list = list(project_collection.find().skip(skip).limit(per_page))

    for project in project_list:
        manager = user_collection.find_one({"_id": project["project_manager"]})
        project["project_manager"] = manager["name"] if manager else "알 수 없음"
        project["start_date"] = to_str(project.get("start_date"))
        project["end_date"] = to_str(project.get("end_date"))

    done = [t for t in project_list if t['status'] == '완료']
    doing = [t for t in project_list if t['status'] == '진행중']
    wait = [t for t in project_list if t['status'] == '진행 대기']

    return render_template(
        "/projectList.html",
        project_list=project_list,
        done=done,
        doing=doing,
        wait=wait,
        page=page,
        total_pages=total_pages
    )

from datetime import datetime

# ✅ 로그인 필요
@app.route("/projectAdd", methods=["GET", "POST"])
@login_required
def projectAdd():
    if request.method == "POST":
        title = request.form.get("name")
        client = request.form.get("client")
        manager_id = request.form.get("project_manager")
        start_str = request.form.get("start")
        end_str = request.form.get("end")
        status = request.form.get("status")
        description = request.form.get("description")

        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")

        project = {
            "title": title,
            "client": client,
            "project_manager": ObjectId(manager_id),
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "description": description,
        }
        project_collection.insert_one(project)
        return redirect(url_for('projectList'))

    user_list = list(user_collection.find({"position": "팀장"}))
    for user in user_list:
        user['_id'] = str(user['_id'])

    return render_template("/projectAdd.html", user_list=user_list)

# ✅ 로그인 필요
@app.route("/projectUpdate/<project_id>", methods=["GET", "POST"])
@login_required
def projectUpdate(project_id):
    if request.method == "POST":
        name = request.form.get("name")
        client = request.form.get("client")
        manager_id = request.form.get("project_manager")
        start_date_str = request.form.get("start")
        end_date_str = request.form.get("end")
        status = request.form.get("status")
        description = request.form.get("description")

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        project_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {
                "title": name,
                "client": client,
                "project_manager": ObjectId(manager_id),
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "description": description,
            }}
        )

        return redirect(url_for('projectDetail', project_id=project_id))

    project = project_collection.find_one({"_id": ObjectId(project_id)})
    manager_doc = user_collection.find_one({"_id": project.get("project_manager")})
    manager = manager_doc["name"] if manager_doc else "알 수 없음"
    project["manager_name"] = manager

    user_list = list(user_collection.find({"position": "팀장"}))

    def to_str(date):
        if not date:
            return ""
        if isinstance(date, str):
            return date
        return date.strftime("%Y-%m-%d")

    project["start_date"] = to_str(project.get("start_date"))
    project["end_date"] = to_str(project.get("end_date"))

    return render_template("/projectUpdate.html", project=project, user_list=user_list)

@app.route('/projectDetail/<project_id>')
@login_required
def projectDetail(project_id):
    project = project_collection.find_one({"_id": ObjectId(project_id)})
    DEFAULT_MANAGER_ID = ObjectId("6853aebf690a71fa9ad4b6e3")

    manager_id = project.get("project_manager", DEFAULT_MANAGER_ID)
    try:
        manager_id = ObjectId(manager_id)
    except:
        manager_id = DEFAULT_MANAGER_ID

    manager_doc = user_collection.find_one({"_id": manager_id})
    manager = manager_doc["name"] if manager_doc else "알 수 없음"
    project["manager_name"] = manager

    def to_str(date):
        if not date:
            return ""
        return date[:10] if isinstance(date, str) else date.strftime("%Y-%m-%d")

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

# ✅ 로그인 필요
@app.route("/projectDelete/<project_id>", methods=["POST"])
@login_required
def projectDelete(project_id):
    project_collection.delete_one({"_id": ObjectId(project_id)})
    return redirect(url_for('projectList'))

# ========== hongseok - timeline ==========

# 일정 타입
TYPE_TAG_CLASS_MAP = {"개인": "personal-schedule-tag", "회사": "company-schedule-tag", "프로젝트": "project-schedule-tag"}

# 일정 타입에 따른 상태 옵션
STATUS_OPTIONS_BY_TYPE = {
    "개인": [{"value": "연차", "text": "연차"}, {"value": "월차", "text": "월차"},
        {"value": "병가", "text": "병가"}, {"value": "출장", "text": "출장"}],
    "회사": [{"value": "사내일정", "text": "사내일정"}],
    "프로젝트": [{"value": "진행중", "text": "진행중"}, {"value": "진행대기", "text": "진행대기"},
        {"value": "지연", "text": "지연"}, {"value": "중단", "text": "중단"}, {"value": "완료", "text": "완료"}]}

# 일정 상태에 따른 태그 클래스
STATUS_TAG_CLASS_MAP = {
    "연차": "vacation-year-tag", "월차": "vacation-month-tag", "병가": "sick-leave-tag", "출장": "travel-tag",
    "사내일정": "company-event-tag",
    "진행중": "status-inprogress-tag", "진행대기": "status-wait-tag", "지연": "status-delayed-tag",
    "중단": "status-stopped-tag", "완료": "status-completed-tag",
}

# 일정 타입 옵션 (드롭다운)
SCHEDULE_TYPE_OPTIONS = [{"value": "전체", "text": "전체 일정"}, {"value": "개인", "text": "개인 일정"},
    {"value": "회사", "text": "회사 일정"}, {"value": "프로젝트", "text": "프로젝트 일정"}]

# 헬퍼 함수
# 사용자 이름으로 user_id (ObjectId) 찾아 반환
def get_user_id_by_name(user_name):
    user = user_collection.find_one({"name": user_name}, {"_id": 1})
    return user["_id"] if user else None

# user_id (ObjectId)로 사용자 이름 찾아 반환
def get_user_name_by_id(user_obj_id):
    try:
        if not isinstance(user_obj_id, ObjectId):
            user_obj_id = ObjectId(user_obj_id)
        user = user_collection.find_one({"_id": user_obj_id}, {"name": 1})
        return user["name"] if user else None
    except Exception as e:
        return None

# user_id 리스트로 사용자 이름 리스트 찾아 반환
def get_user_names_by_ids(user_ids):
    if not user_ids:
        return []
    try:
        valid_ids = []
        for id_val in user_ids:
            if isinstance(id_val, ObjectId):
                valid_ids.append(id_val)
            elif isinstance(id_val, str) and ObjectId.is_valid(id_val):
                valid_ids.append(ObjectId(id_val))
        if not valid_ids:
            return []
        users = user_collection.find({"_id": {"$in": valid_ids}}, {"name": 1})
        return [user["name"] for user in users]
    except Exception as e:
        return []

# 프로젝트 제목으로 project_id (ObjectId) 찾아 반환
def get_project_id_by_title(project_title):
    project = project_collection.find_one({"title": project_title})
    return project["_id"] if project else None

# project_id (ObjectId)로 프로젝트 제목 찾아 반환
def get_project_title_by_id(project_obj_id):
    try:
        if not isinstance(project_obj_id, ObjectId):
            project_obj_id = ObjectId(project_obj_id)
        project = project_collection.find_one({"_id": project_obj_id})
        return project["title"] if project else None
    except Exception as e:
        return None

# 라우팅
@app.route('/timeline')
def timeline():
    user_id = session.get("user_id") # 세션에서 user_id 가져오기 (ObjectId로 변환 필요 시 get_user_name_by_id 사용)
    
    year_param = request.args.get('year')
    month_param = request.args.get('month')
    date_param = request.args.get('date')
    schedule_id_param = request.args.get('schedule_id')
    type_filter_param = request.args.get('type', '전체')
    
    user_names = []
    for user in user_collection.find({}, {"_id": 1, "name": 1, "position": 1, "department": 1}):
        user_data = {"_id": str(user["_id"])}
        if "name" in user and user["name"] is not None:
            user_data["name"] = user["name"]
        else:
            user_data["name"] = "이름 없음"

        user_data["position"] = user.get("position", "")
        user_data["department"] = user.get("department", "")

        user_names.append(user_data)
    
    grouped_users_by_department = {}
    for user_data in user_names:
        department = user_data.get("department", "기타")
        if department not in grouped_users_by_department:
            grouped_users_by_department[department] = []
        grouped_users_by_department[department].append({
            "id": user_data["_id"],
            "name": user_data["name"],
            "position": user_data["position"]
        })
    
    today = date.today()
    current_year = int(year_param) if year_param else today.year
    current_month = int(month_param) if month_param else today.month

    start_of_month = date(current_year, current_month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    calendar_days = []
    first_day_of_week = start_of_month.weekday()
    start_offset = (first_day_of_week + 1) % 7 # 월요일을 0으로 가정하면 (일요일=6) -> (일요일=0)
    start_date = start_of_month - timedelta(days=start_offset)

    for _ in range(35): # 5주 (35일) 표시
        is_current_month = (start_date.month == current_month)
        formatted_date = start_date.strftime('%Y-%m-%d')
        
        start_of_day_dt = datetime.combine(start_date, time.min)
        end_of_day_dt = datetime.combine(start_date, time.max)

        schedules_on_day = timeline_collection.count_documents({
            "start_date": {"$lte": end_of_day_dt}, 
            "end_date": {"$gte": start_of_day_dt}  
        }) > 0 

        calendar_days.append({
            'date': formatted_date,
            'day': start_date.day,
            'is_today': (start_date == today),
            'is_current_month': is_current_month,
            'has_schedule': schedules_on_day
        })
        start_date += timedelta(days=1)

    selected_date_obj = None
    if date_param:
        selected_date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
    else:
        selected_date_obj = today
    
    selected_date_str = selected_date_obj.strftime('%Y-%m-%d')

    daily_schedules_response = get_daily_schedules_api(date_param=selected_date_str, selected_type=type_filter_param).get_json()
    daily_schedules = daily_schedules_response['daily_schedules'] if daily_schedules_response['success'] else []

    selected_schedule_detail = {}
    if schedule_id_param:
        try:
            schedule = timeline_collection.find_one({"_id": ObjectId(schedule_id_param)})
            if schedule:
                selected_schedule_detail["scheduleId"] = str(schedule["_id"])
                selected_schedule_detail["scheduleName"] = schedule.get("title", "") 
                
                if isinstance(schedule.get("start_date"), datetime):
                    selected_schedule_detail["startDate"] = schedule["start_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["startTime"] = schedule["start_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["startDate"] = ""
                    selected_schedule_detail["startTime"] = "09:00"
                
                if isinstance(schedule.get("end_date"), datetime):
                    selected_schedule_detail["endDate"] = schedule["end_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["endTime"] = schedule["end_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["endDate"] = ""
                    selected_schedule_detail["endTime"] = "18:00"

                selected_schedule_detail["content"] = schedule.get("content", "")
                selected_schedule_detail["type"] = schedule.get("type", "")
                selected_schedule_detail["status"] = schedule.get("status", "").strip().replace(" ", "").replace("\u00a0", "")
                
                user_name = get_user_name_by_id(schedule.get("user_id")) 
                selected_schedule_detail["personName"] = user_name if user_name else "-"
                
                project_title = get_project_title_by_id(schedule.get("project_id")) 
                selected_schedule_detail["projectTitle"] = project_title if project_title else ""
                
                member_ids = schedule.get("member", []) 
                
                members_detailed_info = []
                if member_ids: 
                    member_object_ids = [ObjectId(mid) for mid in member_ids if isinstance(mid, str) and ObjectId.is_valid(mid)]
                    member_object_ids.extend([mid for mid in member_ids if isinstance(mid, ObjectId)])
                    
                    member_object_ids = list(set(member_object_ids))

                    for user in user_collection.find(
                        {"_id": {"$in": member_object_ids}},
                        {"name": 1, "position": 1, "department": 1} 
                    ):
                        members_detailed_info.append({
                            "id": str(user["_id"]),
                            "name": user.get("name", "이름 없음"),
                            "position": user.get("position", "직급 없음"),
                            "department": user.get("department", "부서 없음")
                        })
                selected_schedule_detail["members_detailed_info"] = members_detailed_info
                selected_schedule_detail["memberNames"] = [m["name"] for m in members_detailed_info]
                selected_schedule_detail["memberIds"] = [m["id"] for m in members_detailed_info]

        except Exception as e:
            selected_schedule_detail = {}

    project_titles = [p["title"] for p in project_collection.find({}, {"title": 1})]

    return render_template('timeline.html',
                           current_year=current_year, current_month=current_month, calendar_days=calendar_days,
                           daily_schedules=daily_schedules, selected_date=selected_date_str,
                           selected_schedule_detail=selected_schedule_detail,
                           status_options_by_type=STATUS_OPTIONS_BY_TYPE,
                           project_titles=project_titles, user_names=user_names,
                           grouped_users_by_department=grouped_users_by_department,
                           schedule_type_options=SCHEDULE_TYPE_OPTIONS,
                           selected_type_filter=type_filter_param
                          )

# 일별 일정 필터링
@app.route('/timeline/get_daily_schedules', methods=['GET'])
def get_daily_schedules_api(date_param=None, selected_type='전체'):
    if date_param is None:
        date_param = request.args.get('date')
        selected_type = request.args.get('type', '전체')

    if not date_param:
        return jsonify({"success": False, "message": "날짜 정보가 필요합니다."}), 400

    try:
        selected_date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"success": False, "message": "유효하지 않은 날짜 형식입니다."}), 400

    selected_start_of_day_dt = datetime.combine(selected_date_obj, time.min)
    selected_end_of_day_dt = datetime.combine(selected_date_obj, time.max)

    query = {
        "start_date": {"$lte": selected_end_of_day_dt},
        "end_date": {"$gte": selected_start_of_day_dt}
    }

    if selected_type != '전체':
        query["type"] = selected_type

    schedules_cursor = timeline_collection.find(query).sort("start_date", 1)

    daily_schedules = []
    for schedule in schedules_cursor:
        schedule_status = schedule.get("status", "").strip().replace(" ", "").replace("\u00a0", "")
        status_tag_class = STATUS_TAG_CLASS_MAP.get(schedule_status, "default-status-tag")

        daily_schedules.append({
            "schedule_id_param": str(schedule["_id"]),
            "name": schedule.get("title", "제목 없음"),
            "status_tag_class": status_tag_class,
            "status_display_text": schedule_status,
            "type": schedule.get("type", "")
        })
    return jsonify({"success": True, "daily_schedules": daily_schedules})

@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    data = request.get_json()
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "필수 필드(제목, 기간, 타입, 상태)가 누락되었습니다."}), 400

    user_id_from_session = session.get("user_id")
    if not user_id_from_session:
        return jsonify({"success": False, "message": "로그인된 사용자 정보가 없습니다. 다시 로그인 해주세요."}), 401
    
    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        start_date_dt = datetime.fromisoformat(start_date_iso)
        end_date_dt = datetime.fromisoformat(end_date_iso)
    except ValueError as e:
        return jsonify({"success": False, "message": "유효하지 않은 날짜/시간 형식입니다. (YYYY-MM-DDTHH:MM:SS)"}), 400

    new_schedule = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "user_id": ObjectId(user_id_from_session), # 세션의 user_id를 ObjectId로 변환하여 저장
        "created_at": datetime.now() 
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 리스트로 받음)
    member_ids_json = data.get("member_ids", "[]") # 'member_ids' 필드로 변경
    members_to_save = []
    print(f"DEBUG: raw member_ids_json from frontend: {member_ids_json}")
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
        except json.JSONDecodeError as e:
            pass
    
    new_schedule["member"] = members_to_save

    if new_schedule["type"] == "프로젝트":
        project_title = data.get("project_title")
        if not project_title:
            return jsonify({"success": False, "message": "프로젝트 일정을 선택했을 경우 프로젝트 제목을 선택해주세요."}), 400
        
        project_id = get_project_id_by_title(project_title)
        if project_id:
            new_schedule["project_id"] = project_id 
        else:
            return jsonify({"success": False, "message": f"프로젝트 '{project_title}'을(를) 찾을 수 없습니다."}), 400
    else:
        new_schedule["project_id"] = None 

    try:
        result = timeline_collection.insert_one(new_schedule) 
        return jsonify({"success": True, "message": "일정이 성공적으로 생성되었습니다."})
    except Exception as e:
        return jsonify({"success": False, "message": f"일정 생성 중 오류 발생: {str(e)}"}), 500

@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    data = request.get_json()

    original_schedule_id_param = data.get("original_schedule_id_param")

    if not original_schedule_id_param:
        return jsonify({"success": False, "message": "수정할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_update = ObjectId(original_schedule_id_param)
    except Exception as e:
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    user_id_from_session = session.get("user_id")
    if not user_id_from_session:
        return jsonify({"success": False, "message": "로그인된 사용자 정보가 없습니다. 다시 로그인 해주세요."}), 401
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "필수 필드(제목, 기간, 타입, 상태)가 누락되었습니다."}), 400

    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        # Z 문자가 있을 경우 UTC로 처리하기 위해 +00:00으로 대체
        start_date_dt = datetime.fromisoformat(start_date_iso.replace('Z', '+00:00'))
        end_date_dt = datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
    except ValueError as e:
        return jsonify({"success": False, "message": f"유효하지 않은 날짜/시간 형식입니다: {e}"}), 400

    updated_schedule_data = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "updated_at": datetime.now()
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 리스트로 받음)
    member_ids_json = data.get("member_ids", "[]") # 'member_ids' 필드로 변경
    members_to_save = []
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
        except json.JSONDecodeError as e:
            pass
    
    updated_schedule_data["member"] = members_to_save

    if updated_schedule_data["type"] == "프로젝트":
        project_title = data.get("project_title")
        if not project_title:
            return jsonify({"success": False, "message": "프로젝트 일정을 선택했을 경우 프로젝트 제목을 선택해주세요."}), 400
        
        project_id = get_project_id_by_title(project_title)
        if project_id:
            updated_schedule_data["project_id"] = project_id 
        else:
            return jsonify({"success": False, "message": f"프로젝트 '{project_title}'을(를) 찾을 수 없습니다."}), 400
    else:
        updated_schedule_data["project_id"] = None 

    try:
        result = timeline_collection.update_one(
            {"_id": schedule_obj_id_to_update},
            {"$set": updated_schedule_data}
        )
        if result.modified_count == 1:
            return jsonify({"success": True, "message": "일정이 성공적으로 수정되었습니다."})
        else:
            found_document = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
            if found_document:
                return jsonify({"success": True, "message": "일정 내용이 변경되지 않았습니다."})
            else:
                return jsonify({"success": False, "message": "일정을 찾을 수 없습니다."}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"일정 수정 중 오류 발생: {str(e)}"}), 500

@app.route('/timeline/delete_schedule', methods=['POST'])
def delete_schedule():
    data = request.get_json()
    schedule_id_param = data.get("schedule_id_param")

    if not schedule_id_param:
        return jsonify({"success": False, "message": "삭제할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_delete = ObjectId(schedule_id_param)
    except Exception as e:
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    try:
        result = timeline_collection.delete_one({"_id": schedule_obj_id_to_delete}) 
        if result.deleted_count == 1:
            return jsonify({"success": True, "message": "일정이 성공적으로 삭제되었습니다."})
        else:
            return jsonify({"success": False, "message": "일정을 찾을 수 없었습니다."}), 404
    except Exception as e: 
        return jsonify({"success": False, "message": f"일정 삭제 중 오류 발생: {str(e)}"}), 500


# ========== bonghyeon - login ==========
def login_required_bh(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip()
        pw = request.form.get("password")
        user = user_collection.find_one({"email": email})
        if user and str(user["userPassword"]) == pw:
            session["user_id"] = str(user["_id"])
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="이메일 또는 비밀번호가 틀렸습니다.")
    return render_template("login.html")

@app.route("/logout")
def logout_bh():
    session.clear()
    return redirect(url_for("home"))

@app.route("/signup", methods=["GET", "POST"])
def signup_bh():
    if request.method == "POST":
        email_id = request.form.get("email_id")
        email_domain = request.form.get("email_domain") or request.form.get("email_domain_input")
        email = f"{email_id}@{email_domain}".strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        phone = re.sub(r'\D', '', request.form["phone"])
        if password != confirm_password:
            return render_template("signup.html", error="비밀번호가 일치하지 않습니다.")
        if not re.match(r"^[^@]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return render_template("signup.html", error="올바른 이메일 형식이 아닙니다.")
        if user_collection.find_one({"email": email}):
            return render_template("signup.html", error="이미 존재하는 이메일입니다.")
        new_user = OrderedDict([
            ("email", email),
            ("name", request.form["name"]),
            ("userPassword", password),
            ("profile", request.form.get("profile", "")),
            ("department", request.form["department"]),
            ("position", request.form["position"]),
            ("createAt", str(date.today())),
            ("phone_num", phone),
        ])
        user_collection.insert_one(new_user)
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/profile_edit", methods=["GET", "POST"])
@login_required_bh
def profile_edit_bh():
    user_id = ObjectId(session["user_id"])
    print("data check", user_id)
    if request.method == "POST":
        email_id = request.form.get("email_id")
        email_domain = request.form.get("email_domain") or request.form.get("email_domain_input")
        email = f"{email_id}@{email_domain}".strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        phone = re.sub(r'\D', '', request.form.get("phone", ""))
        if password != confirm_password:
            user = user_collection.find_one({"_id": user_id})
            return render_template("profile_edit.html", user=user, error="비밀번호가 일치하지 않습니다.")
        update_data = {
            "name": request.form.get("name"),
            "userPassword": password,
            "phone_num": phone,
            "department": request.form.get("department"),
            "position": request.form.get("position"),
            "profile": request.form.get("profile"),
            "email": email
        }
        user_collection.update_one({"_id": user_id}, {"$set": update_data})
        return redirect(url_for("mypage"))
    user = user_collection.find_one({"_id": user_id})
    return render_template("profile_edit.html", user=user)

@app.route("/delete_account", methods=["GET", "POST"])
@login_required_bh
def delete_account_bh():
    user_id = ObjectId(session["user_id"])
    if request.method == "POST":
        user_collection.delete_one({"_id": user_id})
        session.clear()
        return "<script>alert('탈퇴가 완료되었습니다.'); window.location.href='/'</script>"
    return render_template("delete_account.html")

# ========== inho - faq ==========
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

# ========== yerim - board ==========
@app.route("/board")
def board():
    posts = list(board_collection.find({"category": "자유"}))
    
    for p in posts:
        if p["title"] == "" or p["title"] == None:
            p["title"] = "-"
        try:
            p["writer"] = user_collection.find_one({"_id": p["user_id"]})["name"]
        except Exception as e:
            p["writer"] = "-"
            print(e)
        
        if "update_date" in p and p["update_date"]:
            p["update_date"] = p["update_date"].strftime("%Y-%m-%d %H:%M")
        else:
            p["update_date"] = "-"
    
    posts.sort(key=lambda x: x.get("no", 0), reverse=True)
    return render_template("freeboard_main.html", posts=posts)

@app.route("/board/detail/<id>")
def freeboard_detail(id):
    post = board_collection.find_one({"_id": ObjectId(id)}) 
    try:
        post["writer"] = user_collection.find_one({"_id": post["user_id"]})["name"]
    except Exception as e:
        post["writer"] = "-"
        print(e)

    if "update_date" in post and post["update_date"]:
        post["update_date"] = post["update_date"].strftime("%Y-%m-%d %H:%M")
    else:
        post["update_date"] = "-"
    return render_template("freeboard_detail.html", post=post)

@app.route('/board_insert', methods=['GET', 'POST'])
def insert_form():
    user_id = session.get("user_id")
    if request.method == 'GET':
        if user_id == None:
            return "<script>alert('로그인 후 이용 가능합니다'); window.location.href = './login';</script>"
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