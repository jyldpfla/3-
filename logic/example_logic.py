from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
from bson import ObjectId
import calendar

app = Flask(__name__, static_folder='static', template_folder='templates')

# --- 더미 데이터 시작 ---
def get_dummy_object_id_str():
    return str(ObjectId())

dummy_user_id_hong = get_dummy_object_id_str()
dummy_user_id_kim = get_dummy_object_id_str()
dummy_project_id_a = get_dummy_object_id_str()
dummy_project_id_b = get_dummy_object_id_str()
dummy_project_id_c = get_dummy_object_id_str()

dummy_users = {
    dummy_user_id_hong: {"name": "홍길동 대리"},
    dummy_user_id_kim: {"name": "김대두 과장"}
}

dummy_projects = {
    dummy_project_id_a: {"title": "프로젝트 A"},
    dummy_project_id_b: {"title": "프로젝트 B"},
    dummy_project_id_c: {"title": "프로젝트 C"},
}

# 더미 스케줄 데이터 (날짜 다양화 및 2025년 6월 18일뿐 아니라 다른 날짜에도 배치)
dummy_schedules = [
    { # 6월 18일 (수)
        "_id": get_dummy_object_id_str(),
        "projectId": dummy_project_id_a,
        "schedule_id_param": "프로젝트A_웹협업툴",
        "schedule_title": "프로젝트 A",
        "schedule_name": "웹 기반 협업 툴 개발 진행",
        "schedule": {
            "startDate": datetime(2025, 6, 18, 9, 0),
            "endDate": datetime(2025, 6, 20, 10, 0)
        },
        "writer": dummy_user_id_hong,
        "member": "기획팀, 개발팀", # 이 필드는 프론트엔드에서 제거되지만, 데이터는 유지
        "content": None,
        "update_date": datetime(2025, 6, 17),
        "create_date": datetime(2025, 6, 10),
        "type": "프로젝트",
        "status": "진행중", # 상태 업데이트
        "tasks": [ # tasks는 백엔드에서 유지하지만 UI에서 제거됨
            {"name": "업무 1: 완료", "status": "completed"},
            {"name": "업무 2: 진행중", "status": "progress"},
            {"name": "업무 3: 미완료", "status": "pending"},
        ]
    },
    { # 6월 18일 (수)
        "_id": get_dummy_object_id_str(),
        "projectId": dummy_project_id_b,
        "schedule_id_param": "프로젝트B_UIUX검토",
        "schedule_title": "프로젝트 B",
        "schedule_name": "모바일 앱 UI/UX 디자인 검토",
        "schedule": {
            "startDate": datetime(2025, 6, 18, 10, 0),
            "endDate": datetime(2025, 6, 19, 17, 0)
        },
        "writer": dummy_user_id_kim,
        "member": "디자인팀",
        "content": "모바일 앱 디자인 시안 최종 검토 및 피드백 반영.",
        "update_date": datetime(2025, 6, 16),
        "create_date": datetime(2025, 6, 15),
        "type": "프로젝트",
        "status": "지연", # 상태 업데이트
        "tasks": []
    },
    { # 6월 18일 (수)
        "_id": get_dummy_object_id_str(),
        "projectId": None,
        "schedule_id_param": "김대두과장_휴가",
        "schedule_title": "김대두 과장 휴가",
        "schedule_name": "김대두 과장 여름 휴가",
        "schedule": {
            "startDate": datetime(2025, 6, 18, 9, 0),
            "endDate": datetime(2025, 6, 20, 18, 0)
        },
        "writer": dummy_user_id_kim,
        "member": "김대두 과장",
        "content": "가족여행",
        "update_date": datetime(2025, 6, 17),
        "create_date": datetime(2025, 6, 1),
        "type": "개인",
        "status": "연차", # 상태 업데이트
        "tasks": []
    },
    { # 6월 19일 (목)
        "_id": get_dummy_object_id_str(),
        "projectId": dummy_project_id_c,
        "schedule_id_param": "프로젝트C_회의",
        "schedule_title": "프로젝트 C",
        "schedule_name": "주간 프로젝트 회의",
        "schedule": {
            "startDate": datetime(2025, 6, 19, 14, 0),
            "endDate": datetime(2025, 6, 19, 15, 0)
        },
        "writer": dummy_user_id_hong,
        "member": "전체 팀원",
        "content": "다음 주 업무 분배 및 진행 상황 공유",
        "update_date": datetime(2025, 6, 18),
        "create_date": datetime(2025, 6, 17),
        "type": "프로젝트",
        "status": "진행중", # 상태 업데이트
        "tasks": []
    },
    { # 6월 20일 (금)
        "_id": get_dummy_object_id_str(),
        "projectId": None,
        "schedule_id_param": "홍길동대리_병원",
        "schedule_title": "홍길동 대리 개인 일정",
        "schedule_name": "정기 건강 검진",
        "schedule": {
            "startDate": datetime(2025, 6, 20, 9, 0),
            "endDate": datetime(2025, 6, 20, 12, 0)
        },
        "writer": dummy_user_id_hong,
        "member": "본인",
        "content": "강남병원 방문",
        "update_date": datetime(2025, 6, 19),
        "create_date": datetime(2025, 6, 18),
        "type": "개인",
        "status": "병가", # 상태 업데이트
        "tasks": []
    },
    { # 6월 21일 (토) - 주말 일정
        "_id": get_dummy_object_id_str(),
        "projectId": None,
        "schedule_id_param": "주말_취미",
        "schedule_title": "개인 취미 활동",
        "schedule_name": "테니스 레슨",
        "schedule": {
            "startDate": datetime(2025, 6, 21, 10, 0),
            "endDate": datetime(2025, 6, 21, 11, 0)
        },
        "writer": dummy_user_id_kim,
        "member": "김대두 과장",
        "content": "잠실 테니스장",
        "update_date": datetime(2025, 6, 20),
        "create_date": datetime(2025, 6, 19),
        "type": "개인",
        "status": "월차", # 상태 업데이트
        "tasks": []
    },
    { # 6월 24일 (화) - 출장 일정 추가
        "_id": get_dummy_object_id_str(),
        "projectId": None,
        "schedule_id_param": "홍길동대리_출장",
        "schedule_title": "홍길동 대리 개인 일정", # "개인" 타입으로 변경
        "schedule_name": "제주 지사 미팅 (출장)", # 이름에 출장 표기
        "schedule": {
            "startDate": datetime(2025, 6, 24, 9, 0),
            "endDate": datetime(2025, 6, 25, 18, 0)
        },
        "writer": dummy_user_id_hong,
        "member": "홍길동 대리",
        "content": "제주 지사 시스템 도입 회의",
        "update_date": datetime(2025, 6, 23),
        "create_date": datetime(2025, 6, 20),
        "type": "개인", # "개인" 타입으로 변경
        "status": "출장", # 상태는 "출장" 유지
        "tasks": []
    },
    { # 2025년 5월 10일 (토) - 이전 달 일정
        "_id": get_dummy_object_id_str(),
        "projectId": None,
        "schedule_id_param": "5월_워크숍",
        "schedule_title": "워크숍",
        "schedule_name": "팀 빌딩 워크숍",
        "schedule": {
            "startDate": datetime(2025, 5, 10, 10, 0),
            "endDate": datetime(2025, 5, 10, 17, 0)
        },
        "writer": dummy_user_id_hong,
        "member": "전체 팀원",
        "content": "팀 결속력 강화를 위한 워크숍",
        "update_date": datetime(2025, 5, 5),
        "create_date": datetime(2025, 5, 1),
        "type": "프로젝트",
        "status": "완료",
        "tasks": []
    },
    { # 2025년 7월 5일 (토) - 다음 달 일정
        "_id": get_dummy_object_id_str(),
        "projectId": dummy_project_id_a,
        "schedule_id_param": "7월_프로젝트A_착수",
        "schedule_title": "프로젝트 A",
        "schedule_name": "프로젝트 A 2단계 착수 회의",
        "schedule": {
            "startDate": datetime(2025, 7, 5, 13, 0),
            "endDate": datetime(2025, 7, 5, 15, 0)
        },
        "writer": dummy_user_id_kim,
        "member": "개발팀, 기획팀",
        "content": "프로젝트 A 2단계 기획 및 개발 착수",
        "update_date": datetime(2025, 6, 30),
        "create_date": datetime(2025, 6, 25),
        "type": "프로젝트",
        "status": "진행중",
        "tasks": []
    }
]

