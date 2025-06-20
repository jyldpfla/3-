from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from dotenv import load_dotenv
from functools import wraps
import os

# .env 파일 로드
load_dotenv()

# 환경변수 가져오기
user_env = os.getenv("MONGO_USER").strip('"')
print("✅ USER ENV =", user_env)
print("🔍 정확한 값 (repr):", repr(user_env))

# 형식 검증
if not user_env or ":" not in user_env:
    raise ValueError("❌ MONGO_USER 환경변수가 없거나 '아이디:비밀번호' 형식이 아님")

# username:password 분리
username, password = user_env.split(":")

# MongoDB URI 생성 및 연결
cluster = "team3.fxbwcnh.mongodb.net"
uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["team3"]
user_collection = db["users"]

# Flask 앱 생성
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션 암호화용 키

# 로그인 확인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# 홈 페이지 (로그인 필요)
@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session["username"])

# 로그인 페이지
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

# 로그아웃
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# 마이페이지 (로그인 필요)
@app.route("/mypage")
@login_required
def mypage():
    return render_template("mypage.html", username=session["username"])

# 실행
if __name__ == "__main__":
    app.run(debug=True)
