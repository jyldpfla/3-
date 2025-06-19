from flask import Flask, render_template, request # request 모듈 추가
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from bson import ObjectId

# .env 파일에서 환경변수 로드
load_dotenv()
user = os.getenv("USER")
# uri = f"mongodb+srv://{user}@team3.fxbwcnh.mongodb.net/" # 실제 MongoDB 연결 시 사용

# Flask 앱 생성
app = Flask(__name__, static_folder='static', template_folder='templates')

# MongoDB 연결 (더미 데이터 사용을 위해 실제 연결은 주석 처리합니다.
# 실제 DB 연동 시에는 아래 주석을 해제하고 사용하세요.)
# client = MongoClient(uri)
# db = client['team3']

# 컬렉션 정의 (더미 데이터와 매핑)
# project_collection = db["projects"]
# user_collection = db["users"]
# schedule_collection = db["schedules"]
# personal_todo_collection = db["personal_todo"]
# board_collection = db["board"]
# team_collection = db["team"]


# --- 더미 데이터 시작 ---
# 예시: 가상의 ObjectId 생성 함수 (실제 DB에서는 DB가 생성해줌)
def get_dummy_object_id():
    return str(ObjectId())

dummy_user_id_hong = get_dummy_object_id()
dummy_user_id_kim = get_dummy_object_id()
dummy_project_id_a = get_dummy_object_id()
dummy_project_id_b = get_dummy_object_id()
dummy_project_id_c = get_dummy_object_id()


dummy_project_data_a = {
    "_id": ObjectId(dummy_project_id_a), # 실제 ObjectId
    "title": "프로젝트 A",
    "description": "웹 기반 협업 툴 개발",
    "goal": "효율적인 협업 제공",
    "scope": "기획, 개발, 테스트 포함",
    "schedule": {"startDate": "2025-07-01", "endDate": "2025-09-30"},
    "budget": 10000000,
    "outcome": "MVP 개발 완료",
    "createAt": "2025-06-01",
    "updateAt": "2025-06-10",
    "client": "OO 기업",
    "TeamId": get_dummy_object_id(), # 더미 ID
    "ScheduleListId": get_dummy_object_id() # 더미 ID
}

dummy_project_data_b = {
    "_id": ObjectId(dummy_project_id_b), # 실제 ObjectId
    "title": "프로젝트 B",
    "description": "모바일 앱 UI/UX 개선",
    "goal": "사용자 경험 향상",
    "scope": "기존 앱 분석, 디자인, 테스트",
    "schedule": {"startDate": "2025-08-01", "endDate": "2025-10-31"},
    "budget": 5000000,
    "outcome": "개선된 UI/UX 적용",
    "createAt": "2025-07-01",
    "updateAt": "2025-07-15",
    "client": "스타트업 X",
    "TeamId": get_dummy_object_id(),
    "ScheduleListId": get_dummy_object_id()
}

dummy_project_data_c = {
    "_id": ObjectId(dummy_project_id_c), # 실제 ObjectId
    "title": "프로젝트 C",
    "description": "AI 기반 데이터 분석 시스템 구축",
    "goal": "데이터 활용 효율 증대",
    "scope": "데이터 수집, 모델링, 대시보드 개발",
    "schedule": {"startDate": "2025-09-01", "endDate": "2026-01-31"},
    "budget": 20000000,
    "outcome": "실시간 데이터 분석 시스템",
    "createAt": "2025-08-01",
    "updateAt": "2025-08-20",
    "client": "대기업 Y",
    "TeamId": get_dummy_object_id(),
    "ScheduleListId": get_dummy_object_id()
}


dummy_user_data_hong = {
    "_id": ObjectId(dummy_user_id_hong), # 실제 ObjectId
    "email": "hong@example.com",
    "name": "홍길동 대리",
    "userPassword": "hashed_password123",
    "role": "기획자",
    "profile": "프로젝트 기획 담당",
    "department": "기획팀",
    "position": "대리",
    "createAt": "2025-01-01",
    "phone_num": "010-1111-2222",
    "Personal_todoId": get_dummy_object_id(),
    "BoardId": get_dummy_object_id()
}

