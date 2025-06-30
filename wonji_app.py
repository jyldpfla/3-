from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from functools import wraps  # 로그인 제한용

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 세션 사용을 위한 키 (필수)

client = MongoClient(uri)
db = client['team3']

project_collection = db["projects"]
user_collection = db["users"]
timeline_collection = db["timeline"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]

# ✅ 로그인 제한용 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

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
        return date
    return date.strftime("%Y-%m-%d")

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

# ✅ 로그인 페이지 추가 (테스트용)
@app.route("/login")
def login():
    return "<h2>로그인 필요! (나중에 진짜 로그인 페이지로 연결)</h2>"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
