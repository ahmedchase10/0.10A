from backend.tools.rag_tools import (
    search_course_material,
    generate_exam_from_material,
    generate_exercises_from_material,
    upload_pdf_to_platform,
)
from backend.tools.gmail_tools import (
    draft_email,
    send_email,
)
from backend.tools.classroom_tools import (
    list_classrooms,
    upload_material_to_classroom,
)
from backend.tools.attendance_tools import (
    update_attendance,
    get_attendance_report,
)

# all tools in one list for the agent
all_tools = [
    search_course_material,
    generate_exam_from_material,
    generate_exercises_from_material,
    upload_pdf_to_platform,
    draft_email,
    send_email,
    list_classrooms,
    upload_material_to_classroom,
    update_attendance,
    get_attendance_report,
]