def get_user_id_by_name(user_name):
    for uid, uinfo in dummy_users.items():
        if uinfo["name"] == user_name:
            return uid
    # 새로운 이름이 들어오면 새로운 ID 할당 및 더미 유저에 추가 (예시 목적)
    new_id = get_dummy_object_id_str()
    dummy_users[new_id] = {"name": user_name}
    return new_id

def get_user_name_by_id(user_id):
    return dummy_users.get(user_id, {}).get("name", "알 수 없음")

def get_project_title_by_id(project_id):
    return dummy_projects.get(project_id, {}).get("title", "알 수 없음")

# AM/PM을 포함하는 날짜/시간 형식
def format_datetime_for_display(dt_obj):
    if not isinstance(dt_obj, datetime):
        return ""
    # %p는 로케일에 따라 AM/PM을 출력합니다.
    return dt_obj.strftime("%Y.%m.%d %I:%M %p").replace('AM', '오전').replace('PM', '오후')

def format_datetime_for_input(dt_obj):
    if not isinstance(dt_obj, datetime):
        return ""
    return dt_obj.strftime("%Y-%m-%dT%H:%M")

# --- 더미 데이터 끝 ---

@app.route("/")
def home():
    # 메인 페이지 진입 시 바로 타임라인 페이지로 리다이렉트
    return redirect(url_for('timeline'))

