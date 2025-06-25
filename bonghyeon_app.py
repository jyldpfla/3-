from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from dotenv import load_dotenv
from functools import wraps
import os

# ✅ .env 파일 로드 및 MongoDB 연결
load_dotenv()
user_env = os.getenv("MONGO_USER").strip('"')

if not user_env or ":" not in user_env:
    raise ValueError("❌ MONGO_USER 환경변수가 없거나 '아이디:비밀번호' 형식이 아님")

username, password = user_env.split(":")
uri = f"mongodb+srv://{username}:{password}@team3.fxbwcnh.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["team3"]
user_collection = db["users"]

# ✅ Flask 앱 설정
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ✅ 로그인 확인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ✅ 메인 페이지
@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session["username"])

# ✅ 로그인
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form["username"]
        pw = request.form["password"]
        user = user_collection.find_one({"username": user_id, "password": pw})
        if user:
            session["username"] = user_id
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="아이디 또는 비밀번호가 틀렸습니다.")
    return render_template("login.html")

# ✅ 로그아웃
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# ✅ 마이페이지
@app.route("/mypage")
@login_required
def mypage():
    return render_template("mypage.html", username=session["username"])

# ✅ 회원가입
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        new_user = {
            "username": request.form["username"],
            "password": request.form["password"],
            "name": request.form["name"],
            "email": f"{request.form['email_id']}@{request.form['email_domain']}",
            "phone": request.form["phone"],
            "department": request.form["department"]
        }
        user_collection.insert_one(new_user)
        return redirect(url_for("login"))
    return render_template("signup.html")

# ✅ 개인정보 수정
@app.route("/profile_edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        email_id = request.form.get("email_id")
        email_domain = request.form.get("email_domain")
        phone = request.form.get("phone")
        department = request.form.get("department")
        email = f"{email_id}@{email_domain}"

        user_collection.update_one(
            {"username": session["username"]},
            {"$set": {
                "name": name,
                "password": password,
                "email": email,
                "phone": phone,
                "department": department
            }}
        )
        return redirect(url_for("mypage"))

    user = user_collection.find_one({"username": session["username"]})

    if not user:
        user = {
            "username": session["username"],
            "name": "개발용 유저",
            "email": "dev@example.com",
            "phone": "010-1234-5678",
            "department": "개발팀"
        }
        user_collection.insert_one(user)

    if "email" in user and "@" in user["email"]:
        user["email_id"], user["email_domain"] = user["email"].split("@")

    return render_template("profile_edit.html", user=user)

# ✅ 회원탈퇴
@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    username = session.get("username")
    if request.method == "POST":
        user_collection.delete_one({"username": username})
        session.clear()
        return redirect(url_for("login"))
    return render_template("delete_account.html", username=username)

# ✅ 개발용 테스트 로그인
@app.route("/dev_login")
def dev_login():
    session["username"] = "testuser"
    return redirect(url_for("profile_edit"))

# ✅ 실행
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
