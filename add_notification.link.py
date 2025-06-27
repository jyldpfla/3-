from pymongo import MongoClient
from dotenv import load_dotenv
import os

# env 파일 로드
load_dotenv()
user = os.getenv("USER")
uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/"

client = MongoClient(uri)
db = client['team3']

# 기존 알림 중 notification_link가 없는 것만 업데이트
for note in db.notifications.find({"notification_link": {"$exists": False}}):
    project_id = note.get("project_id")
    if project_id:
        link = f"/projectDetail/{str(project_id)}"
        db.notifications.update_one(
            {"_id": note["_id"]},
            {"$set": {"notification_link": link}}
        )