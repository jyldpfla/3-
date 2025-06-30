from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from datetime import datetime, timedelta, date, time
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import os

# Load .env file
load_dotenv()
# Get MongoDB credentials from environment variables
mongo_user_id = os.getenv("USER_ID")
mongo_user_pw = os.getenv("USER_PW")
# SECRET_KEY is loaded directly by app.secret_key
uri = f"mongodb+srv://{mongo_user_id}:{mongo_user_pw}@team3.fxbwcnh.mongodb.net/"

app = Flask(__name__)
# Set Flask secret key from environment variable for session management
app.secret_key = os.environ["SECRET_KEY"]
client = MongoClient(uri)
db = client['team3']

# Reference to MongoDB collections
project_collection = db["projects"]
user_collection = db["users"]
personal_todo_collection = db["personal_todo"]
board_collection = db["board"]
team_collection = db["team"]
timeline_collection = db["timeline"]

@app.context_processor
def inject_user():
    session["user_id"] = "685df192a2cd54b0683ea346"
    user_id = session.get("user_id")
    print(f"Current session user_id: {user_id}") # Keep for debugging

    user_info = None # Initialize user_info object to be passed to the template
    if user_id:
        try:
            user_obj_id = ObjectId(user_id) # Attempt to convert user_id to ObjectId
            found_user = user_collection.find_one(
                {"_id": user_obj_id},
                {"name": 1, "position": 1, "department": 1} # Retrieve only necessary fields
            )
            # Convert ObjectId to string for easy use in Jinja2 templates.
            # This is crucial because Jinja2 has difficulty directly using ObjectId in conditional statements.
            if found_user:
                user_info = {
                    "_id": str(found_user["_id"]), # Convert ObjectId to string
                    "name": found_user.get("name"),
                    "position": found_user.get("position"),
                    "department": found_user.get("department")
                }
        except Exception as e:
            print(f"Error fetching session user info: {e}")
            user_info = None # Set user_info to None if an error occurs, treating as not logged in

    # Load unread notifications from the 'notifications' collection
    unread_notes = []
    has_notification = False
    if user_id and "notifications" in db.list_collection_names(): 
        try:
            # Convert user_id to ObjectId for querying, as it might be a string
            unread_notes = list(db.notifications.find({
                "user_id": ObjectId(user_id), 
                "read": False
            }))
            messages = [n["message"] for n in unread_notes]
            has_notification = len(messages) > 0
        except Exception as e:
            print(f"Error fetching notification info: {e}")
            messages = []
    else:
        messages = []

    return dict(
        user_info=user_info, # Pass user_info object (used for determining login status)
        notifications=messages,
        has_notification=has_notification
    )

# Mapping for schedule types to CSS classes
TYPE_TAG_CLASS_MAP = {"개인": "personal-schedule-tag", "회사": "company-schedule-tag", "프로젝트": "project-schedule-tag"}

# Status options based on schedule type
STATUS_OPTIONS_BY_TYPE = {
    "개인": [{"value": "연차", "text": "연차"}, {"value": "월차", "text": "월차"},
        {"value": "병가", "text": "병가"}, {"value": "출장", "text": "출장"}],
    "회사": [{"value": "사내일정", "text": "사내일정"}],
    "프로젝트": [{"value": "진행중", "text": "진행중"}, {"value": "진행대기", "text": "진행대기"},
        {"value": "지연", "text": "지연"}, {"value": "중단", "text": "중단"}, {"value": "완료", "text": "완료"}]}

# Mapping for schedule status to CSS classes
STATUS_TAG_CLASS_MAP = {
    "연차": "vacation-year-tag", "월차": "vacation-month-tag", "병가": "sick-leave-tag", "출장": "travel-tag",
    "사내일정": "company-event-tag",
    "진행중": "status-inprogress-tag", "진행대기": "status-wait-tag", "지연": "status-delayed-tag",
    "중단": "status-stopped-tag", "완료": "status-completed-tag",
}

# Schedule type filter options for dropdown
SCHEDULE_TYPE_OPTIONS = [{"value": "전체", "text": "전체 일정"}, {"value": "개인", "text": "개인 일정"},
    {"value": "회사", "text": "회사 일정"}, {"value": "프로젝트", "text": "프로젝트 일정"}]

