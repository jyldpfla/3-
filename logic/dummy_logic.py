from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
current_dir = os.path.dirname(os.path.abspath(__file__))  # logic 폴더 경로
parent_dir = os.path.dirname(current_dir)  # 3팀_프로젝트 폴더 경로

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

client = MongoClient(uri)
db = client['team3']

project_collection = db["projects"]
user_collection = db["users"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]
bell_collection = db["bell"]
timeline_collection = db["timeline"]


def example_add(collection, data):
    collection.insert_one(data)
    
def add_dummy(collection, data):
    collection.insert_many(data)
    
def get_csv(file_name):
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'datas', file_name)
    import pandas as pd
    import numpy as np

    df = pd.read_csv(csv_path)
    df = df.replace({np.nan: None})
    list = df.to_dict(orient="records")
    
    return list
    
def turn_datetime(list, dt_list):
    from datetime import datetime
    
    for l in list:
        for dt in dt_list:
            l[dt] = datetime.fromisoformat(l[dt].replace("Z", ""))
    
    return list
    
def turn_ObjectId(list, ob_list):
    from bson import ObjectId
    
    for l in list:
        for ob in ob_list:
            l[ob] = ObjectId(l[ob])
    
    return list

def turn_list(list, inner_list):
    import ast
    
    for l in list:
        if isinstance(l[inner_list], str):
            l[inner_list] = ast.literal_eval(l[inner_list])
    
    return list
    
if __name__ == "__main__":
    # user_list = get_csv("dummy_users.csv")
    # user_list = turn_datetime(user_list, ["createAt"])
    # add_dummy(user_collection, user_list)
    # project_list = get_csv("dummy_projects.csv")
    # project_list = turn_datetime(project_list, ["start_date", "end_date"])
    # project_list = turn_ObjectId(project_list, ["project_manager"])
    # add_dummy(project_collection, project_list)
    # project_list = get_csv("dummy_projects.csv")
    # project_list = turn_datetime(project_list, ["start_date", "end_date"])
    # project_list = turn_ObjectId(project_list, ["project_manager"])
    # add_dummy(project_collection, project_list)
    # team_list = get_csv("dummy_team.csv")
    # team_list = turn_list(team_list, "member")
    # team_list = turn_list(team_list, "status")
    # from bson import ObjectId
    
    # for t in team_list:
    #     t["member"] = [ObjectId(id) for id in t["member"]]
    # add_dummy(team_collection, team_list)
    # timeline_list = get_csv("dummy_timeline.csv")
    # timeline_list = turn_datetime(timeline_list, ["start_date", "end_date", "created_at", "updated_at"])
    # timeline_list = turn_list(timeline_list, "member")
    # from bson import ObjectId
    
    # for t in timeline_list:
    #     t["member"] = [ObjectId(id) for id in t["member"]]
    # add_dummy(timeline_collection, timeline_list)
    # p_todo_list = get_csv("dummy_p_todo.csv")
    # p_todo_list = turn_datetime(p_todo_list, ["end_date"])
    # p_todo_list = turn_ObjectId(p_todo_list, ["user_id"])
    # add_dummy(personal_todo_collection, p_todo_list)
    # board_list = get_csv("dummy_board.csv")
    # board_list = turn_datetime(board_list, ['create_date', 'update_date'])
    # board_list = turn_ObjectId(board_list, ["user_id"])
    # add_dummy(board_collection, board_list)
    
    # role 컬럼 삭제
    # user_collection.update_many({}, {"$unset": {"role": ""}})
    
    # nan 값 null로 변경
    # import math
    
    # for doc in user_collection.find():
    #     profile = doc.get("profile")

    # # profile 값이 float NaN인 경우만 업데이트
    #     if isinstance(profile, float) and math.isnan(profile):
    #         user_collection.update_one(
    #             {"_id": doc["_id"]},
    #             {"$set": {"profile": None}}
    #         )