@app.route("/timeline")
def timeline():
    # URL 쿼리 파라미터에서 연도, 월, 선택된 날짜 가져오기
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    selected_date_str = request.args.get('date')

    today = datetime.now().date()

    # 현재 연도, 월 설정 (URL 파라미터가 없으면 오늘 날짜 기준)
    if year is None or month is None:
        current_view_date = today
        year = current_view_date.year
        month = current_view_date.month
    else:
        try:
            current_view_date = datetime(year, month, 1).date()
        except ValueError: # 유효하지 않은 연도/월이면 오늘 날짜 기준
            current_view_date = today
            year = current_view_date.year
            month = current_view_date.month

    # 선택된 날짜 설정 (URL 파라미터가 없으면 현재 달의 오늘 날짜)
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = current_view_date # 유효하지 않은 날짜면 현재 캘린더의 첫 날
    else:
        # URL에 date 파라미터가 없으면, 현재 캘린더 월의 오늘 날짜를 선택
        # 만약 오늘 날짜가 현재 캘린더 월에 속하지 않으면, 캘린더 월의 1일로 설정
        if today.year == year and today.month == month:
            selected_date = today
        else:
            selected_date = datetime(year, month, 1).date()

    # 캘린더 날짜 계산
    cal = calendar.Calendar(firstweekday=0) # 월요일을 한 주의 시작으로 설정 (0:월, 6:일)
    month_days = cal.monthdayscalendar(year, month)

    calendar_days = []
    for week in month_days:
        for day_num in week:
            if day_num == 0: # 해당 월에 속하지 않는 날 (0으로 채워짐)
                calendar_days.append({
                    "day": "",
                    "is_current_month": False,
                    "is_current_day": False,
                    "full_date": ""
                })
            else:
                current_date_in_calendar = datetime(year, month, day_num).date()
                is_selected_day = (current_date_in_calendar == selected_date)
                
                calendar_days.append({
                    "day": day_num,
                    "is_current_month": True, # 해당 월에 속하는 날은 True
                    "is_current_day": is_selected_day,
                    "full_date": current_date_in_calendar.strftime("%Y-%m-%d")
                })
    
    # 이날의 일정 목록 (선택된 날짜 기준)
    daily_schedules_for_display = []
    for sched in dummy_schedules:
        # 일정의 시작일이 선택된 날짜와 같거나, 기간 내에 포함되는 경우
        if sched["schedule"]["startDate"].date() == selected_date or \
           (sched["schedule"]["startDate"].date() < selected_date and sched["schedule"]["endDate"].date() >= selected_date):
            tag_class = ""
            if sched["type"] == "프로젝트":
                tag_class = "project-tag"
            elif sched["type"] == "개인":
                if sched["status"] == "출장":
                    tag_class = "travel-tag"
                else:
                    tag_class = "personal-tag"

            daily_schedules_for_display.append({
                "name": sched["schedule_name"],
                "tag_class": tag_class,
                "schedule_id_param": sched["schedule_id_param"]
            })

    # URL 쿼리 파라미터에서 schedule_id_param 가져오기 (기본값: 해당 날짜의 첫 번째 일정 또는 전체 첫 번째 일정)
    daily_schedules_at_date = [
        s for s in dummy_schedules 
        if s["schedule"]["startDate"].date() == selected_date or \
           (s["schedule"]["startDate"].date() < selected_date and s["schedule"]["endDate"].date() >= selected_date)
    ]
    
    # selected_schedule_id_param이 주어졌다면 해당 일정을 찾고, 아니면 daily_schedules_at_date의 첫 번째 또는 dummy_schedules의 첫 번째를 기본으로
    default_schedule_param = ""
    if daily_schedules_at_date:
        default_schedule_param = daily_schedules_at_date[0]["schedule_id_param"]
    elif dummy_schedules:
        default_schedule_param = dummy_schedules[0]["schedule_id_param"]
    
    selected_schedule_id_param = request.args.get('schedule_id', default_schedule_param)

    # 선택된 일정 상세 정보
    selected_schedule_detail = {}
    found_selected_schedule = False
    for sched in dummy_schedules:
        if sched["schedule_id_param"] == selected_schedule_id_param:
            selected_schedule = sched
            found_selected_schedule = True
            break
    
    # 선택된 일정이 없거나 유효하지 않으면, 기본적으로 해당 날짜의 첫 번째 일정 또는 첫 번째 전체 일정을 표시
    if not found_selected_schedule:
        if daily_schedules_at_date:
            selected_schedule = daily_schedules_at_date[0]
        elif dummy_schedules:
            selected_schedule = dummy_schedules[0]
        else:
            selected_schedule = None # 일정이 전혀 없는 경우

    if selected_schedule:
        # 선택된 일정의 표시 제목 결정
        display_title = ""
        if selected_schedule["type"] == "개인":
            display_title = "개인"
        elif selected_schedule["type"] == "프로젝트":
            display_title = get_project_title_by_id(selected_schedule["projectId"])

        selected_schedule_detail = {
            "schedule_id_param": selected_schedule["schedule_id_param"],
            "type": selected_schedule["type"],
            "tag_class": "", 
            "schedule_title": display_title, # 여기서 display_title 사용
            "schedule_name": selected_schedule["schedule_name"],
            "person_name": get_user_name_by_id(selected_schedule["writer"]), # 이름 필드 유지
            "status": selected_schedule["status"],
            "start_date": format_datetime_for_display(selected_schedule["schedule"]["startDate"]),
            "end_date": format_datetime_for_display(selected_schedule["schedule"]["endDate"]),
            "start_date_input": format_datetime_for_input(selected_schedule["schedule"]["startDate"]),
            "end_date_input": format_datetime_for_input(selected_schedule["schedule"]["endDate"]),
            "content": selected_schedule["content"],
            "tasks": selected_schedule.get("tasks", []), # tasks는 데이터로 유지하되, UI에서 제거
            "member": selected_schedule.get("member", "") # member도 데이터로 유지하되, UI에서 제거
        }
        
        if selected_schedule_detail["type"] == "프로젝트":
            selected_schedule_detail["tag_class"] = "project-tag"
        elif selected_schedule_detail["type"] == "개인":
            # 개인 타입이면서 상태가 '출장'이면 'travel-tag' 부여
            if selected_schedule_detail["status"] == "출장":
                selected_schedule_detail["tag_class"] = "travel-tag"
            else:
                selected_schedule_detail["tag_class"] = "personal-tag"

    # 상태 옵션을 타입별로 분류하여 전달
    status_options_by_type = {
        "개인": [
            {"value": "연차", "text": "연차"},
            {"value": "월차", "text": "월차"},
            {"value": "병가", "text": "병가"},
            {"value": "출장", "text": "출장"}, # '출장' 상태를 개인 타입에 추가
        ],
        "프로젝트": [
            {"value": "진행중", "text": "진행중"},
            {"value": "중단", "text": "중단"},
            {"value": "지연", "text": "지연"},
            {"value": "완료", "text": "완료"},
            {"value": "미완료", "text": "미완료"},
        ]
    }

    return render_template(
        "timeline.html",
        current_year=year, # 현재 캘린더 연도 전달
        current_month=month, # 현재 캘린더 월 전달
        current_year_month=f"{year}.{month:02d}", # 표시용 YYYY.MM 형식
        calendar_days=calendar_days,
        daily_schedules=daily_schedules_for_display,
        selected_schedule_detail=selected_schedule_detail,
        project_titles=[proj["title"] for proj in dummy_projects.values()],
        status_options_by_type=status_options_by_type, # 타입별 상태 옵션 전달
        selected_date_display=selected_date.strftime("%Y.%m.%d") # 우측 상단 표시용 날짜
    )

