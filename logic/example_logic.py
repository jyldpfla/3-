from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
current_dir = os.path.dirname(os.path.abspath(__file__))  # logic 폴더 경로
parent_dir = os.path.dirname(current_dir)  # 3팀_프로젝트 폴더 경로

from datas import example

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

client = MongoClient(uri)
db = client['team3']

project_collection = db["projects"]
user_collection = db["users"]
schedule_collection = db["schedules"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]
bell_collection = db["bell"]
timeline_collection = db["timeline"]


def example_add(collection, data):
    collection.insert_one(data)
    
if __name__ == "__main__":
    example_add(project_collection, example.project_data)
    # example_add(user_collection, example.user_data)
    # example_add(schedule_collection, example.schedule_data)
    # example_add(personal_todo_collection, example.personal_todo_data)
    # example_add(board_collection, example.board_data)
    # example_add(team_collection, example.team_data)
    example_add(timeline_collection, example.timeline_data)
    example_add(timeline_collection, example.timeline_data2)
    # example_add(team_collection, example.team_data)
    example_add(bell_collection, example.bell_data)