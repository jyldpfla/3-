from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from datetime import datetime, timedelta, date, time
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import os

load_dotenv()
mongo_user_id = os.getenv("USER_ID")
mongo_user_pw = os.getenv("USER_PW")
uri = f"mongodb+srv://{mongo_user_id}:{mongo_user_pw}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
client = MongoClient(uri)
db = client['team3']

# MongoDB 컬렉션 참조
project_collection = db["projects"]
user_collection = db["users"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]
timeline_collection = db["timeline"]

@app.context_processor
def inject_user():
    # session["user_id"] = "685df192a2cd54b0683ea346" # 테스트를 위한 임시 사용자 ID
    user_id = session.get("user_id")
    print(f"현재 세션 사용자 ID: {user_id}") # 디버깅용 유지

    user_info = None # 템플릿에 전달할 user_info 객체 초기화
    if user_id:
        try:
            user_obj_id = ObjectId(user_id) # user_id를 ObjectId로 변환 시도
            found_user = user_collection.find_one(
                {"_id": user_obj_id},
                {"name": 1, "position": 1, "department": 1}
            )
            # Jinja2 템플릿에서 쉽게 사용할 수 있도록 ObjectId를 문자열로 변환합니다.
            if found_user:
                user_info = {
                    "_id": str(found_user["_id"]), # ObjectId를 문자열로 변환
                    "name": found_user.get("name"),
                    "position": found_user.get("position"),
                    "department": found_user.get("department")
                }
        except Exception as e:
            print(f"세션 사용자 정보 가져오기 오류: {e}")
            user_info = None

    # 'notifications' 컬렉션에서 읽지 않은 알림 로드
    unread_notes = []
    has_notification = False
    if user_id and "notifications" in db.list_collection_names(): 
        try:
            # 문자열일 수 있으므로 user_id를 ObjectId로 변환하여 쿼리
            unread_notes = list(db.notifications.find({
                "user_id": ObjectId(user_id), 
                "read": False
            }))
            messages = [n["message"] for n in unread_notes]
            has_notification = len(messages) > 0
        except Exception as e:
            print(f"알림 정보 가져오기 오류: {e}")
            messages = []
    else:
        messages = []

    return dict(
        user_info=user_info,
        notifications=messages,
        has_notification=has_notification
    )

# 일정 타입을 CSS 클래스에 매핑
TYPE_TAG_CLASS_MAP = {"개인": "personal-schedule-tag", "회사": "company-schedule-tag", "프로젝트": "project-schedule-tag"}

# 일정 타입에 따른 상태 옵션
STATUS_OPTIONS_BY_TYPE = {
    "개인": [{"value": "연차", "text": "연차"}, {"value": "월차", "text": "월차"},
        {"value": "병가", "text": "병가"}, {"value": "출장", "text": "출장"}],
    "회사": [{"value": "사내일정", "text": "사내일정"}],
    "프로젝트": [{"value": "진행중", "text": "진행중"}, {"value": "진행대기", "text": "진행대기"},
        {"value": "지연", "text": "지연"}, {"value": "중단", "text": "중단"}, {"value": "완료", "text": "완료"}]}

# 일정 상태를 CSS 클래스에 매핑
STATUS_TAG_CLASS_MAP = {
    "연차": "vacation-year-tag", "월차": "vacation-month-tag", "병가": "sick-leave-tag", "출장": "travel-tag",
    "사내일정": "company-event-tag",
    "진행중": "status-inprogress-tag", "진행대기": "status-wait-tag", "지연": "status-delayed-tag",
    "중단": "status-stopped-tag", "완료": "status-completed-tag",
}

# 드롭다운용 일정 타입 필터 옵션
SCHEDULE_TYPE_OPTIONS = [{"value": "전체", "text": "전체 일정"}, {"value": "개인", "text": "개인 일정"},
    {"value": "회사", "text": "회사 일정"}, {"value": "프로젝트", "text": "프로젝트 일정"}]