# 특정 날짜의 일정 목록을 JSON으로 반환하는 API (새로 추가)
@app.route('/api/schedules_by_date', methods=['GET'])
def get_schedules_by_date():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "날짜 파라미터가 필요합니다."}), 400
    
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "유효하지 않은 날짜 형식입니다. YYYY-MM-DD 형식이어야 합니다."}), 400

    schedules_on_date = []
    for sched in dummy_schedules:
        # 시작일이 쿼리 날짜와 같거나, 시작일과 종료일 사이에 쿼리 날짜가 포함되는 경우
        if sched["schedule"]["startDate"].date() == query_date or \
           (sched["schedule"]["startDate"].date() < query_date and sched["schedule"]["endDate"].date() >= query_date):
            tag_class = ""
            if sched["type"] == "프로젝트":
                tag_class = "project-tag"
            elif sched["type"] == "개인":
                # 개인 타입이면서 상태가 '출장'이면 'travel-tag' 부여
                if sched["status"] == "출장":
                    tag_class = "travel-tag"
                else:
                    tag_class = "personal-tag"
            
            schedules_on_date.append({
                "name": sched["schedule_name"],
                "tag_class": tag_class,
                "schedule_id_param": sched["schedule_id_param"]
            })
    
    return jsonify(schedules_on_date)