# Helper function: Get user name by user_id (ObjectId)
def get_user_name_by_id(user_obj_id):
    try:
        if not isinstance(user_obj_id, ObjectId): # Attempt to convert to ObjectId if string
            user_obj_id = ObjectId(user_obj_id)
        # Check "name" field name according to actual DB schema
        user = user_collection.find_one({"_id": user_obj_id}, {"name": 1}) 
        return user["name"] if user else None
    except Exception as e:
        print(f"Error fetching user name by ID: {e}")
        return None

# Helper function: Get project_id (ObjectId) by project title
def get_project_id_by_title(project_title):
    # Check "title" field name according to actual DB schema
    project = project_collection.find_one({"title": project_title}) 
    return project["_id"] if project else None

# Helper function: Get project title by project_id (ObjectId)
def get_project_title_by_id(project_obj_id):
    try:
        if not isinstance(project_obj_id, ObjectId): # Attempt to convert to ObjectId if string
            project_obj_id = ObjectId(project_obj_id)
        # Check "title" field name according to actual DB schema
        project = project_collection.find_one({"_id": project_obj_id}) 
        return project["title"] if project else None
    except Exception as e:
        print(f"Error fetching project title by ID: {e}")
        return None

# Main timeline route
@app.route('/timeline')
def timeline():
    # user_info is automatically injected into the template by @app.context_processor
    
    year_param = request.args.get('year')
    month_param = request.args.get('month')
    date_param = request.args.get('date')
    schedule_id_param = request.args.get('schedule_id')
    type_filter_param = request.args.get('type', '전체') # Default value '전체'

    # Retrieve all user information, converting _id to string.
    # This is used for JavaScript's allUsersFlattened object and schedulePersonNameSelect options.
    user_names = [] 
    for user in user_collection.find({}, {"_id": 1, "name": 1, "position": 1, "department": 1}):
        user_data = {
            "_id": str(user["_id"]), # Convert ObjectId to string
            "name": user.get("name", "이름 없음"), # Ensure 'name' exists, provide default
            "position": user.get("position", ""),
            "department": user.get("department", "")
        }
        user_names.append(user_data) 
    
    # Grouped user list by department (used for JavaScript's grouped_users_by_department)
    grouped_users_by_department = {}
    for user_data in user_names: 
        department = user_data.get("department", "기타")
        if department not in grouped_users_by_department:
            grouped_users_by_department[department] = []
        grouped_users_by_department[department].append({
            "id": user_data["_id"], # _id is already a string
            "name": user_data["name"],
            "position": user_data["position"]
        })
    
    today = date.today()
    current_year = int(year_param) if year_param else today.year
    current_month = int(month_param) if month_param else today.month

    # Calculate start and end dates of the current month
    start_of_month = date(current_year, current_month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    calendar_days = []
    # Calculate offset to align the first week of the calendar with Sunday (0)
    first_day_of_week = start_of_month.weekday() # Monday(0) ~ Sunday(6)
    start_offset = (first_day_of_week + 1) % 7 # Adjust for a calendar starting on Sunday
    start_date = start_of_month - timedelta(days=start_offset)

    # Calculate 35 days (5 weeks) to display on the calendar
    for _ in range(35): 
        is_current_month = (start_date.month == current_month)
        formatted_date = start_date.strftime('%Y-%m-%d')
        
        start_of_day_dt = datetime.combine(start_date, time.min)
        end_of_day_dt = datetime.combine(start_date, time.max)

        # Check if there are schedules on that date
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
        selected_date_obj = today # If no date parameter in URL, set to today's date
    
    selected_date_str = selected_date_obj.strftime('%Y-%m-%d')

    # Fetch daily schedules via API function
    daily_schedules_response = get_daily_schedules_api(date_param=selected_date_str, selected_type=type_filter_param).get_json()
    daily_schedules = daily_schedules_response['daily_schedules'] if daily_schedules_response and daily_schedules_response.get('success') else []

    selected_schedule_detail = {} # Dictionary to store detailed info of the selected schedule
    if schedule_id_param: # If schedule_id is in the URL
        try:
            schedule = timeline_collection.find_one({"_id": ObjectId(schedule_id_param)})
            if schedule:
                selected_schedule_detail["scheduleId"] = str(schedule["_id"])
                selected_schedule_detail["scheduleName"] = schedule.get("title", "") 
                
                # Format start date/time
                if isinstance(schedule.get("start_date"), datetime):
                    selected_schedule_detail["startDate"] = schedule["start_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["startTime"] = schedule["start_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["startDate"] = ""
                    selected_schedule_detail["startTime"] = "09:00"
                
                # Format end date/time
                if isinstance(schedule.get("end_date"), datetime):
                    selected_schedule_detail["endDate"] = schedule["end_date"].strftime('%Y-%m-%d')
                    selected_schedule_detail["endTime"] = schedule["end_date"].strftime('%H:%M')
                else:
                    selected_schedule_detail["endDate"] = ""
                    selected_schedule_detail["endTime"] = "18:00"

                selected_schedule_detail["content"] = schedule.get("content", "")
                selected_schedule_detail["type"] = schedule.get("type", "")
                # Remove spaces from status value (for matching HTML classes)
                selected_schedule_detail["status"] = schedule.get("status", "").strip().replace(" ", "").replace("\u00a0", "")
                
                # Get author name and ID via 'user_id' field, add as 'personName' and 'personId'
                author_user_id = schedule.get("user_id")
                user_name = get_user_name_by_id(author_user_id) 
                selected_schedule_detail["personName"] = user_name if user_name else "-"
                selected_schedule_detail["personId"] = str(author_user_id) if author_user_id else "None" # Author ID (string) for JS
                
                # Get project title
                project_title = get_project_title_by_id(schedule.get("project_id")) 
                selected_schedule_detail["projectTitle"] = project_title if project_title else ""
                
                # Get members list and construct detailed info
                member_ids = schedule.get("member", []) 
                members_detailed_info = []
                if member_ids: 
                    # Convert both string IDs and ObjectIds to ObjectId, then remove duplicates
                    member_object_ids = [ObjectId(mid) for mid in member_ids if isinstance(mid, str) and ObjectId.is_valid(mid)]
                    member_object_ids.extend([mid for mid in member_ids if isinstance(mid, ObjectId)])
                    member_object_ids = list(set(member_object_ids)) # Remove duplicates

                    for user_doc in user_collection.find(
                        {"_id": {"$in": member_object_ids}},
                        {"name": 1, "position": 1, "department": 1, "_id": 1} 
                    ):
                        members_detailed_info.append({
                            "id": str(user_doc["_id"]), # Convert ObjectId to string
                            "name": user_doc.get("name", "이름 없음"),
                            "position": user_doc.get("position", "직급 없음"),
                            "department": user_doc.get("department", "부서 없음")
                        })
                selected_schedule_detail["members_detailed_info"] = members_detailed_info
                selected_schedule_detail["memberNames"] = [m["name"] for m in members_detailed_info]
                selected_schedule_detail["memberIds"] = [m["id"] for m in members_detailed_info] # List of string IDs

        except Exception as e:
            print(f"Error loading selected schedule details: {e}")
            selected_schedule_detail = {} # Initialize details if an error occurs

    project_titles = [p["title"] for p in project_collection.find({}, {"title": 1})] # Get all project titles

    return render_template('timeline.html',
                           current_year=current_year, current_month=current_month, calendar_days=calendar_days,
                           daily_schedules=daily_schedules, selected_date=selected_date_str,
                           selected_schedule_detail=selected_schedule_detail,
                           status_options_by_type=STATUS_OPTIONS_BY_TYPE,
                           project_titles=project_titles, 
                           user_names=user_names, # List of objects containing ID and name
                           grouped_users_by_department=grouped_users_by_department,
                           schedule_type_options=SCHEDULE_TYPE_OPTIONS,
                           selected_type_filter=type_filter_param
                          )

# API: Filter and retrieve daily schedules
@app.route('/timeline/get_daily_schedules', methods=['GET'])
def get_daily_schedules_api(date_param=None, selected_type='전체'):
    if date_param is None: # If called directly via HTTP request
        date_param = request.args.get('date')
        selected_type = request.args.get('type', '전체')

    if not date_param:
        return jsonify({"success": False, "message": "Date information is required."}), 400

    try:
        selected_date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format."}), 400

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
            "schedule_id_param": str(schedule["_id"]), # Convert ObjectId to string
            "name": schedule.get("title", "제목 없음"),
            "status_tag_class": status_tag_class,
            "status_display_text": schedule_status,
            "type": schedule.get("type", "")
        })
    return jsonify({"success": True, "daily_schedules": daily_schedules})

