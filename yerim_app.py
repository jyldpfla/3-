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
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]

@app.route("/")
def home():
    return render_template("/index.html")

@app.route("/example")
def example():
    return render_template("/example.html")

@app.route("/mypage")
def mypage():
    user = user_collection.find_one({"name": "장예림"})
    project_pipeline = [
        {
            "$match": {
                "members": "장예림"
            }
        },
        {
            "$project": {
                "_id": 0,
                "project_id": 1
            }
        }
    ]
    projects = list(team_collection.aggregate(project_pipeline))
    print(projects)
    return render_template("/my_page.html", user_info=user)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)