# 기존 일정 생성/수정/삭제 API는 변경 없음 (이전 코드와 동일)
@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    data = request.json
    try:
        start_dt = datetime.strptime(data["start_date"], '%Y-%m-%dT%H:%M')
        end_dt = datetime.strptime(data["end_date"], '%Y-%m-%dT%H:%M')
    except ValueError as e:
        return jsonify({"success": False, "message": f"잘못된 날짜/시간 형식입니다: {e}"}), 400

    # 이름 필드에서 사용자 ID를 가져오거나 새로 생성
    writer_id_to_use = get_user_id_by_name(data.get("writer_name"))

    project_id_to_use = None
    schedule_title_for_db = data["schedule_name"] # 기본적으로 일정 이름
    if data["type"] == "프로젝트":
        project_id_to_use = next((pid for pid, pinfo in dummy_projects.items() if pinfo["title"] == data.get("project_title")), None)
        if project_id_to_use:
            schedule_title_for_db = dummy_projects[project_id_to_use]["title"] # 프로젝트 타입이면 프로젝트 제목으로 설정

    new_schedule_id_param = data["schedule_name"].replace(" ", "_") + "_" + get_dummy_object_id_str()[:4]

    new_schedule = {
        "_id": get_dummy_object_id_str(),
        "projectId": project_id_to_use,
        "schedule_id_param": new_schedule_id_param,
        "schedule_title": schedule_title_for_db, # DB에 저장될 제목
        "schedule_name": data["schedule_name"],
        "schedule": {
            "startDate": start_dt,
            "endDate": end_dt
        },
        "writer": writer_id_to_use, # 업데이트된 writer_id_to_use 사용
        "member": data.get("member", ""), # UI에서 필드가 제거되었지만, 서버에 빈 값으로 보냄 (데이터베이스 스키마를 유지하기 위해)
        "content": data.get("content"),
        "update_date": datetime.now(),
        "create_date": datetime.now(),
        "type": data["type"],
        "status": data["status"],
        "tasks": data.get("tasks", []) # UI에서 필드가 제거되었지만, 서버에 빈 배열로 보냄
    }
    global dummy_schedules
    dummy_schedules.append(new_schedule)
    return jsonify({"success": True, "message": "일정이 성공적으로 추가되었습니다.", "new_schedule_id": new_schedule_id_param})

