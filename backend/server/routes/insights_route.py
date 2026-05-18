from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Any, Dict, List, Optional

from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session
from backend.server.db.dbModels import (
    StudentTopicInsight, CohortTopicInsight, ExamTopicPerformance, StudentClass,
    Grade, ExamType, Flags, Student
)
from backend.classes.access import get_owned_class_or_403

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/students")
def get_student_insights(
    class_id: int = Query(...),
    student_id: Optional[int] = Query(None),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """Fetch per-student topic insights for a class (or single student)."""
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    # Get enrolled student IDs (cast to str to match insight table)
    enrolled = session.exec(
        select(StudentClass.student_id).where(StudentClass.class_id == class_id)
    ).all()
    enrolled_str = [str(sid) for sid in enrolled]

    query = select(StudentTopicInsight).where(
        StudentTopicInsight.student_id.in_(enrolled_str)
    )
    if student_id is not None:
        query = query.where(StudentTopicInsight.student_id == str(student_id))

    rows = session.exec(
        query.order_by(StudentTopicInsight.student_id, StudentTopicInsight.topic_id)
    ).all()

    return {
        "success": True,
        "insights": [
            {
                "student_id": int(r.student_id),
                "topic_id": r.topic_id,
                "mastery_pct": r.mastery_pct,
                "attempts": r.attempts,
                "trend": r.trend,
                "insight_type": r.insight_type,
                "updated_at": r.updated_at,
            }
            for r in rows
        ],
    }


@router.get("/cohort")
def get_cohort_insights(
    class_id: int = Query(...),
    exam_type_scope: Optional[str] = Query(None),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """Fetch class-wide topic insights & remediation recommendations."""
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    query = select(CohortTopicInsight).where(CohortTopicInsight.class_id == class_id)
    if exam_type_scope:
        query = query.where(CohortTopicInsight.exam_type_scope == exam_type_scope)

    # Sort by weakest topics first for immediate teacher attention
    rows = session.exec(query.order_by(CohortTopicInsight.weak_student_pct.desc())).all()

    return {
        "success": True,
        "insights": [
            {
                "topic_id": r.topic_id,
                "exam_type_scope": r.exam_type_scope,
                "cohort_avg_pct": r.cohort_avg_pct,
                "weak_student_pct": r.weak_student_pct,
                "insight_type": r.insight_type,
                "recommendation": r.recommendation,
                "updated_at": r.updated_at,
            }
            for r in rows
        ],
    }


@router.get("/report")
def get_student_report(
    class_id: int = Query(...),
    student_id: int = Query(...),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Comprehensive per-student academic report for a given class.
    Returns: grades (per exam type), topic insights, flags, and summary stats.
    """
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    # ── Verify student is enrolled ────────────────────────────────────────────
    enrollment = session.exec(
        select(StudentClass, Student)
        .join(Student, StudentClass.student_id == Student.id)
        .where(
            StudentClass.class_id == class_id,
            StudentClass.student_id == student_id,
        )
    ).first()

    if not enrollment:
        from backend.models import AppError
        raise AppError("STUDENT_NOT_ENROLLED", "Student not enrolled in this class.", 404)

    student_class, student = enrollment

    # ── Grades ────────────────────────────────────────────────────────────────
    grade_rows = session.exec(
        select(Grade, ExamType)
        .join(ExamType, ExamType.id == Grade.exam_type_id)
        .where(
            Grade.student_id == student_id,
            ExamType.class_id == class_id,
        )
        .order_by(ExamType.category, ExamType.name)
    ).all()

    grades = [
        {
            "exam_type_id": et.id,
            "exam_type_name": et.name,
            "category": et.category,
            "value": g.value,
        }
        for g, et in grade_rows
    ]

    # ── Summary stats ─────────────────────────────────────────────────────────
    all_values = [g["value"] for g in grades]
    ds_values  = [g["value"] for g in grades if g["category"] == "DS"]
    ex_values  = [g["value"] for g in grades if g["category"] == "EXAMEN"]

    def _avg(vals):
        return round(sum(vals) / len(vals), 2) if vals else None

    summary = {
        "overall_average": _avg(all_values),
        "ds_average": _avg(ds_values),
        "exam_average": _avg(ex_values),
        "total_exams": len(grades),
        "grades_below_10": sum(1 for v in all_values if v < 10),
        "grades_above_14": sum(1 for v in all_values if v >= 14),
    }

    # ── Topic insights ────────────────────────────────────────────────────────
    insight_rows = session.exec(
        select(StudentTopicInsight).where(
            StudentTopicInsight.student_id == str(student_id)
        ).order_by(StudentTopicInsight.mastery_pct)
    ).all()

    insights = [
        {
            "topic_id": r.topic_id,
            "mastery_pct": r.mastery_pct,
            "attempts": r.attempts,
            "trend": r.trend,
            "insight_type": r.insight_type,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in insight_rows
    ]

    weak_topics   = [i for i in insights if i["mastery_pct"] < 50]
    strong_topics = [i for i in insights if i["mastery_pct"] >= 75]
    declining     = [i for i in insights if i["trend"] == "declining"]

    # ── Flags ─────────────────────────────────────────────────────────────────
    flag_rows = session.exec(
        select(Flags).where(
            Flags.class_id == class_id,
            Flags.student_id == student_id,
        ).order_by(Flags.created_at.desc())
    ).all()

    flags = [
        {
            "id": f.id,
            "reason": f.reason,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in flag_rows
    ]

    return {
        "success": True,
        "report": {
            "student": {
                "id": student.id,
                "name": student_class.display_name,
                "email": student.email,
            },
            "summary": summary,
            "grades": grades,
            "insights": {
                "all": insights,
                "weak_topics": weak_topics,
                "strong_topics": strong_topics,
                "declining_topics": declining,
            },
            "flags": flags,
        },
    }


@router.get("/exam-topic")
def get_exam_topic_performance(
    class_id: int = Query(...),
    exam_id: Optional[str] = Query(None),
    student_id: Optional[int] = Query(None),
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Raw per-student, per-topic scores from exam corrections.
    Optionally filter by exam_id or student_id.
    Returns rows from exam_topic_performance for the given class.
    """
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    query = select(ExamTopicPerformance).where(
        ExamTopicPerformance.class_id == class_id
    )
    if exam_id is not None:
        query = query.where(ExamTopicPerformance.exam_id == exam_id)
    if student_id is not None:
        query = query.where(ExamTopicPerformance.student_id == str(student_id))

    rows = session.exec(
        query.order_by(
            ExamTopicPerformance.exam_id,
            ExamTopicPerformance.student_id,
            ExamTopicPerformance.topic_id,
        )
    ).all()

    # Build a summary: for each topic across all students, aggregate avg score
    topic_map: Dict[str, Dict] = {}
    for r in rows:
        key = r.topic_id
        if key not in topic_map:
            topic_map[key] = {
                "topic_id": r.topic_id,
                "exam_type": r.exam_type,
                "scores": [],
                "max_score": r.max_score,
            }
        topic_map[key]["scores"].append(r.score)

    topic_summary = []
    for t in topic_map.values():
        scores = t["scores"]
        avg = round(sum(scores) / len(scores), 2) if scores else 0.0
        pct = round((avg / t["max_score"]) * 100, 1) if t["max_score"] else 0.0
        topic_summary.append({
            "topic_id": t["topic_id"],
            "exam_type": t["exam_type"],
            "avg_score": avg,
            "max_score": t["max_score"],
            "avg_pct": pct,
            "student_count": len(scores),
        })

    topic_summary.sort(key=lambda x: x["avg_pct"])

    return {
        "success": True,
        "rows": [
            {
                "exam_id": r.exam_id,
                "student_id": int(r.student_id),
                "class_id": r.class_id,
                "exam_type": r.exam_type,
                "topic_id": r.topic_id,
                "score": r.score,
                "max_score": r.max_score,
                "pct": round((r.score / r.max_score) * 100, 1) if r.max_score else 0.0,
                "feedback": r.feedback,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "topic_summary": topic_summary,
    }