# API: Create schedule
@app.route('/timeline/create_schedule', methods=['POST'])
def create_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session: # Check login status
        return jsonify({"success": False, "message": "Only logged-in users can add schedules."}), 401
    
    data = request.get_json()
    
    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "Required fields (Title, Period, Type, Status) are missing."}), 400

    # The author of the schedule is automatically set to the logged-in user's ID in the session.
    author_id_to_save = user_id_from_session
    if not author_id_to_save: # If user_id is missing from session, return error
        return jsonify({"success": False, "message": "Logged-in user information is missing. Please log in again."}), 401
    
    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        start_date_dt = datetime.fromisoformat(start_date_iso)
        end_date_dt = datetime.fromisoformat(end_date_iso)
    except ValueError as e:
        print(f"Date/time format error: {e}")
        return jsonify({"success": False, "message": "Invalid date/time format. (YYYY-MM-DDTHH:MM:SS)"}), 400

    new_schedule = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        "user_id": ObjectId(author_id_to_save), # Save the ObjectId of the logged-in user
        "created_at": datetime.now() 
    }

    # Handle member_ids (received as a list of ObjectId strings from frontend)
    member_ids_json = data.get("member_ids", "[]") # Changed to 'member_ids' field
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
            print(f"JSON decoding error: {e}")
            pass # If decoding error occurs, keep as empty list
    
    new_schedule["member"] = members_to_save

    if new_schedule["type"] == "프로젝트":
        project_title = data.get("project_title")
        if not project_title:
            return jsonify({"success": False, "message": "Please select a project title if 'Project' schedule type is selected."}), 400
        
        project_id = get_project_id_by_title(project_title)
        if project_id:
            new_schedule["project_id"] = project_id 
        else:
            return jsonify({"success": False, "message": f"Project '{project_title}' not found."}), 400
    else:
        new_schedule["project_id"] = None # If not project type, project_id is None

    try:
        result = timeline_collection.insert_one(new_schedule) 
        return jsonify({"success": True, "message": "Schedule created successfully."})
    except Exception as e:
        print(f"Error creating schedule: {e}")
        return jsonify({"success": False, "message": f"Error creating schedule: {str(e)}"}), 500