@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    data = request.json
    original_schedule_id_param = data["original_schedule_id_param"]

    try:
        start_dt = datetime.strptime(data["start_date"], '%Y-%m-%dT%H:%M')
        end_dt = datetime.strptime(data["end_date"], '%Y-%m-%dT%H:%M')
    except ValueError as e:
        return jsonify({"success": False, "message": f"잘못된 날짜/시간 형식입니다: {e}"}), 400

    found = False
    global dummy_schedules
    for i, sched in enumerate(dummy_schedules):
        if sched["schedule_id_param"] == original_schedule_id_param:
            # 이름 필드에서 사용자 ID를 가져오거나 새로 생성
            writer_id_to_use = get_user_id_by_name(data.get("writer_name"))

            project_id_to_use = None
            schedule_title_for_db = data["schedule_name"] # 기본적으로 일정 이름
            if data["type"] == "프로젝트":
                project_id_to_use = next((pid for pid, pinfo in dummy_projects.items() if pinfo["title"] == data.get("project_title")), None)
                if project_id_to_use:
                    schedule_title_for_db = dummy_projects[project_id_to_use]["title"] # 프로젝트 타입이면 프로젝트 제목으로 설정

            dummy_schedules[i].update({
                "projectId": project_id_to_use,
                "schedule_title": schedule_title_for_db, # DB에 저장될 제목
                "schedule_name": data["schedule_name"],
                "schedule": {
                    "startDate": start_dt,
                    "endDate": end_dt
                },
                "writer": writer_id_to_use, # 업데이트된 writer_id_to_use 사용
                "member": data.get("member", ""), # 참여자 필드 유지 (UI에서만 제거)
                "content": data.get("content"),
                "type": data["type"],
                "status": data["status"],
                "update_date": datetime.now(),
                "tasks": data.get("tasks", []) # tasks 필드 유지 (UI에서만 제거)
            })
            found = True
            break
            
    if found:
        return jsonify({"success": True, "message": "일정이 성공적으로 업데이트되었습니다."})
    return jsonify({"success": False, "message": "일정이 존재하지 않습니다."})

@app.route('/timeline/delete_schedule', methods=['POST'])
def delete_schedule():
    data = request.json
    global dummy_schedules
    schedule_id_param_to_delete = data["schedule_id_param"]
    initial_len = len(dummy_schedules)
    dummy_schedules = [s for s in dummy_schedules if s["schedule_id_param"] != schedule_id_param_to_delete]
    if len(dummy_schedules) < initial_len:
        return jsonify({"success": True, "message": "일정이 성공적으로 삭제되었습니다."})
    return jsonify({"success": False, "message": "일정이 존재하지 않습니다."})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
