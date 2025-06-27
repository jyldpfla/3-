from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)

client = MongoClient(uri)
db = client['team3']

project_collection = db["projects"]
user_collection = db["users"]
timeline_collection = db["timeline"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]

@app.route("/")
def home():
    return render_template("/index.html")

@app.route("/example")
def example():
    return render_template("/example.html")

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

    project_list = list(project_collection.find())
    done = [t for t in project_list if t['status'] == '완료']
    doing = [t for t in project_list if t['status'] == '진행중']
    wait = [t for t in project_list if t['status'] == '진행 대기']

    for project in project_list:
        manager = user_collection.find_one({"_id": project["project_manager"]})
        project["project_manager"] = manager["name"] if manager else "알 수 없음"
        project["start_date"] = to_str(project.get("start_date"))
        project["end_date"] = to_str(project.get("end_date"))

    # ✅ 상태 기준 정렬
    status_order = {"진행 대기": 0, "진행중": 1, "완료": 2}
    project_list.sort(key=lambda x: status_order.get(x["status"], 99))

    return render_template("/projectList.html", project_list=project_list, done=done, doing=doing, wait=wait)



from datetime import datetime

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
        }
        result = project_collection.insert_one(project)

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
            }}
        )

        return redirect(url_for('projectDetail', project_id=project_id))

    # ✅ 여기가 GET 요청 처리 — 여기부터 붙여넣기
    project = project_collection.find_one({"_id": ObjectId(project_id)})

    # 🔒 담당자 안전하게 가져오기
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

    # ✅ 이미 상단에서 import 했으니 여기선 다시 하지 말고 바로 사용
    DEFAULT_MANAGER_ID = ObjectId("6853aebf690a71fa9ad4b6e3")

    manager_id = project.get("project_manager", DEFAULT_MANAGER_ID)

    try:
        manager_id = ObjectId(manager_id)
    except:
        manager_id = DEFAULT_MANAGER_ID

    manager_doc = user_collection.find_one({"_id": manager_id})
    manager = manager_doc["name"] if manager_doc else "알 수 없음"
    project["manager_name"] = manager

    # ✅ 날짜 포맷 처리
    def to_str(date):
        if not date:
            return ""
        return date[:10] if isinstance(date, str) else date.strftime("%Y-%m-%d")

    project["start_date"] = to_str(project.get("start_date"))
    project["end_date"] = to_str(project.get("end_date"))

    # 🔧 팀원 처리
    team_map = {t["project_id"]: t["member"] for t in team_collection.find({})}
    project["team"] = [
        user["name"] for user in user_collection.find(
            {"_id": {"$in": team_map.get(ObjectId(project_id), [])}},
            {"_id": 0, "name": 1}
        )
    ]

    return render_template("/projectDetail.html", project=project)



@app.route("/projectDelete/<project_id>", methods=["POST"])
def projectDelete(project_id):
    project_collection.delete_one({"_id": ObjectId(project_id)})
    return redirect(url_for('projectList'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    