dummy_user_data_kim = {
    "_id": ObjectId(dummy_user_id_kim), # 실제 ObjectId
    "email": "kim@example.com",
    "name": "김대두 과장",
    "userPassword": "hashed_password456",
    "role": "개발자",
    "profile": "백엔드 개발 담당",
    "department": "개발팀",
    "position": "과장",
    "createAt": "2024-05-01",
    "phone_num": "010-3333-4444",
    "Personal_todoId": get_dummy_object_id(),
    "BoardId": get_dummy_object_id()
}


# 2025년 6월 18일 기준의 일정 더미 데이터
dummy_schedules = [
    {   # 프로젝트 A 관련 일정 (1.png의 선택된 일정)
        "projectId": ObjectId(dummy_project_id_a),
        "title": "프로젝트 A", # 이미지와 일치시키기 위해 짧게
        "schedule_name": "프로젝트 A", # 상세 정보에 표시될 이름
        "schedule": {"startDate": "2025-06-18 09:00", "endDate": "2025-06-20 10:00"}, # 1.png에 맞게 시간 조정
        "writer": ObjectId(dummy_user_id_hong),
        "member": "기획팀, 개발팀",
        "content": "공사시작 지연 사유서 일반 민원 프로젝트 지연", # 4.png의 내용
        "update_date": "2025-06-17",
        "create_date": "2025-06-10",
        "type": "프로젝트",
        "status": "progress", # UI 표시를 위한 상태 (CSS 클래스명과 일치)
        "tasks": [ # UI 표시를 위한 세부 업무 목록 (content를 파싱하거나 별도 필드로)
            {"name": "업무 1: 완료", "status": "completed"},
            {"name": "업무 2: 진행중", "status": "progress"},
            {"name": "업무 3: 미완료", "status": "pending"}, # 미완료로 변경
        ]
    },
    {   # 프로젝트 B 관련 일정 (더미)
        "projectId": ObjectId(dummy_project_id_b),
        "title": "프로젝트 B",
        "schedule_name": "디자인 시안 검토",
        "schedule": {"startDate": "2025-06-18 10:00", "endDate": "2025-06-19 17:00"},
        "writer": ObjectId(dummy_user_id_kim),
        "member": "디자인팀",
        "content": "모바일 앱 디자인 시안 최종 검토 및 피드백 반영.",
        "update_date": "2025-06-16",
        "create_date": "2025-06-15",
        "type": "프로젝트",
        "status": "pending", # 미완료
        "tasks": []
    },
    {   # 홍길동 대리 휴가 (업무일정 (휴가).png의 선택된 일정)
        "projectId": None, # 개인 일정은 projectId가 없을 수 있음
        "title": "홍길동 대리 휴가",
        "schedule_name": "홍길동 대리 휴가", # 상세 정보에 표시될 이름
        "schedule": {"startDate": "2025-06-18 09:00", "endDate": "2025-06-20 18:00"},
        "writer": ObjectId(dummy_user_id_hong),
        "member": "홍길동 대리",
        "content": "가족여행",
        "update_date": "2025-06-17",
        "create_date": "2025-06-01",
        "type": "개인",
        "status": "holiday", # UI 표시를 위한 상태 (CSS 클래스명과 일치)
        "tasks": [] # 휴가에는 세부 업무가 없음
    },
    {   # 김대두 과장 출장 (더미)
        "projectId": None, # 개인 일정은 projectId가 없을 수 있음
        "title": "김대두 과장 출장",
        "schedule_name": "김대두 과장 출장",
        "schedule": {"startDate": "2025-06-18 09:00", "endDate": "2025-06-18 18:00"},
        "writer": ObjectId(dummy_user_id_kim),
        "member": "김대두 과장",
        "content": "서울 본사 출장, 중요 미팅 참석",
        "update_date": "2025-06-17",
        "create_date": "2025-06-16",
        "type": "개인",
        "status": "출장", # UI 표시를 위한 상태 (CSS에 추가 필요)
        "tasks": []
    }
]

