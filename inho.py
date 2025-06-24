from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime
from pytz import timezone


# env 파일 로드
load_dotenv()
user = os.getenv("USER")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)

client = MongoClient(uri)
db = client['team3']
app.secret_key = "your-secret-key"  # 아무 문자열이면 됨 (보안용 키)

project_collection = db["projects"]
user_collection = db["users"]
schedule_collection = db["schedules"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]

@app.route("/")
def home():
    notifications = ["새 프로젝트가 등록되었습니다", "마감일이 다가옵니다"]
    has_notification = len(notifications) > 0
    return render_template("index.html", notifications=notifications, has_notification=has_notification)

@app.route("/example")
def example():
    return render_template("/example.html")

@app.route('/login')
def login():
    return "로그인 페이지(나중에 구현)"


@app.route('/set_user/<user_id>') # 테스트용 세선 함수
def set_user(user_id):
    session["user_id"] = user_id
    return f"세션에 사용자 {user_id} 저장 완료"

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

    return render_template("notifications.html", notifications=notifications,current_page="notifications")


@app.route("/notifications/read/<notification_id>", methods=["POST"])
def mark_single_notification_read(notification_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True}}
    )
    return redirect(url_for("show_notifications"))




@app.route("/notifications/read", methods=["POST"]) # 알림 누르면 read:True로 변경되면서 red-dot 사라짐ㅋ
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
        return redirect(url_for("login"))  # 미리 만들어논 예외처리
    
    if request.method == "POST":
        user_ids = request.form.getlist("_id")           
        status_list = request.form.getlist("status")    
        object_ids = [ObjectId(uid) for uid in user_ids]

        team_doc = team_collection.find_one({"project_id": ObjectId(project_id)})
        project_doc = project_collection.find_one({"_id": ObjectId(project_id)})
        project_manager_id = ObjectId(session["user_id"])  # 세션에서 현재 로그인한 사용자 (팀장)

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
                {"$set": {
                    "member": members,
                    "status": statuses
                }}
            )
            print("[업데이트] 기존 팀 문서에 중복 제거 후 새 멤버 추가 완료.")
        else:
            team_collection.insert_one({
                "project_id": ObjectId(project_id),
                "member": object_ids,
                "status": status_list
            })
            print("[등록] 새 팀 문서 생성 완료.")

        # ✅ 알림 생성
        manager = user_collection.find_one({"_id": project_manager_id})
        for uid in object_ids:
            user = user_collection.find_one({"_id": uid})
            message = f"{manager['name']}님이 프로젝트 '{project_doc['title']}'에 팀원으로 {user['name']}님을 추가했습니다."

            notification = {
                "user_id": uid,
                "sender_id": project_manager_id,
                "message": message,
                "project_id": ObjectId(project_id),
                "read": False,
                "created_at": datetime.utcnow()
            }
            db.notifications.insert_one(notification)

        return redirect(url_for("teamMemberManage", project_id=project_id))

    users = list(user_collection.find({"position": {"$ne": "팀장"}}))
    for u in users:
        u["_id"] = str(u["_id"])

    return render_template("teamMemberAdd.html", users=users, project_id=project_id)


# GET 요청:

# 프로젝트에 등록 가능한 모든 사용자 리스트를 MongoDB에서 불러와 teamMembersAdd.html 템플릿에 전달합니다.

# ObjectId 타입을 문자열로 변환하여 템플릿에서 쉽게 처리할 수 있도록 합니다.

# POST 요청:

# 폼에서 넘어온 팀원 ID 리스트와 상태 리스트를 받고, MongoDB ObjectId 타입으로 변환합니다.

# 해당 프로젝트의 팀 문서가 이미 있으면 기존 팀원과 상태 배열에서 중복되는 사용자는 삭제하고, 새로 넘어온 멤버와 상태를 추가합니다.

# 팀 문서가 없으면 새로 생성합니다.

# 처리 후 팀원 관리 페이지(/teamMemberManage)로 리다이렉트합니다.

# @app.route('/teamMemberAdd/<project_id>', methods=["GET", "POST"])
# def teamMemberAdd(project_id):
#     if request.method == "POST":
#         user_ids = request.form.getlist("_id")
#         status_list = request.form.getlist("status")
#         # print(user_ids, status_list)
#         id_list = []

#         for user_id in user_ids:
#             user_info = user_collection.find_one({"_id": ObjectId(user_id)})

#             if not user_info:
#                 print(f"[오류] {user_info.name} 사용자를 찾을 수 없습니다.")
#                 user_ids.remove(user_id)
#                 continue

#             already_exists = team_collection.find_one({"_id": ObjectId(user_id), "project_id": ObjectId(project_id)})
#             if already_exists:
#                 print(f"[중복] {user_info.name}은 이미 팀에 등록되어 있습니다.")
#                 user_ids.remove(user_id)
#                 continue
#             id_list.append(ObjectId(user_id))

#         team_collection.insert_one({
#             "project_id": ObjectId(project_id),
#             "member": id_list,
#             "status": status_list
#         })
        
#         print(f"[등록 완료] {len(user_ids)}명 팀원 추가 완료")

#         return redirect(url_for("teamMemberManage", project_id=project_id))

#     print(project_id)
#     users = list(user_collection.find({}))
#     for u in users:
#         u["_id"] = str(u["_id"])
#     return render_template("teamMembersAdd.html", users=users, project_id=project_id)



