import os
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from datetime import timedelta
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") 

# MongoDB 연결 설정
uri = "mongodb+srv://team3_member:fwA36oY8zSlNez8w@team3.fxbwcnh.mongodb.net/"
client = MongoClient(uri)
db = client['team3']

# 컬렉션 참조
timeline_collection = db["timeline"] 
users_collection = db["users"] 
projects_collection = db["projects"] 

# 일정 타입에 따른 상태 옵션
STATUS_OPTIONS_BY_TYPE = {
    "개인": [
        {"value": "연차", "text": "연차"},
        {"value": "월차", "text": "월차"},
        {"value": "병가", "text": "병가"},
        {"value": "출장", "text": "출장"}
    ],
    "회사": [
        {"value": "사내일정", "text": "사내일정"}
    ],
    "프로젝트": [
        {"value": "진행중", "text": "진행중"},
        {"value": "진행대기", "text": "진행대기"},
        {"value": "지연", "text": "지연"},
        {"value": "중단", "text": "중단"},
        {"value": "완료", "text": "완료"}
    ]
}

# 태그 클래스 매핑
TAG_CLASS_MAP = {
    "개인": "personal-tag",
    "회사": "company-tag",
    "프로젝트": "project-tag",
    "연차": "vacation-year-tag",
    "월차": "vacation-month-tag",
    "병가": "sick-leave-tag",
    "출장": "travel-tag",
    "사내일정": "company-event-tag",
    "진행중": "status-inprogress-tag",
    "진행대기": "status-wait-tag",
    "지연": "status-delayed-tag",
    "중단": "status-stopped-tag",
    "완료": "status-completed-tag",
}

# 헬퍼 함수
# 사용자 이름으로 user_id (ObjectId) 찾아 반환
def get_user_id_by_name(user_name):
    user = users_collection.find_one({"name": user_name}, {"_id": 1})
    return user["_id"] if user else None

# user_id (ObjectId)로 사용자 이름 찾아 반환
def get_user_name_by_id(user_obj_id):
    try:
        if not isinstance(user_obj_id, ObjectId):
            user_obj_id = ObjectId(user_obj_id)
        user = users_collection.find_one({"_id": user_obj_id}, {"name": 1})
        return user["name"] if user else None
    except Exception as e:
        print(f"Error converting user ID {user_obj_id} to name: {e}")
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

        users = users_collection.find({"_id": {"$in": valid_ids}}, {"name": 1})
        return [user["name"] for user in users]
    except Exception as e:
        print(f"Error converting user IDs to names: {e}")
        return []

# 프로젝트 제목으로 project_id (ObjectId) 찾아 반환
def get_project_id_by_title(project_title):
    project = projects_collection.find_one({"title": project_title})
    return project["_id"] if project else None

# project_id (ObjectId)로 프로젝트 제목 찾아 반환
def get_project_title_by_id(project_obj_id):
    try:
        if not isinstance(project_obj_id, ObjectId):
            project_obj_id = ObjectId(project_obj_id)
        project = projects_collection.find_one({"_id": project_obj_id})
        return project["title"] if project else None
    except Exception as e:
        print(f"Error converting project ID {project_obj_id} to title: {e}")
        return None

@app.context_processor
def inject_user():
    # 실제 환경에서는 사용자 로그인 정보를 세션에서 가져와야 합니다.
    session["user_id"] = "685df192a2cd54b0683ea346" 
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = users_collection.find_one(
                {"_id": ObjectId(user_id)},
                {"name": 1, "position": 1, "department": 1}
            )
        except Exception as e:
            print(f"Error fetching user info for ID {user_id}: {e}")
            user = None

    # db.notifications 컬렉션에서 안 읽은 알림 불러오기
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
            print(f"Error fetching notifications for user {user_id}: {e}")
            messages = []
    else:
        messages = []

    return dict(
        user_info=user,
        notifications=messages,
        has_notification=has_notification
    )

