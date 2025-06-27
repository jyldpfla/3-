from collections import defaultdict
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
app.secret_key = os.environ["SECRET_KEY"]

client = MongoClient(uri)
db = client['team3']

board_collection = db["board"]

# -------------------------------
# FAQ 등록 (폼에서 POST로)
# -------------------------------
@app.route("/faq/insert_action", methods=["POST"])
def faq_insert():
    title = request.form.get("title")
    category = request.form.get("category")
    content = request.form.get("content")
    user_id = request.form.get("user_id")  # form에서 user_id를 받아온다고 가정
    now = datetime.now(timezone('Asia/Seoul'))
    if title and category and content and user_id:
        board_collection.insert_one({
            "title": title,
            "category": category,
            "user_id": ObjectId(user_id),
            "content": content,
            "create_date": now,
            "update_date": now
        })
    return redirect(url_for("faq_main"))

# -------------------------------
# FAQ 수정
# -------------------------------
@app.route("/faq/update_action/<faq_id>", methods=["POST"])
def faq_update(faq_id):
    title = request.form.get("title")
    category = request.form.get("category")
    content = request.form.get("content")
    now = datetime.now(timezone('Asia/Seoul'))
    if title and category and content:
        board_collection.update_one(
            {"_id": ObjectId(faq_id)},
            {"$set": {
                "title": title,
                "category": category,
                "content": content,
                "update_date": now
            }}
        )
    return redirect(url_for("faq_main"))

# -------------------------------
# FAQ 삭제
# -------------------------------
@app.route("/faq/delete/<faq_id>", methods=["POST"])
def faq_delete(faq_id):
    board_collection.delete_one({"_id": ObjectId(faq_id)})
    return redirect(url_for("faq_main"))

# -------------------------------
# FAQ 메인 (리스트)
# -------------------------------
@app.route("/faq")
def faq_main():
    faqs = list(board_collection.find().sort("create_date", -1))
    return render_template("faq_main.html", faqs=faqs)

# -------------------------------
# 메인 실행
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)