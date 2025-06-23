from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import calendar
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

if not MONGO_URI:
    raise ValueError("MONGO_URI 환경 변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
if not MONGO_DB_NAME:
    raise ValueError("MONGO_DB_NAME 환경 변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")

try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    client.admin.command('ping')
    print("MongoDB에 성공적으로 연결되었습니다!")
except Exception as e:
    print(f"MongoDB 연결 오류: {e}")

schedules_collection = db.schedules
users_collection = db.users
projects_collection = db.projects

def get_project_title_by_id(project_id):
    """프로젝트 ID로 프로젝트 제목을 가져옴 (projectId가 ObjectId로 저장되어 있을 경우)"""
    try:
        oid = ObjectId(project_id)
    except Exception:
        return "알 수 없음"
        
    project = projects_collection.find_one({"_id": oid})
    return project.get("title", "알 수 없음") if project else "알 수 없음"

def format_datetime_for_display(dt_obj):
    if not isinstance(dt_obj, datetime):
        return ""
    return dt_obj.strftime("%Y.%m.%d %I:%M %p").replace('AM', '오전').replace('PM', '오후')

def format_datetime_for_input(dt_obj):
    if not isinstance(dt_obj, datetime):
        return ""
    return dt_obj.strftime("%Y-%m-%dT%H:%M")

# 라우팅 시작

@app.route("/")
def home():
    return redirect(url_for('timeline'))

@app.route("/timeline")
def timeline():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    selected_date_str = request.args.get('date')
    selected_schedule_id_param = request.args.get('schedule_id') # 추가: 선택된 일정 ID 파라미터

    today = datetime.now().date()

    if year is None or month is None:
        current_view_date = today
        year = current_view_date.year
        month = current_view_date.month
    else:
        try:
            current_view_date = datetime(year, month, 1).date()
        except ValueError:
            current_view_date = today
            year = current_view_date.year
            month = current_view_date.month

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = current_view_date
    else:
        if today.year == year and today.month == month:
            selected_date = today
        else:
            selected_date = datetime(year, month, 1).date()

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    calendar_days = []
    for week in month_days:
        for day_num in week:
            if day_num == 0:
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
                    "is_current_month": True,
                    "is_current_day": is_selected_day,
                    "full_date": current_date_in_calendar.strftime("%Y-%m-%d")
                })
    
    # 변경: 일정 목록을 start_date 내림차순으로 정렬
    daily_schedules_from_db = list(schedules_collection.find({
        "start_date": {"$lte": datetime(selected_date.year, selected_date.month, selected_date.day, 23, 59, 59)},
        "end_date": {"$gte": datetime(selected_date.year, selected_date.month, selected_date.day, 0, 0, 0)}
    }).sort("start_date", -1)) # 정렬 순서 변경: 1 -> -1 (내림차순)

    daily_schedules_for_display = []
    for sched in daily_schedules_from_db:
        tag_class = ""
        if sched.get("type") == "프로젝트":
            tag_class = "project-tag"
        elif sched.get("type") == "개인":
            if sched.get("status") == "출장":
                tag_class = "travel-tag"
            else:
                tag_class = "personal-tag"
        
        daily_schedules_for_display.append({
            "name": sched.get("schedule_name", "이름 없음"),
            "tag_class": tag_class,
            "schedule_id_param": str(sched["_id"])
        })

    # 선택된 일정 상세 정보 (MongoDB에서 조회)
    selected_schedule_detail = {}
    selected_schedule = None

    if selected_schedule_id_param: # URL 파라미터로 넘어온 schedule_id가 있으면 최우선
        try:
            selected_schedule = schedules_collection.find_one({"_id": ObjectId(selected_schedule_id_param)})
        except Exception:
            selected_schedule = None

    if not selected_schedule: # URL 파라미터의 일정이 없거나 유효하지 않으면, 해당 날짜의 첫 번째 일정
        if daily_schedules_from_db:
            selected_schedule = daily_schedules_from_db[0]
        elif schedules_collection.count_documents({}) > 0: # 해당 날짜에 일정이 없으면, 전체 일정 중 가장 최근 일정 (내림차순 정렬이므로)
            selected_schedule = schedules_collection.find_one(sort=[("start_date", -1)]) # 변경: -1로 정렬하여 가장 최근 일정 가져옴

    if selected_schedule:
        display_title = ""
        if selected_schedule.get("type") == "개인":
            display_title = "개인"
        elif selected_schedule.get("type") == "프로젝트" and selected_schedule.get("project_title"):
            display_title = selected_schedule["project_title"]
        elif selected_schedule.get("type") == "프로젝트": # project_title이 없는 경우 schedule_name 사용
            display_title = selected_schedule.get("schedule_name", "프로젝트 일정")

        selected_schedule_detail = {
            "schedule_id_param": str(selected_schedule["_id"]),
            "type": selected_schedule.get("type", "알 수 없음"),
            "tag_class": "", 
            "schedule_title": display_title,
            "schedule_name": selected_schedule.get("schedule_name", "이름 없음"),
            "person_name": selected_schedule.get("writer_name", "작성자 알 수 없음"),
            "status": selected_schedule.get("status", "미정"),
            "start_date": format_datetime_for_display(selected_schedule.get("start_date")),
            "end_date": format_datetime_for_display(selected_schedule.get("end_date")),
            "start_date_input": format_datetime_for_input(selected_schedule.get("start_date")),
            "end_date_input": format_datetime_for_input(selected_schedule.get("end_date")),
            "content": selected_schedule.get("content", ""),
            "tasks": selected_schedule.get("tasks", []),
            "member": selected_schedule.get("member", "")
        }
        
        if selected_schedule_detail["type"] == "프로젝트":
            selected_schedule_detail["tag_class"] = "project-tag"
        elif selected_schedule_detail["type"] == "개인":
            if selected_schedule_detail["status"] == "출장":
                selected_schedule_detail["tag_class"] = "travel-tag"
            else:
                selected_schedule_detail["tag_class"] = "personal-tag"

    all_project_titles = [proj.get("title", "알 수 없음") for proj in projects_collection.find({}, {"title": 1})]

    status_options_by_type = {
        "개인": [
            {"value": "연차", "text": "연차"},
            {"value": "월차", "text": "월차"},
            {"value": "병가", "text": "병가"},
            {"value": "출장", "text": "출장"},
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
        current_year=year,
        current_month=month,
        current_year_month=f"{year}.{month:02d}",
        calendar_days=calendar_days,
        daily_schedules=daily_schedules_for_display,
        selected_schedule_detail=selected_schedule_detail,
        project_titles=all_project_titles,
        status_options_by_type=status_options_by_type,
        selected_date_display=selected_date.strftime("%Y.%m.%d")
    )

# 특정 날짜의 일정 목록을 JSON으로 반환하는 API
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
    # 변경: 일정 목록을 start_date 내림차순으로 정렬
    schedules_from_db = schedules_collection.find({
        "start_date": {"$lte": datetime(query_date.year, query_date.month, query_date.day, 23, 59, 59)},
        "end_date": {"$gte": datetime(query_date.year, query_date.month, query_date.day, 0, 0, 0)}
    }).sort("start_date", -1) # 정렬 순서 변경: 1 -> -1 (내림차순)

    for sched in schedules_from_db:
        tag_class = ""
        if sched.get("type") == "프로젝트":
            tag_class = "project-tag"
        elif sched.get("type") == "개인":
            if sched.get("status") == "출장":
                tag_class = "travel-tag"
            else:
                tag_class = "personal-tag"
            
        schedules_on_date.append({
            "name": sched.get("schedule_name", "이름 없음"),
            "tag_class": tag_class,
            "schedule_id_param": str(sched["_id"])
        })
    
    return jsonify(schedules_on_date)

@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    data = request.json
    try:
        start_dt = datetime.strptime(data["start_date"], '%Y-%m-%dT%H:%M')
        end_dt = datetime.strptime(data["end_date"], '%Y-%m-%dT%H:%M')
    except ValueError as e:
        return jsonify({"success": False, "message": f"잘못된 날짜/시간 형식입니다: {e}"}), 400

    writer_name_to_use = data.get("writer_name")

    project_id_to_use = None
    project_title_to_save = None 
    if data["type"] == "프로젝트":
        project_title_to_save = data.get("project_title")
        project = projects_collection.find_one({"title": project_title_to_save})
        if project:
            project_id_to_use = project["_id"]

    new_schedule = {
        "project_id": project_id_to_use,
        "schedule_name": data["schedule_name"],
        "writer_name": writer_name_to_use,
        "start_date": start_dt,
        "end_date": end_dt,
        "content": data.get("content", ""),
        "type": data["type"],
        "status": data["status"],
        "project_title": project_title_to_save,
        "created_at": datetime.now(),
    }
    
    result = schedules_collection.insert_one(new_schedule)
    return jsonify({"success": True, "message": "일정이 성공적으로 추가되었습니다.", "new_schedule_id": str(result.inserted_id)})

@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    data = request.json
    original_schedule_id_param = data["original_schedule_id_param"]

    try:
        start_dt = datetime.strptime(data["start_date"], '%Y-%m-%dT%H:%M')
        end_dt = datetime.strptime(data["end_date"], '%Y-%m-%dT%H:%M')
        schedule_oid = ObjectId(original_schedule_id_param)
    except Exception as e:
        return jsonify({"success": False, "message": f"잘못된 요청 데이터 또는 일정 ID 형식입니다: {e}"}), 400

    writer_name_to_use = data.get("writer_name")

    project_id_to_use = None
    project_title_to_save = None
    if data["type"] == "프로젝트":
        project_title_to_save = data.get("project_title")
        project = projects_collection.find_one({"title": project_title_to_save})
        if project:
            project_id_to_use = project["_id"]

    update_fields = {
        "project_id": project_id_to_use,
        "schedule_name": data["schedule_name"],
        "writer_name": writer_name_to_use,
        "start_date": start_dt,
        "end_date": end_dt,     
        "content": data.get("content", ""),
        "type": data["type"],
        "status": data["status"],
        "project_title": project_title_to_save,
        "updated_at": datetime.now(),
    }
    
    result = schedules_collection.update_one(
        {"_id": schedule_oid},
        {"$set": update_fields}
    )
            
    if result.modified_count > 0:
        # 수정 성공 시, 수정된 일정의 ID를 반환하여 프론트엔드에서 유지할 수 있도록 함
        return jsonify({"success": True, "message": "일정이 성공적으로 업데이트되었습니다.", "updated_schedule_id": str(schedule_oid)})
    return jsonify({"success": False, "message": "일정 업데이트에 실패했거나 변경된 내용이 없습니다."})

@app.route('/timeline/delete_schedule', methods=['POST'])
def delete_schedule():
    data = request.json
    schedule_id_param_to_delete = data["schedule_id_param"]
    
    try:
        schedule_oid = ObjectId(schedule_id_param_to_delete)
    except Exception:
        return jsonify({"success": False, "message": "유효하지 않은 일정 ID 형식입니다."}), 400

    result = schedules_collection.delete_one({"_id": schedule_oid})
    
    if result.deleted_count > 0:
        return jsonify({"success": True, "message": "일정이 성공적으로 삭제되었습니다."})
    return jsonify({"success": False, "message": "일정이 존재하지 않습니다."})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)