# 라우팅
@app.route('/timeline')
def timeline():
    user_id = session.get("user_id") # 세션에서 user_id 가져오기 (ObjectId로 변환 필요 시 get_user_name_by_id 사용)
    
    year_param = request.args.get('year')
    month_param = request.args.get('month')
    date_param = request.args.get('date')
    schedule_id_param = request.args.get('schedule_id')
    
    user_names = []
    for user in users_collection.find({}, {"_id": 1, "name": 1, "position": 1, "department": 1}):
        user_data = {"_id": str(user["_id"])}
        if "name" in user and user["name"] is not None:
            user_data["name"] = user["name"]
        else:
            print(f"WARN: User document with _id {user.get('_id', 'UNKNOWN_ID')} is missing or has a None 'name' field.")
            user_data["name"] = "이름 없음"

        user_data["position"] = user.get("position", "") # position 필드 추가
        user_data["department"] = user.get("department", "") # department 필드 추가

        user_names.append(user_data)
    
    today = datetime.date.today()
    current_year = int(year_param) if year_param else today.year
    current_month = int(month_param) if month_param else today.month

    start_of_month = datetime.date(current_year, current_month, 1)
    end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    
    calendar_days = []
    first_day_of_week = start_of_month.weekday()
    start_offset = (first_day_of_week + 1) % 7 # 월요일을 0으로 가정하면 (일요일=6) -> (일요일=0)
    start_date = start_of_month - datetime.timedelta(days=start_offset)

    for _ in range(35): # 5주 (35일) 표시
        is_current_month = (start_date.month == current_month)
        formatted_date = start_date.strftime('%Y-%m-%d')
        
        start_of_day_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_of_day_dt = datetime.datetime.combine(start_date, datetime.time.max)

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
        start_date += datetime.timedelta(days=1)

    selected_date_obj = None
    if date_param:
        selected_date_obj = datetime.datetime.strptime(date_param, '%Y-%m-%d').date()
    else:
        selected_date_obj = today
    
    selected_date_str = selected_date_obj.strftime('%Y-%m-%d')

    daily_schedules = []
    selected_start_of_day_dt = datetime.datetime.combine(selected_date_obj, datetime.time.min)
    selected_end_of_day_dt = datetime.datetime.combine(selected_date_obj, datetime.time.max)

    schedules_cursor = timeline_collection.find({
        "start_date": {"$lte": selected_end_of_day_dt}, 
        "end_date": {"$gte": selected_start_of_day_dt}  
    }).sort("start_date", 1)

    for schedule in schedules_cursor:
        schedule_type = schedule.get("type", "")
        schedule_status = schedule.get("status", "")
        
        tag_class = TAG_CLASS_MAP.get(schedule_type, "default-tag") # 기본 태그 클래스
        
        # 일정 타입에 따라 태그 클래스 오버라이드
        if schedule_type == "개인":
            tag_class = TAG_CLASS_MAP.get(schedule_status, "personal-tag")
        elif schedule_type == "프로젝트":
            tag_class = TAG_CLASS_MAP.get(schedule_status, "project-tag")
        elif schedule_type == "회사":
            tag_class = TAG_CLASS_MAP.get(schedule_status, "company-tag")

        daily_schedules.append({
            "schedule_id_param": str(schedule["_id"]), 
            "name": schedule.get("title", "제목 없음"), 
            "tag_class": tag_class 
        })

    selected_schedule_detail = {}
    if schedule_id_param:
        try:
            schedule = timeline_collection.find_one({"_id": ObjectId(schedule_id_param)})
            if schedule:
                selected_schedule_detail["scheduleId"] = str(schedule["_id"])
                selected_schedule_detail["scheduleName"] = schedule.get("title", "") 
                
                if isinstance(schedule.get("start_date"), datetime.datetime):
                    selected_schedule_detail["startDate"] = schedule["start_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["startTime"] = schedule["start_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["startDate"] = ""
                    selected_schedule_detail["startTime"] = "09:00"
                
                if isinstance(schedule.get("end_date"), datetime.datetime):
                    selected_schedule_detail["endDate"] = schedule["end_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["endTime"] = schedule["end_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["endDate"] = ""
                    selected_schedule_detail["endTime"] = "18:00"

                selected_schedule_detail["content"] = schedule.get("content", "")
                selected_schedule_detail["type"] = schedule.get("type", "")
                selected_schedule_detail["status"] = schedule.get("status", "") 
                
                # 작성자 이름 가져오기
                user_name = get_user_name_by_id(schedule.get("user_id")) 
                selected_schedule_detail["personName"] = user_name if user_name else "-" # 작성자 이름 없으면 "-"
                
                # 프로젝트 제목 가져오기
                project_title = get_project_title_by_id(schedule.get("project_id")) 
                selected_schedule_detail["projectTitle"] = project_title if project_title else ""
                
                # 참여자 ID 리스트 가져오기
                member_ids = schedule.get("member", []) 
                
                members_detailed_info = []
                if member_ids: 
                    member_object_ids = [ObjectId(mid) for mid in member_ids if isinstance(mid, str) and ObjectId.is_valid(mid)]
                    member_object_ids.extend([mid for mid in member_ids if isinstance(mid, ObjectId)])
                    
                    # 중복 방지를 위해 set으로 변환 후 다시 list로
                    member_object_ids = list(set(member_object_ids))

                    # users_collection에서 이름, 직급, 부서 필드를 모두 가져옴
                    for user in users_collection.find(
                        {"_id": {"$in": member_object_ids}},
                        {"name": 1, "position": 1, "department": 1} 
                    ):
                        members_detailed_info.append({
                            "id": str(user["_id"]),
                            "name": user.get("name", "이름 없음"),
                            "position": user.get("position", "직급 없음"),
                            "department": user.get("department", "부서 없음")
                        })
                
                selected_schedule_detail["members_detailed_info"] = members_detailed_info # 새로운 필드 추가
                
                # 기존 memberNames, memberIds도 필요하다면 유지 (JS에서 활용할 수 있음)
                selected_schedule_detail["memberNames"] = [m["name"] for m in members_detailed_info] #
                selected_schedule_detail["memberIds"] = [m["id"] for m in members_detailed_info] #

            else:
                print(f"DEBUG: No schedule found for ID: {schedule_id_param}")
        except Exception as e:
            print(f"ERROR: Failed to fetch schedule detail for ID {schedule_id_param}: {e}")
            selected_schedule_detail = {}

    project_titles = [p["title"] for p in projects_collection.find({}, {"title": 1})]

    return render_template('timeline.html',
                            current_year=current_year,
                            current_month=current_month,
                            calendar_days=calendar_days,
                            daily_schedules=daily_schedules,
                            selected_date=selected_date_str,
                            selected_schedule_detail=selected_schedule_detail, 
                            status_options_by_type=STATUS_OPTIONS_BY_TYPE, 
                            project_titles=project_titles,
                            user_names=user_names) # 모든 사용자 이름 전달

@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    data = request.get_json()
    print("\n--- create_schedule API 호출됨 ---")
    print("수신 데이터 (create_schedule):", data) 
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        print("ERROR: 필수 필드 누락.")
        return jsonify({"success": False, "message": "필수 필드(일정 이름, 기간, 타입, 상태)가 누락되었습니다."}), 400

    user_id_from_session = session.get("user_id")
    if not user_id_from_session:
        print("ERROR: 세션 사용자 ID 없음.")
        return jsonify({"success": False, "message": "로그인된 사용자 정보가 없습니다. 다시 로그인 해주세요."}), 401
    
    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        start_date_dt = datetime.datetime.fromisoformat(start_date_iso)
        end_date_dt = datetime.datetime.fromisoformat(end_date_iso)
    except ValueError as e:
        print(f"ERROR: 유효하지 않은 날짜/시간 형식: {e}")
        return jsonify({"success": False, "message": "유효하지 않은 날짜/시간 형식입니다. (YYYY-MM-DDTHH:MM:SS)"}), 400

    new_schedule = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "user_id": ObjectId(user_id_from_session), # 세션의 user_id를 ObjectId로 변환하여 저장
        "created_at": datetime.datetime.now() 
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 리스트로 받음)
    member_ids_json = data.get("member_ids", "[]") # 'member_ids' 필드로 변경
    members_to_save = []
    print(f"DEBUG: raw member_ids_json from frontend: {member_ids_json}")
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            print(f"DEBUG: parsed_member_ids (after json.loads): {parsed_member_ids}, type: {type(parsed_member_ids)}")
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    print(f"DEBUG: processing member_id_str: {member_id_str}")
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
                        print(f"DEBUG: added valid ObjectId: {member_id_str}")
                    else:
                        print(f"WARN: Invalid ObjectId string received for member (skipped): {member_id_str}")
            else:
                print(f"WARN: member_ids is not a list after parsing: {parsed_member_ids}")
        except json.JSONDecodeError as e:
            print(f"ERROR: JSONDecodeError for member_ids: {e} - Raw: {member_ids_json}")
    
    new_schedule["member"] = members_to_save
    print(f"DEBUG: Final members_to_save before DB insert: {new_schedule['member']}")

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
        print(f"INFO: 일정 생성 성공. Inserted ID: {result.inserted_id}")
        return jsonify({"success": True, "message": "일정이 성공적으로 생성되었습니다."})
    except Exception as e:
        print(f"ERROR: 일정 생성 중 오류 발생: {str(e)}")
        return jsonify({"success": False, "message": f"일정 생성 중 오류 발생: {str(e)}"}), 500

@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    data = request.get_json()
    print("\n--- update_schedule API 호출됨 ---")
    print("수신 데이터 (update_schedule):", data) 

    original_schedule_id_param = data.get("original_schedule_id_param")

    if not original_schedule_id_param:
        print("ERROR: 수정할 일정 ID 누락.")
        return jsonify({"success": False, "message": "수정할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_update = ObjectId(original_schedule_id_param)
    except Exception as e:
        print(f"ERROR: 유효하지 않은 일정 ID 형식: {e}")
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    user_id_from_session = session.get("user_id")
    if not user_id_from_session:
        print("ERROR: 세션 사용자 ID 없음.")
        return jsonify({"success": False, "message": "로그인된 사용자 정보가 없습니다. 다시 로그인 해주세요."}), 401
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        print("ERROR: 필수 필드 누락.")
        return jsonify({"success": False, "message": "필수 필드(일정 이름, 기간, 타입, 상태)가 누락되었습니다."}), 400

    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        # Z 문자가 있을 경우 UTC로 처리하기 위해 +00:00으로 대체
        start_date_dt = datetime.datetime.fromisoformat(start_date_iso.replace('Z', '+00:00'))
        end_date_dt = datetime.datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
    except ValueError as e:
        print(f"ERROR: 유효하지 않은 날짜/시간 형식: {e}")
        return jsonify({"success": False, "message": f"유효하지 않은 날짜/시간 형식입니다: {e}"}), 400

    updated_schedule_data = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "updated_at": datetime.datetime.now()
    }

    # member_ids 처리 (프론트엔드에서 ObjectId 문자열 리스트로 받음)
    member_ids_json = data.get("member_ids", "[]") # 'member_ids' 필드로 변경
    members_to_save = []
    print(f"DEBUG: raw member_ids_json from frontend: {member_ids_json}")
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            print(f"DEBUG: parsed_member_ids (after json.loads): {parsed_member_ids}, type: {type(parsed_member_ids)}")
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    print(f"DEBUG: processing member_id_str: {member_id_str}")
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
                        print(f"DEBUG: added valid ObjectId: {member_id_str}")
                    else:
                        print(f"WARN: Invalid ObjectId string received for member (skipped): {member_id_str}")
            else:
                print(f"WARN: member_ids is not a list after parsing: {parsed_member_ids}")
        except json.JSONDecodeError as e:
            print(f"ERROR: JSONDecodeError for member_ids: {e} - Raw: {member_ids_json}")
    
    updated_schedule_data["member"] = members_to_save
    print(f"DEBUG: Final members_to_save before DB update: {updated_schedule_data['member']}")

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
            print("INFO: 일정 수정 성공.")
            return jsonify({"success": True, "message": "일정이 성공적으로 수정되었습니다."})
        else:
            found_document = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
            if found_document:
                print("INFO: 일정 내용 변경 없음.")
                return jsonify({"success": True, "message": "일정 내용이 변경되지 않았습니다."})
            else:
                print("ERROR: 수정할 일정을 찾을 수 없음.")
                return jsonify({"success": False, "message": "일정을 찾을 수 없습니다."}), 404
    except Exception as e:
        print(f"ERROR update_schedule: {e}")
        return jsonify({"success": False, "message": f"일정 수정 중 오류 발생: {str(e)}"}), 500

@app.route('/timeline/delete_schedule', methods=['POST'])
def delete_schedule():
    data = request.get_json()
    schedule_id_param = data.get("schedule_id_param")

    if not schedule_id_param:
        return jsonify({"success": False, "message": "삭제할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_delete = ObjectId(schedule_id_param)
    except Exception as e:
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    try:
        result = timeline_collection.delete_one({"_id": schedule_obj_id_to_delete}) 
        if result.deleted_count == 1:
            return jsonify({"success": True, "message": "일정이 성공적으로 삭제되었습니다."})
        else:
            return jsonify({"success": False, "message": "일정을 찾을 수 없었습니다."}), 404
    except Exception as e:
        print(f"ERROR delete_schedule: {e}") 
        return jsonify({"success": False, "message": f"일정 삭제 중 오류 발생: {str(e)}"}), 500

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
