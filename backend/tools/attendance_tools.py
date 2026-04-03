from langchain.tools import tool
import requests
from datetime import date



@tool
def update_attendance(token:str, student_id:int ,class_id:int ,status: str) -> dict:
    """Update student attendance in the database.
    Use this when the teacher wants to mark attendance.
    Status must be: 'present', 'absent' or 'excused'.
    use get_students to get the student id and class id if you don't have them."""
    try:
        if status not in ("P", "A", "L", "E"):
            return {"success": False, "message": f"Invalid status '{status}'. Use P, A, L, or E."}
        url="http://localhost:3001/api/attendance"
        now = date.today()


        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "studentId": student_id,
            "classId": class_id,
            "date": now.isoformat(),
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
@tool
def get_classes(token) -> dict:
    """Fetch the list of classes for the teacher."""
    try:
        url="http://localhost:3001/api/classes"

        headers = {
            "Authorization": f"Bearer {token}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {
                "error": response.json(),
                "status": response.status_code
            }
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
        "error": str(e)
    }


def filter_response(response_json, args):
    return {
        "classes": [
            {k: item.get(k) for k in args}
            for item in response_json.get("classes", [])
        ]
    }


'''used when we want to identify a student from the teacher voice(typing might not be identical example:sara and sarra'''
@tool
def get_students(token ,class_id = None ) -> dict :
    """Fetch the id name and class id of all students of the teacher
    or the students of a certain class of the teacher so you need to pass a classId ."""
    try:
        url=f"http://localhost:3001/api/students"

        headers = {
            "Authorization": f"Bearer {token}",
        }
        if class_id is not None :
            args = {
                "classId": class_id
            }
            response = requests.get(url, params=args, headers=headers)
        else:
            response = requests.get(url, headers=headers)
            return filter_response(response.json(), ["id", "name", "classId"])

        if response.status_code != 200:
            return {
                "error": response.json(),
                "status": response.status_code
            }


    except requests.exceptions.RequestException as e:
        return {
        "error": str(e)
    }

threshold=4
@tool
def check_threshold(token:str ,class_id:int) -> dict:
    """Check if any student in the class has reached the absence threshold."""
    try:
        url=f"http://localhost:3001/api/attendance/absences"

        headers = {
            "Authorization": f"Bearer {token}",
        }
        args= {
                "classId": class_id ,
                "threshold": threshold
               }
        response = requests.get(url ,params=args ,headers=headers)

        if response.status_code != 200:
            return {
                "error": response.json(),
                "status": response.status_code
            }
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e)
        }