# API: Update schedule
@app.route('/timeline/update_schedule', methods=['POST'])
def update_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session: # Check login status
        return jsonify({"success": False, "message": "Only logged-in users can update schedules."}), 401 

    data = request.get_json()

    original_schedule_id_param = data.get("original_schedule_id_param")

    if not original_schedule_id_param:
        return jsonify({"success": False, "message": "Schedule ID to update is missing."}), 400

    try:
        schedule_obj_id_to_update = ObjectId(original_schedule_id_param)
    except Exception as e:
        print(f"Invalid schedule ID format: {e}")
        return jsonify({"success": False, "message": f"Invalid schedule ID format: {e}"}), 400

    schedule_to_update = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
    if not schedule_to_update:
        return jsonify({"success": False, "message": "Schedule to update not found."}), 404
    
    # Check modification permission: Verify if the currently logged-in user is the author of the schedule
    # If you want only the author to be able to modify, uncomment this. Currently, any logged-in user can modify.
    # if schedule_to_update.get("user_id") != ObjectId(user_id_from_session):
    #     return jsonify({"success": False, "message": "You do not have permission to modify this schedule."}), 403 

    if not all(k in data for k in ['schedule_name', 'start_date', 'end_date', 'type', 'status']):
        return jsonify({"success": False, "message": "Required fields (Title, Period, Type, Status) are missing."}), 400

    try:
        start_date_iso = data.get("start_date")
        end_date_iso = data.get("end_date")
        # Replace 'Z' with '+00:00' to handle UTC timezone for fromisoformat compatibility
        start_date_dt = datetime.fromisoformat(start_date_iso.replace('Z', '+00:00'))
        end_date_dt = datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
    except ValueError as e:
        print(f"Date/time format error: {e}")
        return jsonify({"success": False, "message": f"Invalid date/time format: {e}"}), 500

    updated_schedule_data = {
        "title": data.get("schedule_name"), 
        "start_date": start_date_dt, 
        "end_date": end_date_dt, 
        "content": data.get("content", ""),
        "type": data.get("type"),
        "status": data.get("status"),
        # The user_id field is not included in the update as the author does not change.
        "updated_at": datetime.now()
    }

    # Handle member_ids (received as a list of ObjectId strings from frontend)
    member_ids_json = data.get("member_ids", "[]") # Changed to 'member_ids' field
    members_to_save = []
    if member_ids_json:
        try:
            parsed_member_ids = json.loads(member_ids_json)
            if isinstance(parsed_member_ids, list):
                for member_id_str in parsed_member_ids:
                    if ObjectId.is_valid(member_id_str):
                        members_to_save.append(ObjectId(member_id_str))
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            pass
    
    updated_schedule_data["member"] = members_to_save

    if updated_schedule_data["type"] == "프로젝트":
        project_title = data.get("project_title")
        if not project_title:
            return jsonify({"success": False, "message": "Please select a project title if 'Project' schedule type is selected."}), 400
        
        project_id = get_project_id_by_title(project_title)
        if project_id:
            updated_schedule_data["project_id"] = project_id 
        else:
            return jsonify({"success": False, "message": f"Project '{project_title}' not found."}), 400
    else:
        updated_schedule_data["project_id"] = None 

    try:
        result = timeline_collection.update_one(
            {"_id": schedule_obj_id_to_update},
            {"$set": updated_schedule_data}
        )
        if result.modified_count == 1:
            return jsonify({"success": True, "message": "Schedule updated successfully."})
        else:
            # If modified_count is 0, check if the document exists to differentiate between no change and not found
            found_document = timeline_collection.find_one({"_id": schedule_obj_id_to_update})
            if found_document:
                return jsonify({"success": True, "message": "No changes made to the schedule."})
            else:
                return jsonify({"success": False, "message": "Schedule not found."}), 404
    except Exception as e:
        print(f"Error updating schedule: {e}")
        return jsonify({"success": False, "message": f"Error updating schedule: {str(e)}"}), 500

