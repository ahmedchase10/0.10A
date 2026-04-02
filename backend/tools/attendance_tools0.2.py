# =============================================
# DIGI-SCHOOL AI — Attendance Tools
# These are the functions the LangGraph agent
# calls as tools to read/write attendance data.
# =============================================

import psycopg2
import psycopg2.extras
import requests
from datetime import date
from typing import Optional
from langchain_core.tools import tool

from backend.config import DB_CONFIG, EXPRESS_API_URL


# ─── DB helper ───────────────────────────────

def _get_conn():
    """Open a fresh psycopg2 connection."""
    return psycopg2.connect(**DB_CONFIG)


# ─── Tool 1: get_students_for_class ──────────

@tool
def get_students_for_class(class_name: str, teacher_id: int) -> list[dict]:
    """
    Fetch all students belonging to a class by class name.
    Use this when you need to resolve student names or IDs for a given class.

    Args:
        class_name: The name of the class, e.g. '3G' or '3G — English'
        teacher_id: The ID of the authenticated teacher

    Returns:
        List of students with their id, name, class_id, class_name
    """
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT s.id, s.name, s.class_id, c.name AS class_name
                FROM students s
                JOIN classes c ON c.id = s.class_id
                WHERE c.teacher_id = %s
                  AND (c.name ILIKE %s OR c.name ILIKE %s)
                ORDER BY s.name ASC
            """, (teacher_id, f"%{class_name}%", class_name))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()


# ─── Tool 2: get_today_attendance ────────────

@tool
def get_today_attendance(teacher_id: int) -> list[dict]:
    """
    Fetch attendance records already marked today for all of this teacher's classes.
    Use this to check what has already been recorded before marking new attendance.

    Args:
        teacher_id: The ID of the authenticated teacher

    Returns:
        List of attendance records for today
    """
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT a.student_id, a.status, a.date,
                       s.name AS student_name,
                       c.id   AS class_id,
                       c.name AS class_name
                FROM attendance a
                JOIN students s ON s.id = a.student_id
                JOIN classes  c ON c.id = a.class_id
                WHERE c.teacher_id = %s
                  AND a.date = CURRENT_DATE
                ORDER BY c.name, s.name
            """, (teacher_id,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()


# ─── Tool 3: mark_attendance ─────────────────

@tool
def mark_attendance(
    student_id:   int,
    class_id:     int,
    status:       str,
    date_str:     Optional[str] = None,
    teacher_id:   int = 0,
    jwt_token:    str = "",
) -> dict:
    """
    Mark a student's attendance status for a given date.
    Status must be one of: P (Present), A (Absent), L (Late), E (Excused).
    If date_str is not provided, today's date is used.

    Args:
        student_id:  The student's database ID
        class_id:    The class database ID
        status:      One of 'P', 'A', 'L', 'E'
        date_str:    ISO date string e.g. '2026-03-30'. Defaults to today.
        teacher_id:  Teacher ID (used for logging)
        jwt_token:   JWT bearer token to call the Node.js API

    Returns:
        Dict with 'success' bool and 'message' string
    """
    if status not in ("P", "A", "L", "E"):
        return {"success": False, "message": f"Invalid status '{status}'. Use P, A, L, or E."}

    target_date = date_str or date.today().isoformat()

    # Call Node.js attendance API so it goes through the same validation layer
    try:
        response = requests.post(
            f"{EXPRESS_API_URL}/attendance",
            json={
                "studentId": student_id,
                "classId":   class_id,
                "date":      target_date,
                "status":    status,
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
            timeout=5,
        )
        response.raise_for_status()
        return {"success": True, "message": f"Marked student {student_id} as {status} on {target_date}"}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"API error: {str(e)}"}


# ─── Tool 4: flag_student ────────────────────

@tool
def flag_student(
    student_id:  int,
    class_id:    int,
    flag_type:   str,
    reason:      str,
    jwt_token:   str = "",
) -> dict:
    """
    Flag a student for behavior, absence, or grade concerns.
    Use this when a teacher mentions repeated issues or threshold breaches.

    Args:
        student_id:  The student's database ID
        class_id:    The class database ID
        flag_type:   One of 'behavior', 'absence', 'grade'
        reason:      Human-readable reason for the flag
        jwt_token:   JWT bearer token to call the Node.js API

    Returns:
        Dict with 'success' bool and 'message' string
    """
    if flag_type not in ("behavior", "absence", "grade"):
        return {"success": False, "message": f"Invalid flag type '{flag_type}'."}

    try:
        response = requests.post(
            f"{EXPRESS_API_URL}/flagged",
            json={
                "studentId": student_id,
                "classId":   class_id,
                "type":      flag_type,
                "reason":    reason,
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
            timeout=5,
        )
        response.raise_for_status()
        return {"success": True, "message": f"Flagged student {student_id} for {flag_type}: {reason}"}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"API error: {str(e)}"}


# ─── Tool 5: check_absence_threshold ─────────

@tool
def check_absence_threshold(student_id: int, threshold: int = 5) -> dict:
    """
    Check how many times a student has been absent this month.
    Use this to decide whether to automatically flag a student for absences.

    Args:
        student_id: The student's database ID
        threshold:  Number of absences that triggers a flag (default 5)

    Returns:
        Dict with 'absence_count', 'exceeds_threshold', 'student_id'
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM attendance
                WHERE student_id = %s
                  AND status = 'A'
                  AND date >= DATE_TRUNC('month', CURRENT_DATE)
            """, (student_id,))
            count = cur.fetchone()[0]
            return {
                "student_id":        student_id,
                "absence_count":     count,
                "exceeds_threshold": count >= threshold,
            }
    finally:
        conn.close()