from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Any, Dict, List, Optional

from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session
from backend.server.db.dbModels import StudentTopicInsight, CohortTopicInsight, StudentClass
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