# user_id(ObjectId)로 사용자 이름 가져오기
def get_user_name_by_id(user_obj_id):
    try:
        if not isinstance(user_obj_id, ObjectId): # 문자열일 경우 ObjectId로 변환 시도
            user_obj_id = ObjectId(user_obj_id)
        user = user_collection.find_one({"_id": user_obj_id}, {"name": 1}) 
        return user["name"] if user else None
    except Exception as e:
        print(f"사용자 ID로 이름 가져오기 오류: {e}")
        return None

# 프로젝트 제목으로 project_id(ObjectId) 가져오기
def get_project_id_by_title(project_title):
    project = project_collection.find_one({"title": project_title}) 
    return project["_id"] if project else None

# project_id(ObjectId)로 프로젝트 제목 가져오기
def get_project_title_by_id(project_obj_id):
    try:
        if not isinstance(project_obj_id, ObjectId): # 문자열일 경우 ObjectId로 변환 시도
            project_obj_id = ObjectId(project_obj_id)
        project = project_collection.find_one({"_id": project_obj_id}) 
        return project["title"] if project else None
    except Exception as e:
        print(f"프로젝트 ID로 제목 가져오기 오류: {e}")
        return None

# 라우팅
@app.route('/timeline')
def timeline():
    year_param = request.args.get('year')
    month_param = request.args.get('month')
    date_param = request.args.get('date')
    schedule_id_param = request.args.get('schedule_id')
    type_filter_param = request.args.get('type', '전체')

    user_names = [] 
    for user in user_collection.find({}, {"_id": 1, "name": 1, "position": 1, "department": 1}):
        user_data = {
            "_id": str(user["_id"]), # ObjectId를 문자열로 변환
            "name": user.get("name", "이름 없음"),
            "position": user.get("position", ""),
            "department": user.get("department", "")
        }
        user_names.append(user_data) 
    
    # 부서별로 그룹화된 사용자 목록
    grouped_users_by_department = {}
    for user_data in user_names: 
        department = user_data.get("department", "기타")
        if department not in grouped_users_by_department:
            grouped_users_by_department[department] = []
        grouped_users_by_department[department].append({
            "id": user_data["_id"],
            "name": user_data["name"],
            "position": user_data["position"]
        })
    
    today = date.today()
    current_year = int(year_param) if year_param else today.year
    current_month = int(month_param) if month_param else today.month

    # 현재 월의 시작 및 종료 날짜 계산
    start_of_month = date(current_year, current_month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    calendar_days = []
    first_day_of_week = start_of_month.weekday()
    start_offset = (first_day_of_week + 1) % 7
    start_date = start_of_month - timedelta(days=start_offset)

    # 캘린더에 표시할 35일(5주) 계산
    for _ in range(35): 
        is_current_month = (start_date.month == current_month)
        formatted_date = start_date.strftime('%Y-%m-%d')
        
        start_of_day_dt = datetime.combine(start_date, time.min)
        end_of_day_dt = datetime.combine(start_date, time.max)

        # 해당 날짜에 일정이 있는지 확인
        schedules_on_day = timeline_collection.count_documents({
            "start_date": {"$lte": end_of_day_dt}, 
            "end_date": {"$gte": start_of_day_dt}  
        }) > 0 

        calendar_days.append({
            'date': formatted_date,
            'day': start_date.day,
            'is_today': (start_date == today),
            'is_current_month': is_current_month,
            'has_schedule': schedules_on_day
        })
        start_date += timedelta(days=1)

    selected_date_obj = None
    if date_param:
        selected_date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
    else:
        selected_date_obj = today
    
    selected_date_str = selected_date_obj.strftime('%Y-%m-%d')

    # API 함수를 통해 일일 일정 가져오기
    daily_schedules_response = get_daily_schedules_api(date_param=selected_date_str, selected_type=type_filter_param).get_json()
    daily_schedules = daily_schedules_response['daily_schedules'] if daily_schedules_response and daily_schedules_response.get('success') else []

    selected_schedule_detail = {} # 선택된 일정의 상세 정보를 저장할 사전
    if schedule_id_param: # URL에 schedule_id가 있는 경우
        try:
            schedule = timeline_collection.find_one({"_id": ObjectId(schedule_id_param)})
            if schedule:
                selected_schedule_detail["scheduleId"] = str(schedule["_id"])
                selected_schedule_detail["scheduleName"] = schedule.get("title", "") 
                
                # 시작 날짜/시간 형식 지정
                if isinstance(schedule.get("start_date"), datetime):
                    selected_schedule_detail["startDate"] = schedule["start_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["startTime"] = schedule["start_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["startDate"] = ""
                    selected_schedule_detail["startTime"] = "09:00"
                
                # 종료 날짜/시간 형식 지정
                if isinstance(schedule.get("end_date"), datetime):
                    selected_schedule_detail["endDate"] = schedule["end_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["endTime"] = schedule["end_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["endDate"] = ""
                    selected_schedule_detail["endTime"] = "18:00"

                selected_schedule_detail["content"] = schedule.get("content", "")
                selected_schedule_detail["type"] = schedule.get("type", "")
                # HTML 클래스 일치를 위해 상태 값에서 공백 제거
                selected_schedule_detail["status"] = schedule.get("status", "").strip().replace(" ", "").replace("\u00a0", "")
                
                # 'user_id' 필드를 통해 작성자 이름 및 ID를 가져와 'personName' 및 'personId'로 추가
                author_user_id = schedule.get("user_id")
                user_name = get_user_name_by_id(author_user_id) 
                selected_schedule_detail["personName"] = user_name if user_name else "-"
                selected_schedule_detail["personId"] = str(author_user_id) if author_user_id else "None" # JS용 작성자 ID (문자열)
                
                # 프로젝트 제목 가져오기
                project_title = get_project_title_by_id(schedule.get("project_id")) 
                selected_schedule_detail["projectTitle"] = project_title if project_title else ""
                
                # 멤버 목록 가져오기 및 상세 정보 구성
                member_ids = schedule.get("member", []) 
                members_detailed_info = []
                if member_ids: 
                    # 문자열 ID와 ObjectId를 모두 ObjectId로 변환한 다음 중복 제거
                    member_object_ids = [ObjectId(mid) for mid in member_ids if isinstance(mid, str) and ObjectId.is_valid(mid)]
                    member_object_ids.extend([mid for mid in member_ids if isinstance(mid, ObjectId)])
                    member_object_ids = list(set(member_object_ids))

                    for user_doc in user_collection.find(
                        {"_id": {"$in": member_object_ids}},
                        {"name": 1, "position": 1, "department": 1, "_id": 1} 
                    ):
                        members_detailed_info.append({
                            "id": str(user_doc["_id"]), # ObjectId를 문자열로 변환
                            "name": user_doc.get("name", "이름 없음"),
                            "position": user_doc.get("position", "직급 없음"),
                            "department": user_doc.get("department", "부서 없음")
                        })
                selected_schedule_detail["members_detailed_info"] = members_detailed_info
                selected_schedule_detail["memberNames"] = [m["name"] for m in members_detailed_info]
                selected_schedule_detail["memberIds"] = [m["id"] for m in members_detailed_info] # 문자열 ID 목록

        except Exception as e:
            print(f"선택된 일정 상세 정보 로드 오류: {e}")
            selected_schedule_detail = {} # 오류 발생 시 상세 정보 초기화

    project_titles = [p["title"] for p in project_collection.find({}, {"title": 1})] # 모든 프로젝트 제목 가져오기

    return render_template('timeline.html',
                           current_year=current_year, current_month=current_month, calendar_days=calendar_days,
                           daily_schedules=daily_schedules, selected_date=selected_date_str,
                           selected_schedule_detail=selected_schedule_detail,
                           status_options_by_type=STATUS_OPTIONS_BY_TYPE,
                           project_titles=project_titles, 
                           user_names=user_names,
                           grouped_users_by_department=grouped_users_by_department,
                           schedule_type_options=SCHEDULE_TYPE_OPTIONS,
                           selected_type_filter=type_filter_param
                          )

# 일일 일정 필터링 및 검색
@app.route('/timeline/get_daily_schedules', methods=['GET'])
def get_daily_schedules_api(date_param=None, selected_type='전체'):
    if date_param is None:
        date_param = request.args.get('date')
        selected_type = request.args.get('type', '전체')

    if not date_param:
        return jsonify({"success": False, "message": "날짜 정보가 필요합니다."}), 400

    try:
        selected_date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"success": False, "message": "유효하지 않은 날짜 형식입니다."}), 400

    selected_start_of_day_dt = datetime.combine(selected_date_obj, time.min)
    selected_end_of_day_dt = datetime.combine(selected_date_obj, time.max)

    query = {
        "start_date": {"$lte": selected_end_of_day_dt},
        "end_date": {"$gte": selected_start_of_day_dt}
    }

    if selected_type != '전체':
        query["type"] = selected_type

    schedules_cursor = timeline_collection.find(query).sort("start_date", 1)

    daily_schedules = []
    for schedule in schedules_cursor:
        schedule_status = schedule.get("status", "").strip().replace(" ", "").replace("\u00a0", "")
        status_tag_class = STATUS_TAG_CLASS_MAP.get(schedule_status, "default-status-tag")

        daily_schedules.append({
            "schedule_id_param": str(schedule["_id"]), # ObjectId를 문자열로 변환
            "name": schedule.get("title", "제목 없음"),
            "status_tag_class": status_tag_class,
            "status_display_text": schedule_status,
            "type": schedule.get("type", "")
        })
    return jsonify({"success": True, "daily_schedules": daily_schedules})

# 일정 생성
@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session: # 로그인 상태 확인
        return jsonify({"success": False, "message": "로그인된 사용자만 일정을 추가할 수 있습니다."}), 401
    
    data = request.get_json()
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "필수 필드(제목, 기간, 타입, 상태)가 누락되었습니다."}), 400

    # 일정 작성자는 세션에 로그인된 사용자 ID로 자동 설정
    author_id_to_save = user_id_from_session
    if not author_id_to_save:
        return jsonify({"success": False, "message": "로그인된 사용자 정보가 없습니다. 다시 로그인해 주세요."}), 401
    
    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        start_date_dt = datetime.fromisoformat(start_date_iso)
        end_date_dt = datetime.fromisoformat(end_date_iso)
    except ValueError as e:
        print(f"날짜/시간 형식 오류: {e}")
        return jsonify({"success": False, "message": "유효하지 않은 날짜/시간 형식입니다. (YYYY-MM-DDTHH:MM:SS)"}), 400

    new_schedule = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "user_id": ObjectId(author_id_to_save), # 로그인된 사용자의 ObjectId 저장
        "created_at": datetime.now() 
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 목록으로 수신)
    member_ids_json = data.get("member_ids", "[]") # 'member_ids' 필드로 변경
    members_to_save = []
    print(f"DEBUG: 프론트엔드에서 받은 원시 member_ids_json: {member_ids_json}")
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
        except json.JSONDecodeError as e:
            pass
    
    new_schedule["member"] = members_to_save

    if new_schedule["type"] == "프로젝트":
        project_title = data.get("project_title")
        if not project_title:
            return jsonify({"success": False, "message": "프로젝트 일정을 선택한 경우 프로젝트 제목을 선택해 주세요."}), 400
        
        project_id = get_project_id_by_title(project_title)
        if project_id:
            new_schedule["project_id"] = project_id 
        else:
            return jsonify({"success": False, "message": f"프로젝트 '{project_title}'을(를) 찾을 수 없습니다."}), 400
    else:
        new_schedule["project_id"] = None # 프로젝트 타입이 아니면 project_id는 None

    try:
        result = timeline_collection.insert_one(new_schedule) 
        return jsonify({"success": True, "message": "일정이 성공적으로 생성되었습니다."})
    except Exception as e:
        print(f"일정 생성 오류: {e}")
        return jsonify({"success": False, "message": f"일정 생성 오류: {str(e)}"}), 500

