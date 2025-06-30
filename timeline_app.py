from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from datetime import datetime, timedelta, date, time
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import os

# env 파일 로드
load_dotenv()
id = os.getenv("USER_ID")
pw = os.getenv("USER_PW")
# session_key = os.getenv("SECRET_KEY")
uri = f"mongodb+srv://{id}:{pw}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
client = MongoClient(uri)
db = client['team3']

# 컬렉션 참조
project_collection = db["projects"]
user_collection = db["users"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]
timeline_collection = db["timeline"]

@app.context_processor
def inject_user():
    # 실제 환경에서 사용자 로그인 정보를 세션에서 가져와야함.
    # session["user_id"] = "685df192a2cd54b0683ea346" 
    user_id = session.get("user_id")
    print(f"Current session user_id: {user_id}")
    user = None
    if user_id:
        try:
            user = user_collection.find_one(
                {"_id": ObjectId(user_id)},
                {"name": 1, "position": 1, "department": 1}
            )
        except Exception as e:
            user = None

    # notifications 컬렉션에서 안 읽은 알림 불러오기
    unread_notes = []
    has_notification = False
    if user_id and "notifications" in db.list_collection_names(): 
        try:
            unread_notes = list(db.notifications.find({
                "user_id": ObjectId(user_id),
                "read": False
            }))
            messages = [n["message"] for n in unread_notes]
            has_notification = len(messages) > 0
        except Exception as e:
            messages = []
    else:
        messages = []

    return dict(
        user_info=user,
        notifications=messages,
        has_notification=has_notification
    )

# 일정 타입
TYPE_TAG_CLASS_MAP = {"개인": "personal-schedule-tag", "회사": "company-schedule-tag", "프로젝트": "project-schedule-tag"}

# 일정 타입에 따른 상태 옵션
STATUS_OPTIONS_BY_TYPE = {
    "개인": [{"value": "연차", "text": "연차"}, {"value": "월차", "text": "월차"},
        {"value": "병가", "text": "병가"}, {"value": "출장", "text": "출장"}],
    "회사": [{"value": "사내일정", "text": "사내일정"}],
    "프로젝트": [{"value": "진행중", "text": "진행중"}, {"value": "진행대기", "text": "진행대기"},
        {"value": "지연", "text": "지연"}, {"value": "중단", "text": "중단"}, {"value": "완료", "text": "완료"}]}

# 일정 상태에 따른 태그 클래스
STATUS_TAG_CLASS_MAP = {
    "연차": "vacation-year-tag", "월차": "vacation-month-tag", "병가": "sick-leave-tag", "출장": "travel-tag",
    "사내일정": "company-event-tag",
    "진행중": "status-inprogress-tag", "진행대기": "status-wait-tag", "지연": "status-delayed-tag",
    "중단": "status-stopped-tag", "완료": "status-completed-tag",
}

# 일정 타입 옵션 (드롭다운)
SCHEDULE_TYPE_OPTIONS = [{"value": "전체", "text": "전체 일정"}, {"value": "개인", "text": "개인 일정"},
    {"value": "회사", "text": "회사 일정"}, {"value": "프로젝트", "text": "프로젝트 일정"}]

# 헬퍼 함수
# 사용자 이름으로 user_id (ObjectId) 찾아 반환
def get_user_id_by_name(user_name):
    user = user_collection.find_one({"name": user_name}, {"_id": 1})
    return user["_id"] if user else None

# user_id (ObjectId)로 사용자 이름 찾아 반환
def get_user_name_by_id(user_obj_id):
    try:
        if not isinstance(user_obj_id, ObjectId):
            user_obj_id = ObjectId(user_obj_id)
        user = user_collection.find_one({"_id": user_obj_id}, {"name": 1})
        return user["name"] if user else None
    except Exception as e:
        return None

# user_id 리스트로 사용자 이름 리스트 찾아 반환
def get_user_names_by_ids(user_ids):
    if not user_ids:
        return []
    try:
        valid_ids = []
        for id_val in user_ids:
            if isinstance(id_val, ObjectId):
                valid_ids.append(id_val)
            elif isinstance(id_val, str) and ObjectId.is_valid(id_val):
                valid_ids.append(ObjectId(id_val))
        if not valid_ids:
            return []
        users = user_collection.find({"_id": {"$in": valid_ids}}, {"name": 1})
        return [user["name"] for user in users]
    except Exception as e:
        return []

# 프로젝트 제목으로 project_id (ObjectId) 찾아 반환
def get_project_id_by_title(project_title):
    project = project_collection.find_one({"title": project_title})
    return project["_id"] if project else None

# project_id (ObjectId)로 프로젝트 제목 찾아 반환
def get_project_title_by_id(project_obj_id):
    try:
        if not isinstance(project_obj_id, ObjectId):
            project_obj_id = ObjectId(project_obj_id)
        project = project_collection.find_one({"_id": project_obj_id})
        return project["title"] if project else None
    except Exception as e:
        return None