# 더미 데이터에서 writer와 projectId에 해당하는 name/title 조회 함수 (UI 표시용)
def get_user_name_by_id(user_id):
    if user_id == ObjectId(dummy_user_id_hong):
        return dummy_user_data_hong["name"]
    elif user_id == ObjectId(dummy_user_id_kim):
        return dummy_user_data_kim["name"]
    return "알 수 없음"

def get_project_title_by_id(project_id):
    if project_id == ObjectId(dummy_project_id_a):
        return dummy_project_data_a["title"]
    elif project_id == ObjectId(dummy_project_id_b):
        return dummy_project_data_b["title"]
    elif project_id == ObjectId(dummy_project_id_c):
        return dummy_project_data_c["title"]
    return "알 수 없음"

# 날짜 문자열을 datetime 객체로 파싱하고, datetime-local 형식으로 포맷하는 헬퍼 함수
def format_datetime_for_input(dt_str):
    if not dt_str:
        return ""
    try:
        # 입력 문자열이 AM/PM을 포함할 경우 파싱
        if "AM" in dt_str or "PM" in dt_str:
            dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M%p") # %p는 AM/PM
        else:
            dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return dt_obj.strftime("%Y-%m-%dT%H:%M") # datetime-local 형식
    except ValueError:
        return "" # 파싱 실패 시 빈 문자열 반환


# --- 더미 데이터 끝 ---


# 라우팅
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/example")
def example():
    return render_template("example.html")