# 일정 업데이트
@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session: # 로그인 상태 확인
        return jsonify({"success": False, "message": "로그인된 사용자만 일정을 업데이트할 수 있습니다."}), 401 

    data = request.get_json()

    original_schedule_id_param = data.get("original_schedule_id_param")

    if not original_schedule_id_param:
        return jsonify({"success": False, "message": "업데이트할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_update = ObjectId(original_schedule_id_param)
    except Exception as e:
        print(f"유효하지 않은 일정 ID 형식: {e}")
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    schedule_to_update = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
    if not schedule_to_update:
        return jsonify({"success": False, "message": "업데이트할 일정을 찾을 수 없습니다."}), 404

    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "필수 필드(제목, 기간, 타입, 상태)가 누락되었습니다."}), 400

    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        start_date_dt = datetime.fromisoformat(start_date_iso.replace('Z', '+00:00'))
        end_date_dt = datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
    except ValueError as e:
        print(f"날짜/시간 형식 오류: {e}")
        return jsonify({"success": False, "message": f"유효하지 않은 날짜/시간 형식입니다: {e}"}), 500

    updated_schedule_data = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "updated_at": datetime.now()
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 목록으로 수신)
    member_ids_json = data.get("member_ids", "[]") # 'member_ids' 필드로 변경
    members_to_save = []
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
        except json.JSONDecodeError as e:
            print(f"JSON 디코딩 오류: {e}")
            pass
    
    updated_schedule_data["member"] = members_to_save

    if updated_schedule_data["type"] == "프로젝트":
        project_title = data.get("project_title")
        if not project_title:
            return jsonify({"success": False, "message": "프로젝트 일정을 선택한 경우 프로젝트 제목을 선택해 주세요."}), 400
        
        project_id = get_project_id_by_title(project_title)
        if project_id:
            updated_schedule_data["project_id"] = project_id 
        else:
            return jsonify({"success": False, "message": f"프로젝트 '{project_title}'을(를) 찾을 수 없습니다."}), 400
    else:
        updated_schedule_data["project_id"] = None 

    try:
        result = timeline_collection.update_one(
            {"_id": schedule_obj_id_to_update},
            {"$set": updated_schedule_data}
        )
        if result.modified_count == 1:
            return jsonify({"success": True, "message": "일정이 성공적으로 업데이트되었습니다."})
        else:
            found_document = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
            if found_document:
                return jsonify({"success": True, "message": "일정에 변경 사항이 없습니다."})
            else:
                return jsonify({"success": False, "message": "일정을 찾을 수 없습니다."}), 404
    except Exception as e:
        print(f"일정 업데이트 오류: {e}")
        return jsonify({"success": False, "message": f"일정 업데이트 오류: {str(e)}"}), 500

# 일정 삭제
@app.route('/timeline/delete_schedule', methods=['POST'])
def delete_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session: # 로그인 상태 확인
        return jsonify({"success": False, "message": "로그인된 사용자만 일정을 삭제할 수 있습니다."}), 401 
        
    data = request.get_json()
    schedule_id_param = data.get("schedule_id_param")

    if not schedule_id_param:
        return jsonify({"success": False, "message": "삭제할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_delete = ObjectId(schedule_id_param)
    except Exception as e:
        print(f"유효하지 않은 일정 ID 형식: {e}")
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    try:
        result = timeline_collection.delete_one({"_id": schedule_obj_id_to_delete}) 
        if result.deleted_count == 1:
            return jsonify({"success": True, "message": "일정이 성공적으로 삭제되었습니다."})
        else:
            return jsonify({"success": False, "message": "일정을 찾을 수 없습니다."}), 404
    except Exception as e: 
        print(f"일정 삭제 오류: {e}")
        return jsonify({"success": False, "message": f"일정 삭제 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
