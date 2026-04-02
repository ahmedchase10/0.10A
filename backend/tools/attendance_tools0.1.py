from langchain.tools import tool
import requests
from backend.config import JWS_AI_TOKEN

@tool
def update_attendance(student_id:int ,class_id:int ,date:str ,status: str) -> dict:
    """Update student attendance in the database.
    Use this when the teacher wants to mark attendance.
    Status must be: 'present', 'absent' or 'excused'."""
    try:
        url="http://localhost:3001/api/attendance"

        headers = {
            "Authorization": f"Bearer {JWS_AI_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "studentId": student_id,
            "classId": class_id,
            "date": date,
            "status": status
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 201:
            return {
                "error": response.json(),
                "status": response.status_code
            }
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
        "error": str(e)
    }

'''
@tool
def get_attendance_report() -> dict:
'''

#remove @tool to test the functions
'''
er=update_attendance(1,11,"2025-2-01","A")
print(er)
'''