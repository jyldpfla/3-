import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from datetime import timedelta
import json # json 모듈 추가

app = Flask(__name__)

# MongoDB 연결 설정
uri = "mongodb+srv://team3_member:fwA36oY8zSlNez8w@team3.fxbwcnh.mongodb.net/"
client = MongoClient(uri)
db = client['team3'] # 'team3' 데이터베이스 사용

# 컬렉션 참조
timeline_collection = db["timeline"] 
users_collection = db["users"] 
projects_collection = db["projects"] 

# 일정 타입에 따른 상태 옵션 (수정됨: 요청에 따라 재구성)
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
        {"value": "지연", "text": "지연"},
        {"value": "중단", "text": "중단"},
        {"value": "완료", "text": "완료"}
    ]
}

# 태그 클래스 매핑 (프론트엔드에서 사용될 수 있도록 추가)
TAG_CLASS_MAP = {
    "개인": "personal-tag",
    "회사": "company-tag",
    "프로젝트": "project-tag",
    "연차": "vacation-tag",
    "월차": "vacation-tag",
    "병가": "sick-leave-tag",
    "출장": "travel-tag",
    "사내일정": "company-event-tag",
    "진행중": "status-inprogress-tag",
    "지연": "status-delayed-tag",
    "중단": "status-stopped-tag",
    "완료": "status-completed-tag",
}

# --- 헬퍼 함수 (이전과 동일하게 유지) ---
def get_user_id_by_name(user_name):
    """사용자 이름으로 user_id (ObjectId)를 찾아 반환합니다."""
    user = users_collection.find_one({"name": user_name}, {"_id": 1})
    return user["_id"] if user else None

def get_user_name_by_id(user_obj_id):
    """user_id (ObjectId)로 사용자 이름을 찾아 반환합니다."""
    try:
        if not isinstance(user_obj_id, ObjectId):
            user_obj_id = ObjectId(user_obj_id)
        user = users_collection.find_one({"_id": user_obj_id}, {"name": 1})
        return user["name"] if user else None
    except Exception as e:
        print(f"Error converting user ID {user_obj_id} to name: {e}")
        return None

def get_user_ids_by_names(user_names):
    """사용자 이름 리스트로 user_id (ObjectId) 리스트를 찾아 반환합니다."""
    if not user_names:
        return []
    
    # 공백 제거 및 유효한 이름만 필터링
    unique_user_names = [name.strip() for name in user_names if name.strip()]
    if not unique_user_names: return []

    # 이름으로 users 컬렉션에서 _id를 찾음
    users = users_collection.find({"name": {"$in": unique_user_names}}, {"_id": 1, "name": 1})
    
    member_ids = [user["_id"] for user in users]
    return member_ids

def get_user_names_by_ids(user_ids):
    """user_id 리스트로 사용자 이름 리스트를 찾아 반환합니다."""
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

def get_project_id_by_title(project_title):
    """프로젝트 제목으로 project_id (ObjectId)를 찾아 반환합니다."""
    project = projects_collection.find_one({"title": project_title})
    return project["_id"] if project else None

def get_project_title_by_id(project_obj_id):
    """project_id (ObjectId)로 프로젝트 제목을 찾아 반환합니다."""
    try:
        if not isinstance(project_obj_id, ObjectId):
            project_obj_id = ObjectId(project_obj_id)
        project = projects_collection.find_one({"_id": project_obj_id})
        return project["title"] if project else None
    except Exception as e:
        print(f"Error converting project ID {project_obj_id} to title: {e}")
        return None

# --- 라우팅 ---