@app.route('/teamMemberManage/<project_id>')
def teamMemberManage(project_id):
    # [1] 로그인 안 되어있으면 로그인 페이지로 리다이렉트 (준비용)
    if "user_id" not in session:
        return redirect(url_for("login"))  # login 라우트는 나중에 만들면 됩니다.

    # [2] 현재 로그인한 사용자 ID 가져오기
    current_user_id = ObjectId(session["user_id"])

    # [3] 프로젝트 찾기
    project_obj_id = ObjectId(project_id)
    project_doc = project_collection.find_one({"_id": project_obj_id})
    if not project_doc:
        return "해당 프로젝트를 찾을 수 없습니다.", 404

    # [4] 팀장 정보
    project_manager_id = project_doc.get("project_manager")
    manager_user = user_collection.find_one({"_id": project_manager_id})
    if not manager_user:
        return "팀장 유저 정보를 찾을 수 없습니다.", 404

    # [5] 팀 문서
    team_doc = team_collection.find_one({"project_id": project_obj_id})
    member_ids = team_doc.get("member", []) if team_doc else []
    status_list = team_doc.get("status", []) if team_doc else []

    # [6] 팀장 포함시키기
    if project_manager_id not in member_ids:
        member_ids.insert(0, project_manager_id)
        status_list.insert(0, "팀장")

    # [7] 사용자 정보 조회
    user_info_map = {
        str(user["_id"]): user
        for user in user_collection.find(
            {"_id": {"$in": member_ids}}, {"name": 1, "email": 1, "role": 1}
        )
    }

    # [8] 팀원 정보 리스트 만들기
    members = []
    for i, member_id in enumerate(member_ids):
        user = user_info_map.get(str(member_id))
        if user:
            members.append({
                "_id": str(member_id),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "status": status_list[i],
                "is_manager": member_id == project_manager_id
            })

    # [9] 현재 유저의 읽지 않은 알림 가져오기
    notification_docs = db.notifications.find({
        "user_id": current_user_id,
        "read": False
    })
    notifications = [doc["message"] for doc in notification_docs]
    has_notification = len(notifications) > 0

    # [10] 렌더링
    return render_template(
        'teamMemberManage.html',
        project_id=project_id,
        team_members=members,
        notifications=notifications,
        has_notification=has_notification
    )


# 프로젝트 ID에 해당하는 팀 문서에서 팀원 목록(member)과 상태(status)를 불러옵니다.

# 각 팀원 ID에 해당하는 사용자 정보를 user_collection에서 조회해서 매핑합니다.

# 사용자 정보와 상태를 조합해 팀원 목록을 구성해 teamMembersManage.html 템플릿에 전달합니다.

@app.route('/teamMemberUpdate/<project_id>/<member_id>', methods=["POST"])
def teamMemberUpdate(project_id, member_id):
    new_status = request.form.get("status")
    
    team_doc = team_collection.find_one({"project_id": ObjectId(project_id)})
    
    if not team_doc:
        print("팀 정보를 찾을 수 없습니다.")
        return redirect(url_for("teamMemberManage", project_id=project_id))
    
    try:
        index = team_doc["member"].index(ObjectId(member_id))
    except ValueError:
        print("해당 멤버가 팀에 없습니다.")
        return redirect(url_for("teamMemberManage", project_id=project_id))
    
    team_doc["status"][index] = new_status
    
    team_collection.update_one(
        {"project_id": ObjectId(project_id)},
        {"$set": {"status": team_doc["status"]}}
    )
    
    print(f"팀원 상태가 '{new_status}'로 업데이트 되었습니다.")
    print("넘어온 member_id:", member_id)
    print("변환된 ObjectId:", ObjectId(member_id))
    print("team_doc['member'] 리스트:")
    for i, m in enumerate(team_doc["member"]):
        print(f"  {i}: {m} (type: {type(m)})")
    
    return redirect(url_for("teamMemberManage", project_id=project_id))

# 폼에서 전달된 status 값을 받아 해당 프로젝트 팀 문서에서 해당 멤버의 상태를 수정하고 DB에 업데이트합니다.

# 처리 후 팀원 관리 페이지로 리다이렉트합니다.


@app.route('/teamMemberDelete/<project_id>/<member_id>', methods=["POST"])
def teamMemberDelete(project_id, member_id):
    team_doc = team_collection.find_one({"project_id": ObjectId(project_id)})

    if not team_doc:
        print("팀 정보를 찾을 수 없습니다.")
        return redirect(url_for("teamMemberManage", project_id=project_id))

    try:
        index = team_doc["member"].index(ObjectId(member_id))
    except ValueError:
        print("해당 멤버가 팀에 없습니다.")
        return redirect(url_for("teamMemberManage", project_id=project_id))

    del team_doc["member"][index]
    del team_doc["status"][index]

    team_collection.update_one(
        {"project_id": ObjectId(project_id)},
        {"$set": {
            "member": team_doc["member"],
            "status": team_doc["status"]
        }}
    )

    print("팀원 삭제 완료.")
    return redirect(url_for("teamMemberManage", project_id=project_id))

# 해당 프로젝트 팀 문서에서 멤버 ID를 찾아 삭제하고, 상태 배열도 함께 삭제한 후 DB에 반영합니다.

# 삭제 후 팀원 관리 페이지로 리다이렉트합니다.


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)