# 라우팅
@app.route('/timeline')
def timeline():
    user_id = session.get("user_id") # 세션에서 user_id 가져오기 (ObjectId로 변환 필요 시 get_user_name_by_id 사용)
    
    year_param = request.args.get('year')
    month_param = request.args.get('month')
    date_param = request.args.get('date')
    schedule_id_param = request.args.get('schedule_id')
    type_filter_param = request.args.get('type', '전체')
    
    user_names = []
    for user in user_collection.find({}, {"_id": 1, "name": 1, "position": 1, "department": 1}):
        user_data = {"_id": str(user["_id"])}
        if "name" in user and user["name"] is not None:
            user_data["name"] = user["name"]
        else:
            user_data["name"] = "이름 없음"

        user_data["position"] = user.get("position", "")
        user_data["department"] = user.get("department", "")

        user_names.append(user_data)
    
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

    start_of_month = date(current_year, current_month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    calendar_days = []
    first_day_of_week = start_of_month.weekday()
    start_offset = (first_day_of_week + 1) % 7 # 월요일을 0으로 가정하면 (일요일=6) -> (일요일=0)
    start_date = start_of_month - timedelta(days=start_offset)

    for _ in range(35): # 5주 (35일) 표시
        is_current_month = (start_date.month == current_month)
        formatted_date = start_date.strftime('%Y-%m-%d')
        
        start_of_day_dt = datetime.combine(start_date, time.min)
        end_of_day_dt = datetime.combine(start_date, time.max)

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

    daily_schedules_response = get_daily_schedules_api(date_param=selected_date_str, selected_type=type_filter_param).get_json()
    daily_schedules = daily_schedules_response['daily_schedules'] if daily_schedules_response['success'] else []

    selected_schedule_detail = {}
    if schedule_id_param:
        try:
            schedule = timeline_collection.find_one({"_id": ObjectId(schedule_id_param)})
            if schedule:
                selected_schedule_detail["scheduleId"] = str(schedule["_id"])
                selected_schedule_detail["scheduleName"] = schedule.get("title", "") 
                
                if isinstance(schedule.get("start_date"), datetime):
                    selected_schedule_detail["startDate"] = schedule["start_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["startTime"] = schedule["start_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["startDate"] = ""
                    selected_schedule_detail["startTime"] = "09:00"
                
                if isinstance(schedule.get("end_date"), datetime):
                    selected_schedule_detail["endDate"] = schedule["end_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["endTime"] = schedule["end_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["endDate"] = ""
                    selected_schedule_detail["endTime"] = "18:00"

                selected_schedule_detail["content"] = schedule.get("content", "")
                selected_schedule_detail["type"] = schedule.get("type", "")
                selected_schedule_detail["status"] = schedule.get("status", "").strip().replace(" ", "").replace("\u00a0", "")
                
                user_name = get_user_name_by_id(schedule.get("user_id")) 
                selected_schedule_detail["personName"] = user_name if user_name else "-"
                selected_schedule_detail["personId"] = str(schedule.get("user_id")) if schedule.get("user_id") else "None" 
                
                project_title = get_project_title_by_id(schedule.get("project_id")) 
                selected_schedule_detail["projectTitle"] = project_title if project_title else ""
                
                member_ids = schedule.get("member", []) 
                
                members_detailed_info = []
                if member_ids: 
                    member_object_ids = [ObjectId(mid) for mid in member_ids if isinstance(mid, str) and ObjectId.is_valid(mid)]
                    member_object_ids.extend([mid for mid in member_ids if isinstance(mid, ObjectId)])
                    
                    member_object_ids = list(set(member_object_ids))

                    for user in user_collection.find(
                        {"_id": {"$in": member_object_ids}},
                        {"name": 1, "position": 1, "department": 1} 
                    ):
                        members_detailed_info.append({
                            "id": str(user["_id"]),
                            "name": user.get("name", "이름 없음"),
                            "position": user.get("position", "직급 없음"),
                            "department": user.get("department", "부서 없음")
                        })
                selected_schedule_detail["members_detailed_info"] = members_detailed_info
                selected_schedule_detail["memberNames"] = [m["name"] for m in members_detailed_info]
                selected_schedule_detail["memberIds"] = [m["id"] for m in members_detailed_info]

        except Exception as e:
            selected_schedule_detail = {}

    project_titles = [p["title"] for p in project_collection.find({}, {"title": 1})]

    return render_template('timeline.html',
                           current_year=current_year, current_month=current_month, calendar_days=calendar_days,
                           daily_schedules=daily_schedules, selected_date=selected_date_str,
                           selected_schedule_detail=selected_schedule_detail,
                           status_options_by_type=STATUS_OPTIONS_BY_TYPE,
                           project_titles=project_titles, user_names=user_names,
                           grouped_users_by_department=grouped_users_by_department,
                           schedule_type_options=SCHEDULE_TYPE_OPTIONS,
                           selected_type_filter=type_filter_param
                          )

# 일별 일정 필터링
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
            "schedule_id_param": str(schedule["_id"]),
            "name": schedule.get("title", "제목 없음"),
            "status_tag_class": status_tag_class,
            "status_display_text": schedule_status,
            "type": schedule.get("type", "")
        })
    return jsonify({"success": True, "daily_schedules": daily_schedules})

@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session:
        return jsonify({"success": False, "message": "로그인된 사용자만 일정을 추가할 수 있습니다."}), 401 # 추가

    data = request.get_json()
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "필수 필드(제목, 기간, 타입, 상태)가 누락되었습니다."}), 400
    
    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        start_date_dt = datetime.fromisoformat(start_date_iso)
        end_date_dt = datetime.fromisoformat(end_date_iso)
    except ValueError as e:
        return jsonify({"success": False, "message": "유효하지 않은 날짜/시간 형식입니다. (YYYY-MM-DDTHH:MM:SS)"}), 400

    new_schedule = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "user_id": ObjectId(user_id_from_session), # 세션의 user_id를 ObjectId로 변환하여 저장
        "created_at": datetime.now() 
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 리스트로 받음)
    member_ids_json = data.get("member_ids", "[]") 
    members_to_save = []
    print(f"DEBUG: raw member_ids_json from frontend: {member_ids_json}")
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
            return jsonify({"success": False, "message": "프로젝트 일정을 선택했을 경우 프로젝트 제목을 선택해주세요."}), 400
        
        project_id = get_project_id_by_title(project_title)
        if project_id:
            new_schedule["project_id"] = project_id 
        else:
            return jsonify({"success": False, "message": f"프로젝트 '{project_title}'을(를) 찾을 수 없습니다."}), 400
    else:
        new_schedule["project_id"] = None 

    try:
        result = timeline_collection.insert_one(new_schedule) 
        return jsonify({"success": True, "message": "일정이 성공적으로 생성되었습니다."})
    except Exception as e:
        return jsonify({"success": False, "message": f"일정 생성 중 오류 발생: {str(e)}"}), 500

