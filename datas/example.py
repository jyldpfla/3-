from bson import ObjectId

# 예시 데이터 참고
# null 값은 다른 컬렉션에서 삽입해야하는 값임 -> ObjectId("")

project_data = {
    "title": "예시입니다",
    "description": "웹 기반 협업 툴 개발",
    "goal": "효율적인 협업 제공",
    "scope": "기획, 개발, 테스트 포함",
    "schedule": "2025 Q3",
    "schedule.startDate": "2025-07-01",
    "schedule.endDate": "2025-09-30",
    "budget": 10000000,
    "outcome": "MVP 개발 완료",
    "createAt": "2025-06-01",
    "updateAt": "2025-06-10",
    "client": "OO 기업",
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

board_data = {
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

team_data = {
    "projectId": None,
    "member": ["장예림", "백인호"],
    "status": ["참여중", "대기"]
}