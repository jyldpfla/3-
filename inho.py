from flask import *
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)

client = MongoClient(uri)
db = client['team3']

project_collection = db["projects"]
user_collection = db["users"]
schedule_collection = db["schedules"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]

@app.route("/")
def home():
    return render_template("/index.html")

@app.route("/example")
def example():
    return render_template("/example.html")



@app.route('/teamMemberAdd', methods=["GET", "POST"])
def teamMemberAdd():
    if request.method == "POST":
        name = request.form.get("name")
        status = request.form.get("status")
        user_info = user_collection.find_one({"name": name})
        if user_info:
            team_collection.insert_one({
                "name": name,
                "email": user_info.get("email"),
                "role": user_info.get("role"),
                "department": user_info.get("department"),
                "status": status
            })
            return redirect(url_for("teamMemberManage"))
        else:
            return "해당 이름의 유저를 찾을 수 없습니다.", 404
    users = list(user_collection.find({}, {"_id": 0})) 
    return render_template("teamMembersAdd.html", users=users)


@app.route('/teamMemberManage')
def teamMemberManage():
    team_members = list(team_collection.find({}, {'_id': 0}))  
    return render_template('teamMembersManage.html', team_members=team_members)

@app.route('/teamMemberUpdate', methods=["POST"])
def teamMemberUpdate():
    name = request.form.get("name")
    status = request.form.get("status")
    result = team_collection.update_one(
        {"name": name},
        {"$set": {"status": status}}
    )
    if result.modified_count > 0:
        print(f"{name}의 상태가 {status}로 업데이트 되었습니다.")
    else:
        print(f"{name} 상태 변경 없음 또는 실패.")
    return redirect(url_for("teamMemberManage"))

@app.route('/teamMemberDelete/<name>', methods=["POST"])
def teamMemberDelete(name):
    result = team_collection.delete_one({"name": name})
    if result.deleted_count > 0:
        print(f"{name} 팀원이 삭제되었습니다.")
    else:
        print(f"{name} 팀원 삭제 실패.")
    return redirect(url_for("teamMemberManage", name=name))



@app.route('/project-detail') # 원지님 코드
def project_detail():
    return render_template("/projectDetail.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)