@app.route("/timeline")
def timeline():
    # 쿼리 파라미터에서 선택된 스케줄 ID를 가져옵니다.
    # 예: /timeline?schedule_id=홍길동대리휴가
    # 초기 로드 시 기본값으로 '프로젝트 A' 상세 정보를 표시하도록 설정합니다.
    selected_schedule_id_param = request.args.get('schedule_id', '프로젝트 A')

    # 현재 날짜 설정 (이미지 기준: 2025.06.18)
    current_year_month_str = "2025.06"
    current_day_int = 18

    # 캘린더 날짜 데이터 생성
    calendar_days = []
    
    # 2025년 6월 1일은 일요일 (weekday()는 월요일 0, 일요일 6)
    # 이미지 캘린더는 월요일부터 시작하고, 6월 1일이 일요일이므로,
    # 캘린더 시작일은 5월 26일 (월요일)이어야 함
    # 2025-06-01은 일요일 (Python weekday() -> 6)
    # 6월 1일의 weekday가 6 (일)이므로, 첫째 주 월요일은 (6 - 0) % 7 = 6일 전, 즉 5월 26일 (2025-06-01 - 6일)
    first_day_of_month = datetime(2025, 6, 1)
    # Python의 weekday()는 월(0) ~ 일(6)
    # 우리가 원하는 캘린더는 월(0) ~ 일(6)
    # 6월 1일 (일요일, weekday=6)이 캘린더의 일요일 칸에 오도록 하려면,
    # 캘린더의 첫 번째 월요일은 6월 1일에서 6일을 빼야 한다.
    start_date_for_calendar = first_day_of_month - timedelta(days=first_day_of_month.weekday() + 7 - 1)
    # 5월 26일부터 시작하면 된다. (2025년 5월 26일은 월요일)

    # 6주 (42칸)의 캘린더 생성
    for i in range(42): # 6주 * 7일 = 42일
        current_date = start_date_for_calendar + timedelta(days=i)
        
        day = current_date.day
        month = current_date.month
        year = current_date.year

        # 현재 캘린더가 2025년 6월을 표시하고 있으므로, 해당 월의 날짜만 is_current_month로 표시
        is_current_month_display = (month == 6 and year == 2025)
        
        is_current_day_display = (is_current_month_display and day == current_day_int)
        
        calendar_days.append({
            "day": day,
            "is_current_month": is_current_month_display,
            "is_current_day": is_current_day_display
        })

    # 2025.06.18의 일정 필터링 및 필요한 정보 추가
    daily_schedules_for_display = []
    for sched in dummy_schedules:
        # 시작 날짜가 "2025-06-18"로 시작하는 일정만 필터링
        if sched["schedule"]["startDate"].startswith("2025-06-18"):
            display_name = ""
            tag_class = ""
            if sched["type"] == "프로젝트":
                display_name = get_project_title_by_id(sched["projectId"])
                # 프로젝트 A, B, C에 따라 태그 클래스 지정
                if display_name == "프로젝트 A":
                    tag_class = "project-a"
                elif display_name == "프로젝트 B":
                    tag_class = "project-b"
                elif display_name == "프로젝트 C":
                    tag_class = "project-c"
            elif sched["type"] == "개인":
                display_name = sched["title"] # 개인 일정의 경우 제목 자체가 이름
                tag_class = "personal-tag" # 개인 일정에 대한 일반 태그 클래스

            daily_schedules_for_display.append({
                "name": display_name,
                "tag_class": tag_class,
                "title": sched["title"] # 원본 제목 (예: "홍길동 대리 휴가")
            })

    # 선택된 업무 상세 정보 (쿼리 파라미터에 따라 변경)
    selected_schedule = None
    for sched in dummy_schedules:
        if sched["title"] == selected_schedule_id_param: # title 필드로 검색
            selected_schedule = sched
            break
    
    # 기본값 설정: 쿼리 파라미터가 없거나 일치하는 스케줄이 없으면 '프로젝트 A'를 기본으로 보여줌
    if not selected_schedule:
        for sched in dummy_schedules:
            if sched["title"] == "프로젝트 A": # 기본 상세 정보
                selected_schedule = sched
                break

    selected_schedule_detail = {}
    if selected_schedule:
        selected_schedule_detail = {
            "type": selected_schedule["type"],
            # 상세 정보 상단의 태그 클래스 결정 로직
            "tag_class": "", # 기본값
            "schedule_name": selected_schedule["schedule_name"],
            "person_name": get_user_name_by_id(selected_schedule["writer"]) if selected_schedule["writer"] else "N/A",
            "status": selected_schedule["status"],
            "start_date": format_datetime_for_input(selected_schedule["schedule"]["startDate"]), # 날짜 포맷 변경
            "end_date": format_datetime_for_input(selected_schedule["schedule"]["endDate"]), # 날짜 포맷 변경
            "content": selected_schedule["content"],
            "tasks": selected_schedule.get("tasks", [])
        }
        # 상세 정보에 표시될 태그 클래스
        if selected_schedule_detail["type"] == "프로젝트":
            project_title = get_project_title_by_id(selected_schedule["projectId"])
            if project_title == "프로젝트 A":
                selected_schedule_detail["tag_class"] = "project-a"
            elif project_title == "프로젝트 B":
                selected_schedule_detail["tag_class"] = "project-b"
            elif project_title == "프로젝트 C":
                selected_schedule_detail["tag_class"] = "project-c"
        elif selected_schedule_detail["type"] == "개인":
            selected_schedule_detail["tag_class"] = "personal-tag" # 개인 태그는 별도의 클래스를 가짐

        # content와 tasks가 동시에 넘어가지 않도록 처리
        if selected_schedule_detail["tasks"]:
            selected_schedule_detail["content"] = None # tasks가 있으면 content는 비움
        else:
            selected_schedule_detail["tasks"] = None # content가 있으면 tasks는 비움


    return render_template(
        "timeline.html",
        current_year_month=current_year_month_str,
        calendar_days=calendar_days,
        daily_schedules=daily_schedules_for_display,
        selected_schedule_detail=selected_schedule_detail
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)