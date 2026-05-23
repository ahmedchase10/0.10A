from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.server.auth.dependencies import require_auth
from backend.server.db.engine import get_session
from backend.server.db.dbModels import (
    StudentTopicInsight, CohortTopicInsight, ExamTopicPerformance, StudentClass,
    Grade, ExamType, Flags, Student, ClassInsightConfig
)
from backend.classes.access import get_owned_class_or_403
from backend.agents.grading_agent.aggregator import (
    resolve_insight_config,
    run_aggregation_for_student,
    run_cohort_aggregation_for_class,
    DEFAULT_INSIGHT_CONFIG
)

router = APIRouter(prefix="/insights", tags=["insights"])


# Pydantic schema
class InsightConfigUpdate(BaseModel):
    weight_exercise: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_midterm: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_final: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_attempts: Optional[int] = Field(None, ge=1, le=10)
    weak_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    master_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    cohort_weak_pct: Optional[float] = Field(None, ge=0.0, le=1.0)
    scope_rules: Optional[Dict[str, List[str]]] = None


# Student Insights
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


# Cohort Insights
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


# Raw Exam Topic Performance
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


# Insight Configuration
@router.get("/classes/{class_id}/config")
def get_insight_config(
    class_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """Return resolved config + system defaults for UI rendering."""
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    resolved = resolve_insight_config(session, class_id)
    return {
        "success": True,
        "config": resolved,
        "defaults": DEFAULT_INSIGHT_CONFIG,
    }


@router.patch("/classes/{class_id}/config")
def update_insight_config(
    class_id: int,
    body: InsightConfigUpdate,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Partially update insight config. Null fields revert to defaults.
    Triggers synchronous recalculation of all student & cohort insights.
    """
    teacher_id = int(teacher["id"])
    get_owned_class_or_403(session, teacher_id=teacher_id, class_id=class_id)

    # Upsert config row
    cfg = session.exec(select(ClassInsightConfig).where(ClassInsightConfig.class_id == class_id)).first()
    if not cfg:
        cfg = ClassInsightConfig(class_id=class_id)
        session.add(cfg)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cfg, key, value)
    cfg.updated_at = datetime.now(timezone.utc)
    session.add(cfg)
    session.commit()

    # Recalculate student insights
    enrolled = session.exec(
        select(StudentClass.student_id).where(StudentClass.class_id == class_id)
    ).all()

    updated_students = 0
    for sid in enrolled:
        run_aggregation_for_student(session, str(sid), "FINAL", class_id)
        updated_students += 1

    # Recalculate cohort insights using canonical scope names
    for scope in ["MIDTERM", "FINAL"]:
        run_cohort_aggregation_for_class(session, class_id, scope)

    return {
        "success": True,
        "config": resolve_insight_config(session, class_id),
        "recalculated": {
            "students": updated_students,
            "cohort_scopes": ["MIDTERM", "FINAL"]
        }
    }