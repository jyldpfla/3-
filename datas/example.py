from bson import ObjectId

# 예시 데이터 참고
# null 값은 다른 컬렉션에서 삽입해야하는 값임 -> ObjectId("")

project_data = {
    "title": "프로젝트1",
    "description": "웹 기반 협업 툴 개발",
    "schedule.start_date": "2025-07-01",
    "schedule.end_date": "2025-09-30",
    "status": "진행 대기",
    "client": "OO 기업",
    "project_manager": ObjectId("6853aebf690a71fa9ad4b6e3"),
    "TeamId": None,
    "ScheduleListId": None
}

user_data = {
        "email": "ino456852@example.com",
        "name": "백인호",
        "userPassword": "hashed_pw_3",
        "role": "개발자",
        "profile": "개발자",
        "department": "개발팀",
        "position": "팀장",
        "createAt": "2025-06-03",
        "phone_num": "010-3456-7890",
        "Personal_todoId": None,
        "BoardId": None
}

schedule_data = {
    "projectId": None,
    "title": "예시입니다",
    "schedule.startDate": "2025-07-01",
    "schedule.endDate": "2025-07-10",
    "writer": None,
    "member": "기획팀",
    "content": "초안 작성 및 회의",
    "update_date": "2025-07-09",
    "create_date": "2025-07-01",
    "type": "중간일정"
}

personal_todo_data = {
    "user_id": ObjectId("6853aebf690a71fa9ad4b6e3"),
    "content": "예시입니다",
    "end_date": "2025-07-10",
    "status": "To do",
}

board_data = {
    "user_id": None,
    "title": "예시입니다",
    "category": "공지",
    "content": "초안 작성 및 회의",
    "update_date": "2025-07-09",
    "create_date": "2025-07-01",
}

team_data = {
    "projectId": ObjectId("6853aebf690a71fa9ad4b6e2"),
    "member": ["장예림", "백인호"],
    "status": ["참여중", "대기"]
}

timeline_data = {
    "_project_id": None,
    "user_id": ObjectId("6853aebf690a71fa9ad4b6e3"),
    "title": "연차",
    "start_date": "2025-06-23",
    "end_date": "2025-07-02",
    "member": None,
    "content": "내용 작성",
    "type": "개인",
    "status": "연차",
}

timeline_data2 = {
    "project_id": ObjectId("6858e855a4d53f19194ed3b2"),
    "user_id": ObjectId("6853aebf690a71fa9ad4b6e3"),
    "title": "회의",
    "start_date": "2025-06-23",
    "end_date": "2025-07-02",
    "member": [ObjectId("6853aebf690a71fa9ad4b6e3"), ObjectId("6854be045d8c554194fe197b")],
    "content": "내용 작성",
    "type": "프로젝트",
    "status": "진행중",
}

timeline_data = {
    "_project_id": None,
    "user_id": ObjectId("6853aebf690a71fa9ad4b6e3"),
    "title": "연차",
    "start_date": "2025-06-23",
    "end_date": "2025-07-02",
    "member": None,
    "content": "내용 작성",
    "type": "개인",
    "status": "연차",
}

timeline_data2 = {
    "project_id": ObjectId("6858e855a4d53f19194ed3b2"),
    "user_id": ObjectId("6853aebf690a71fa9ad4b6e3"),
    "title": "회의",
    "start_date": "2025-06-23",
    "end_date": "2025-07-02",
    "member": [ObjectId("6853aebf690a71fa9ad4b6e3"), ObjectId("6854be045d8c554194fe197b")],
    "content": "내용 작성",
    "type": "프로젝트",
    "status": "진행중",
}