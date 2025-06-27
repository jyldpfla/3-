from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
from functools import wraps
from collections import OrderedDict
from datetime import date
import os
import re

# ✅ 환경변수 로드 및 MongoDB 연결
load_dotenv()
user_env = os.getenv("MONGO_USER").strip('"')
if not user_env or ":" not in user_env:
    raise ValueError("❌ MONGO_USER 환경변수가 없거나 '아이디:비밀번호' 형식이 아님")

username, password = user_env.split(":")
uri = f"mongodb+srv://{username}:{password}@team3.fxbwcnh.mongodb.net/team3?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["team3"]
user_collection = db["users"]

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ✅ 로그인 확인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ✅ 메인 페이지
@app.route("/")
@login_required
def index():
    user = user_collection.find_one({"_id": ObjectId(session["user_id"])})
    return render_template("index.html", user=user)

# ✅ 로그인
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip()
        pw = request.form.get("password")

        user = user_collection.find_one({"email": email})
        if user and str(user["userPassword"]) == pw:
            session["user_id"] = str(user["_id"])
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="이메일 또는 비밀번호가 틀렸습니다.")
    return render_template("login.html")


# ✅ 로그아웃
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ✅ 마이페이지
@app.route("/mypage")
@login_required
def mypage():
    user = user_collection.find_one({"_id": ObjectId(session["user_id"])})
    return render_template("mypage.html", user=user)

# ✅ 회원가입
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email_id = request.form.get("email_id")
        email_domain = request.form.get("email_domain") or request.form.get("email_domain_input")
        email = f"{email_id}@{email_domain}".strip()

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        phone = re.sub(r'\D', '', request.form["phone"])  # 숫자만 저장

        if password != confirm_password:
            return render_template("signup.html", error="비밀번호가 일치하지 않습니다.")

        if not re.match(r"^[^@]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return render_template("signup.html", error="올바른 이메일 형식이 아닙니다.")

        if user_collection.find_one({"email": email}):
            return render_template("signup.html", error="이미 존재하는 이메일입니다.")

        new_user = OrderedDict([
            ("email", email),
            ("name", request.form["name"]),
            ("userPassword", password),
            ("role", request.form.get("role", "직원")),
            ("profile", request.form.get("profile", "")),
            ("department", request.form["department"]),
            ("position", request.form["position"]),
            ("createAt", str(date.today())),
            ("phone_num", phone),
        ])

        user_collection.insert_one(new_user)
        return redirect(url_for("login"))

    return render_template("signup.html")

# ✅ 개인정보 수정
@app.route("/profile_edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    user_id = ObjectId(session["user_id"])

    if request.method == "POST":
        email_id = request.form.get("email_id")
        email_domain = request.form.get("email_domain") or request.form.get("email_domain_input")
        email = f"{email_id}@{email_domain}".strip()

        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        phone = re.sub(r'\D', '', request.form.get("phone", ""))

        if password != confirm_password:
            user = user_collection.find_one({"_id": user_id})
            return render_template("profile_edit.html", user=user, error="비밀번호가 일치하지 않습니다.")

        update_data = {
            "name": request.form.get("name"),
            "userPassword": password,
            "phone_num": phone,
            "department": request.form.get("department"),
            "position": request.form.get("position"),
            "role": request.form.get("role"),
            "profile": request.form.get("profile"),
            "email": email
        }

        user_collection.update_one({"_id": user_id}, {"$set": update_data})
        return redirect(url_for("mypage"))

    user = user_collection.find_one({"_id": user_id})
    return render_template("profile_edit.html", user=user)

# ✅ 회원탈퇴
@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    user_id = ObjectId(session["user_id"])
    if request.method == "POST":
        user_collection.delete_one({"_id": user_id})
        session.clear()
        return "<script>alert('탈퇴가 완료되었습니다.'); window.location.href='/'</script>"
    return render_template("delete_account.html")

# ✅ 실행
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