@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session:
        return jsonify({"success": False, "message": "로그인된 사용자만 일정을 수정할 수 있습니다."}), 401 # 추가

    data = request.get_json()

    original_schedule_id_param = data.get("original_schedule_id_param")

    if not original_schedule_id_param:
        return jsonify({"success": False, "message": "수정할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_update = ObjectId(original_schedule_id_param)
    except Exception as e:
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    # 이전에 제거했던 작성자 확인 로직은 다시 넣지 않습니다. (요구사항에 따라 로그인만 확인)
    schedule_to_update = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
    if not schedule_to_update:
        return jsonify({"success": False, "message": "수정할 일정을 찾을 수 없습니다."}), 404
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "필수 필드(제목, 기간, 타입, 상태)가 누락되었습니다."}), 400

    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        # Z 문자가 있을 경우 UTC로 처리하기 위해 +00:00으로 대체
        start_date_dt = datetime.fromisoformat(start_date_iso.replace('Z', '+00:00'))
        end_date_dt = datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
    except ValueError as e:
        return jsonify({"success": False, "message": f"유효하지 않은 날짜/시간 형식입니다: {e}"}), 400

    updated_schedule_data = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "updated_at": datetime.now()
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 리스트로 받음)
    member_ids_json = data.get("member_ids", "[]") 
    members_to_save = []
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
        except json.JSONDecodeError as e:
            pass
    
    updated_schedule_data["member"] = members_to_save

    if updated_schedule_data["type"] == "프로젝트":
        project_title = data.get("project_title")
        if not project_title:
            return jsonify({"success": False, "message": "프로젝트 일정을 선택했을 경우 프로젝트 제목을 선택해주세요."}), 400
        
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
            return jsonify({"success": True, "message": "일정이 성공적으로 수정되었습니다."})
        else:
            found_document = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
            if found_document:
                return jsonify({"success": True, "message": "일정 내용이 변경되지 않았습니다."})
            else:
                return jsonify({"success": False, "message": "일정을 찾을 수 없습니다."}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"일정 수정 중 오류 발생: {str(e)}"}), 500

@app.route('/timeline/delete_schedule', methods=['POST'])
def delete_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session:
        return jsonify({"success": False, "message": "로그인된 사용자만 일정을 삭제할 수 있습니다."}), 401 # 추가

    data = request.get_json()
    schedule_id_param = data.get("schedule_id_param")

    if not schedule_id_param:
        return jsonify({"success": False, "message": "삭제할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_delete = ObjectId(schedule_id_param)
    except Exception as e:
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    schedule_to_delete = timeline_collection.find_one({"_id": schedule_obj_id_to_delete})
    if not schedule_to_delete:
        return jsonify({"success": False, "message": "삭제할 일정을 찾을 수 없습니다."}), 404

    try:
        result = timeline_collection.delete_one({"_id": schedule_obj_id_to_delete}) 
        if result.deleted_count == 1:
            return jsonify({"success": True, "message": "일정이 성공적으로 삭제되었습니다."})
        else:
            return jsonify({"success": False, "message": "일정을 찾을 수 없었습니다."}), 404
    except Exception as e: 
        return jsonify({"success": False, "message": f"일정 삭제 중 오류 발생: {str(e)}"}), 500

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