@app.route('/timeline')
def timeline():
    year_param = request.args.get('year')
    month_param = request.args.get('month')
    date_param = request.args.get('date')
    schedule_id_param = request.args.get('schedule_id') # timeline._id 값

    today = datetime.date.today()
    current_year = int(year_param) if year_param else today.year
    current_month = int(month_param) if month_param else today.month

    start_of_month = datetime.date(current_year, current_month, 1)
    end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    
    calendar_days = []
    first_day_of_week = start_of_month.weekday() # 월요일=0, 일요일=6
    start_offset = (first_day_of_week + 1) % 7 # 일요일(0)을 0으로, 월요일(1)을 1으로...
    start_date = start_of_month - datetime.timedelta(days=start_offset)

    # 캘린더를 항상 6주로 유지 (42일)
    for _ in range(42): # 6주 * 7일 = 42일
        is_current_month = (start_date.month == current_month)
        formatted_date = start_date.strftime('%Y-%m-%d')
        
        # 해당 날짜의 시작과 끝 datetime 객체
        start_of_day_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_of_day_dt = datetime.datetime.combine(start_date, datetime.time.max)

        # 해당 날짜에 포함되는 일정이 있는지 확인 (timeline_collection 사용)
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
    # 선택된 날짜에 포함되는 모든 일정 조회 (timeline_collection 사용)
    selected_start_of_day_dt = datetime.datetime.combine(selected_date_obj, datetime.time.min)
    selected_end_of_day_dt = datetime.datetime.combine(selected_date_obj, datetime.time.max)

    schedules_cursor = timeline_collection.find({
        "start_date": {"$lte": selected_end_of_day_dt}, 
        "end_date": {"$gte": selected_start_of_day_dt}  
    }).sort("start_date", 1) # 시작 시간 기준으로 정렬

    for schedule in schedules_cursor:
        # 태그 클래스 결정 로직 (타입과 상태 모두 고려)
        schedule_type = schedule.get("type", "")
        schedule_status = schedule.get("status", "")
        
        tag_class = TAG_CLASS_MAP.get(schedule_type, "default-tag") # 우선 타입에 따른 태그
        
        # 개인 일정의 경우 상태에 따라 더 구체적인 태그 적용
        if schedule_type == "개인":
            tag_class = TAG_CLASS_MAP.get(schedule_status, "personal-tag")
        # 프로젝트 일정의 경우 상태에 따라 더 구체적인 태그 적용 (필요 시)
        elif schedule_type == "프로젝트":
            tag_class = TAG_CLASS_MAP.get(schedule_status, "project-tag")
        # 회사 일정의 경우 상태에 따라 더 구체적인 태그 적용 (필요 시)
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
                
                # datetime 객체에서 날짜와 시간을 분리하여 전달
                if isinstance(schedule.get("start_date"), datetime.datetime):
                    selected_schedule_detail["startDate"] = schedule["start_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["startTime"] = schedule["start_date"].strftime('%H:%M')
                else: # 예외 처리: datetime 객체가 아닌 경우
                    selected_schedule_detail["startDate"] = ""
                    selected_schedule_detail["startTime"] = "09:00" # 기본 시간
                
                if isinstance(schedule.get("end_date"), datetime.datetime):
                    selected_schedule_detail["endDate"] = schedule["end_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["endTime"] = schedule["end_date"].strftime('%H:%M')
                else: # 예외 처리: datetime 객체가 아닌 경우
                    selected_schedule_detail["endDate"] = ""
                    selected_schedule_detail["endTime"] = "18:00" # 기본 시간

                selected_schedule_detail["content"] = schedule.get("content", "")
                selected_schedule_detail["type"] = schedule.get("type", "")
                selected_schedule_detail["status"] = schedule.get("status", "") 
                
                user_name = get_user_name_by_id(schedule.get("user_id")) 
                selected_schedule_detail["personName"] = user_name if user_name else ""
                
                project_title = get_project_title_by_id(schedule.get("project_id")) 
                selected_schedule_detail["projectTitle"] = project_title if project_title else ""
                
                member_ids = schedule.get("member", []) 
                
                print("data확인", member_ids)
                member_names = get_user_names_by_ids(member_ids)
                # memberNames를 문자열 배열 그대로 유지하여 join(',')으로 프론트에 전달
                selected_schedule_detail["memberNames"] = member_names 
                
            else:
                print(f"DEBUG: No schedule found for ID: {schedule_id_param}")
        except Exception as e:
            print(f"ERROR: Failed to fetch schedule detail for ID {schedule_id_param}: {e}")
            selected_schedule_detail = {}

    project_titles = [p["title"] for p in projects_collection.find({}, {"title": 1})]
    
    # 모든 사용자 이름 가져오기
    # user_names = [user["name"] for user in users_collection.find({}, {"_id": 1, "name": 1}).sort("name", 1)] # 알파벳 순 정렬
    user_names = [user for user in users_collection.find({}, {"_id": 1, "name": 1}).sort("name", 1)] # 알파벳 순 정렬

    return render_template('timeline.html',
                            current_year=current_year,
                            current_month=current_month,
                            calendar_days=calendar_days,
                            daily_schedules=daily_schedules,
                            selected_date=selected_date_str,
                            selected_schedule_detail=selected_schedule_detail, 
                            status_options_by_type=STATUS_OPTIONS_BY_TYPE, 
                            project_titles=project_titles,
                            user_names=user_names) # user_names 추가

@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    data = request.get_json()
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status', 'person_name']):
        return jsonify({"success": False, "message": "필수 필드(일정 이름, 기간, 타입, 상태, 작성자)가 누락되었습니다."}), 400

    person_name = data.get("person_name")
    user_id = get_user_id_by_name(person_name) 

    if not user_id:
        # 드롭다운 선택 방식이므로 이 에러는 발생하지 않아야 하지만, 안전을 위해 유지
        return jsonify({"success": False, "message": f"작성자 '{person_name}'을(를) 찾을 수 없습니다. 유효한 사용자를 선택해주세요."}), 400

    # start_date와 end_date를 ISO 8601 문자열로 받아서 datetime 객체로 변환
    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")

        start_date_dt = datetime.datetime.fromisoformat(start_date_iso)
        end_date_dt = datetime.datetime.fromisoformat(end_date_iso)
    except ValueError:
        return jsonify({"success": False, "message": "유효하지 않은 날짜/시간 형식입니다. (YYYY-MM-DDTHH:MM:SS)"}), 400

    new_schedule = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "user_id": user_id, 
        "created_at": datetime.datetime.now() 
    }

    # member_names (JSON 문자열)을 파싱하여 배열로 변환
    member_names_json = data.get("member_names", "[]") # 기본값 빈 JSON 배열 문자열
    members_to_save = []
    if member_names_json:
        try:
            parsed_members = json.loads(member_names_json)
            if isinstance(parsed_members, list):
                # 여기서 각 멤버 이름에 해당하는 ObjectId를 찾아서 배열에 추가
                members_to_save = get_user_ids_by_names(parsed_members) # 수정된 get_user_ids_by_names 사용
            else:
                print(f"WARN: member_names is not a list after parsing: {parsed_members}")
        except json.JSONDecodeError as e:
            print(f"ERROR: JSONDecodeError for member_names: {e} - Raw: {member_names_json}")
    
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
        return jsonify({"success": True, "message": "일정이 성공적으로 추가되었습니다.", "new_schedule_id": str(result.inserted_id)})
    except Exception as e:
        print(f"ERROR create_schedule: {e}") 
        return jsonify({"success": False, "message": f"일정 추가 중 오류 발생: {str(e)}"}), 500

@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    data = request.get_json()
    print("수신 데이터:", data) # 디버깅을 위해 수신 데이터 출력

    original_schedule_id_param = data.get("original_schedule_id_param")

    if not original_schedule_id_param:
        return jsonify({"success": False, "message": "수정할 일정 ID가 누락되었습니다."}), 400

    try:
        schedule_obj_id_to_update = ObjectId(original_schedule_id_param)
    except Exception as e:
        return jsonify({"success": False, "message": f"유효하지 않은 일정 ID 형식입니다: {e}"}), 400

    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status', 'person_name']):
        return jsonify({"success": False, "message": "필수 필드(일정 이름, 기간, 타입, 상태, 작성자)가 누락되었습니다."}), 400

    person_name = data.get("person_name")
    user_id = get_user_id_by_name(person_name) 

    if not user_id:
        return jsonify({"success": False, "message": f"작성자 '{person_name}'을(를) 찾을 수 없습니다. 유효한 사용자를 선택해주세요."}), 400
    
    # start_date와 end_date를 ISO 8601 문자열로 받아서 datetime 객체로 변환
    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")

        # fromisoformat은 'Z'나 '+00:00'을 직접 처리하지 못할 수 있으므로, .replace()로 제거
        # 또는 dateutil.parser.isoparse 사용 권장 (pip install python-dateutil)
        start_date_dt = datetime.datetime.fromisoformat(start_date_iso.replace('Z', '+00:00'))
        end_date_dt = datetime.datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
    except ValueError as e:
        return jsonify({"success": False, "message": f"유효하지 않은 날짜/시간 형식입니다: {e}"}), 400

    updated_schedule_data = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "user_id": user_id, 
        "updated_at": datetime.datetime.now()
    }

    # member_names (JSON 문자열)을 파싱하여 배열로 변환
    members_to_save = json.loads(data.get("member_names"))
    # member_names_json = data.get("member_names", "[]") # 기본값 빈 JSON 배열 문자열
    # members_to_save = []
    # if member_names_json:
    #     try:
    #         parsed_members = json.loads(member_names_json)
    #         if isinstance(parsed_members, list):
    #             # 여기서 각 멤버 이름에 해당하는 ObjectId를 찾아서 배열에 추가
    #             members_to_save = get_user_ids_by_names(parsed_members) # 수정된 get_user_ids_by_names 사용
    #         else:
    #             print(f"WARN: member_names is not a list after parsing: {parsed_members}")
    #     except json.JSONDecodeError as e:
    #         print(f"ERROR: JSONDecodeError for member_names: {e} - Raw: {member_names_json}")
    li = []
    for m in members_to_save:
        li.append(ObjectId(m))
        
    
    updated_schedule_data["member"] = li

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
        # 프로젝트 타입이 아니면 project_id를 None으로 설정 (기존에 값이 있었더라도 제거)
        updated_schedule_data["project_id"] = None 

    try:
        result = timeline_collection.update_one(
            {"_id": schedule_obj_id_to_update},
            {"$set": updated_schedule_data}
        )
        if result.modified_count == 1:
            return jsonify({"success": True, "message": "일정이 성공적으로 수정되었습니다."})
        else:
            # matched_count는 1이지만 modified_count가 0인 경우 (변경 사항 없음)
            # 또는 찾지 못한 경우
            found_document = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
            if found_document:
                return jsonify({"success": True, "message": "일정 내용이 변경되지 않았습니다."})
            else:
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
