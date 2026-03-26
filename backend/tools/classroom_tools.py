import os
from langchain.tools import tool
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from backend.tools.google_auth import get_google_credentials

@tool
def list_classrooms() -> str:
    """List all active Google Classroom courses for the teacher.
    Use this when the teacher wants to see their classes
    or before uploading material to a specific classroom."""
    try:
        creds = get_google_credentials()
        service = build("classroom", "v1", credentials=creds)

        results = service.courses().list(
            teacherId="me",
            courseStates=["ACTIVE"]
        ).execute()

        courses = results.get("courses", [])
        if not courses:
            return "No active classrooms found."

        course_list = "\n".join([
            f"- {c['name']} (ID: {c['id']})"
            for c in courses
        ])
        return f"Your active classrooms:\n{course_list}"
    except Exception as e:
        return f"Failed to list classrooms: {str(e)}"

@tool
def upload_material_to_classroom(
    course_id: str,
    title: str,
    file_path: str,
    description: str = ""
) -> str:
    """Upload course material to a specific Google Classroom.
    Use this when the teacher wants to share a file with students.
    First call list_classrooms to get the course_id."""
    try:
        creds = get_google_credentials()
        classroom_service = build("classroom", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)

        if not os.path.exists(file_path):
            return f"File not found: {file_path}"

        # upload to Drive first
        file_metadata = {"name": title}
        media = MediaFileUpload(file_path, resumable=True)
        drive_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        # attach to classroom
        material = {
            "title": title,
            "description": description,
            "materials": [
                {"driveFile": {"driveFile": {"id": drive_file.get("id")}}}
            ],
            "state": "PUBLISHED",
        }

        result = classroom_service.courses().courseWorkMaterials().create(
            courseId=course_id,
            body=material
        ).execute()

        return f"Material '{title}' uploaded to classroom ✓ Material ID: {result['id']}"
    except Exception as e:
        return f"Classroom upload failed: {str(e)}"