# API: Delete schedule
@app.route('/timeline/delete_schedule', methods=['POST'])
def delete_schedule():
    user_id_from_session = session.get("user_id")
    if not user_id_from_session: # Check login status
        return jsonify({"success": False, "message": "Only logged-in users can delete schedules."}), 401 
        
    data = request.get_json()
    schedule_id_param = data.get("schedule_id_param")

    if not schedule_id_param:
        return jsonify({"success": False, "message": "Schedule ID to delete is missing."}), 400

    try:
        schedule_obj_id_to_delete = ObjectId(schedule_id_param)
    except Exception as e:
        print(f"Invalid schedule ID format: {e}")
        return jsonify({"success": False, "message": f"Invalid schedule ID format: {e}"}), 400

    # Optional: Check deletion permission (only author can delete)
    # schedule_to_delete = timeline_collection.find_one({"_id": schedule_obj_id_to_delete})
    # if schedule_to_delete and schedule_to_delete.get("user_id") != ObjectId(user_id_from_session):
    #     return jsonify({"success": False, "message": "You do not have permission to delete this schedule."}), 403

    try:
        result = timeline_collection.delete_one({"_id": schedule_obj_id_to_delete}) 
        if result.deleted_count == 1:
            return jsonify({"success": True, "message": "Schedule deleted successfully."})
        else:
            return jsonify({"success": False, "message": "Schedule not found."}), 404
    except Exception as e: 
        print(f"Error deleting schedule: {e}")
        return jsonify({"success": False, "message": f"Error deleting schedule: {str(e)}"}), 500

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
