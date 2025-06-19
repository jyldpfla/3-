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



@app.route('/team-member-add', methods=["GET", "POST"])
def team_member_add():
    # if request.method == "POST":
        # name = request.form.get("name")
        # status = request.form.get("status")

        # users 컬렉션에서 이름에 해당하는 사용자 정보 찾기
        # user_info = user_collection.find_one({"name": name})
        # if user_info:
        #     team_collection.insert_one({
        #         "name": name,
        #         "email": user_info.get("email"),
        #         "role": user_info.get("role"),
        #         "department": user_info.get("department"),
        #         "status": status
        #     })
        #     return redirect(url_for("home")) 
        # else:
        #     return "해당 이름의 유저를 찾을 수 없습니다.", 404
    return render_template('/teamMembersAdd.html')

@app.route('/team-member-manage')
def team_member_manage():
    
    return render_template('/teamMembersManage.html')


@app.route('/project-detail')
def project_detail():
    return render_template("/projectDetail.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)