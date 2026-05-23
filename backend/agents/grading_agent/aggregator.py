import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

from sqlmodel import Session, select
from backend.server.db.dbModels import ExamTopicPerformance, StudentTopicInsight, ExamType, CohortTopicInsight

logger = logging.getLogger(__name__)

from backend.server.db.dbModels import ClassInsightConfig

DEFAULT_INSIGHT_CONFIG = {
    "weight_exercise": 0.3, "weight_midterm": 0.7, "weight_final": 1.0,
    "min_attempts": 2, "weak_threshold": 0.5, "master_threshold": 0.85,
    "cohort_weak_pct": 0.6,
    "scope_rules": {"MIDTERM": ["EXERCISE"], "FINAL": ["EXERCISE", "MIDTERM"]}
}

def resolve_insight_config(session: Session, class_id: int) -> dict:
    cfg = session.exec(select(ClassInsightConfig).where(ClassInsightConfig.class_id == class_id)).first()
    resolved = dict(DEFAULT_INSIGHT_CONFIG)
    if cfg:
        for key in DEFAULT_INSIGHT_CONFIG:
            val = getattr(cfg, key, None)
            if val is not None:
                resolved[key] = val
    return resolved


def run_cohort_aggregation_for_class(session: Session, class_id: int, exam_type: str):
    cfg = resolve_insight_config(session, class_id)
    base_allowed = cfg["scope_rules"].get(exam_type, ["EXERCISE"])

    enabled_categories = session.exec(
        select(ExamType.category).where(
            ExamType.class_id == class_id,
            ExamType.category.in_(base_allowed),
            ExamType.use_for_insights == True
        )
    ).all()
    allowed_categories = list(set(enabled_categories))

    if not allowed_categories:
        logger.info("No exam types enabled for cohort insights in this scope. Skipping.")
        return

    rows = session.exec(
        select(ExamTopicPerformance)
        .where(
            ExamTopicPerformance.class_id == class_id,
            ExamTopicPerformance.exam_type.in_(allowed_categories)
        )
    ).all()

    # Group by topic
    topic_data: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        topic_data.setdefault(r.topic_id, []).append({
            "student_id": r.student_id,
            "score": r.score,
            "max_score": r.max_score,
        })

    insights_to_save = []
    for topic_id, attempts in topic_data.items():
        if not attempts:
            continue

        # Compute per-student mastery for this topic
        student_mastery: Dict[str, List[float]] = {}
        for a in attempts:
            sid = str(a["student_id"])
            if a["max_score"] > 0:
                student_mastery.setdefault(sid, []).append(a["score"] / a["max_score"])

        if not student_mastery:
            continue

        avg_per_student = {sid: sum(scores) / len(scores) for sid, scores in student_mastery.items()}
        cohort_avg = sum(avg_per_student.values()) / len(avg_per_student)
        weak_pct = sum(1 for v in avg_per_student.values() if v < cfg["weak_threshold"]) / len(avg_per_student)

        if weak_pct >= cfg["cohort_weak_pct"]:
            insights_to_save.append(CohortTopicInsight(
                class_id=class_id,
                topic_id=topic_id,
                exam_type_scope=exam_type,
                cohort_avg_pct=round(cohort_avg * 100, 1),
                weak_student_pct=round(weak_pct * 100, 1),
                insight_type="cohort_topic_weakness",
                recommendation=f"Schedule a targeted review session on this topic. {round(weak_pct * 100)}% of the class is below {round(cfg['weak_threshold'] * 100)}% mastery.",
                updated_at=datetime.now(timezone.utc),
            ))

    if insights_to_save:
        for ins in insights_to_save:
            existing = session.exec(
                select(CohortTopicInsight).where(
                    CohortTopicInsight.class_id == ins.class_id,
                    CohortTopicInsight.topic_id == ins.topic_id,
                    CohortTopicInsight.exam_type_scope == ins.exam_type_scope,
                )
            ).first()
            if existing:
                existing.cohort_avg_pct = ins.cohort_avg_pct
                existing.weak_student_pct = ins.weak_student_pct
                existing.insight_type = ins.insight_type
                existing.recommendation = ins.recommendation
                existing.updated_at = ins.updated_at
            else:
                session.add(ins)
        session.commit()
        logger.info("Generated %d cohort insights for class %s", len(insights_to_save), class_id)


def run_aggregation_for_student(session: Session, student_id: str, latest_exam_type: str, class_id: int):
    """Compute mastery %, trends, and flag insights for a student."""
    cfg = resolve_insight_config(session, class_id)
    base_allowed = cfg["scope_rules"].get(latest_exam_type, ["EXERCISE"])

    weight_map = {
        "EXERCISE": cfg["weight_exercise"],
        "MIDTERM": cfg["weight_midterm"],
        "FINAL": cfg["weight_final"]
    }

    enabled_categories = session.exec(
        select(ExamType.category).where(
            ExamType.class_id == class_id,
            ExamType.category.in_(base_allowed),
            ExamType.use_for_insights == True
        )
    ).all()
    allowed_categories = list(set(enabled_categories))

    if not allowed_categories:
        logger.info("No exam types enabled for insights in this scope. Skipping aggregation.")
        return

    rows = session.exec(
        select(ExamTopicPerformance)
        .where(
            ExamTopicPerformance.student_id == student_id,
            ExamTopicPerformance.exam_type.in_(allowed_categories),
        )
        .order_by(ExamTopicPerformance.created_at)
    ).all()

    topic_data: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        topic_data.setdefault(r.topic_id, []).append({
            "score": r.score,
            "max_score": r.max_score,
            "type": r.exam_type,
            "created_at": r.created_at,
        })

    insights_to_save = []
    for topic_id, attempts in topic_data.items():
        if len(attempts) < cfg["min_attempts"]:
            continue

        weighted_sum = sum(
            (a["score"] / a["max_score"]) * weight_map.get(str(a["type"]), cfg["weight_exercise"])
            for a in attempts if a["max_score"] > 0
        )
        weight_total = sum(
            weight_map.get(str(a["type"]), cfg["weight_exercise"])
            for a in attempts if a["max_score"] > 0
        )
        mastery_pct = (weighted_sum / weight_total) * 100 if weight_total > 0 else 0

        trend = "stable"
        if len(attempts) >= 2:
            last2 = [a for a in attempts[-2:] if a["max_score"] > 0]
            if len(last2) == 2:
                delta = (last2[1]["score"] / last2[1]["max_score"]) - (last2[0]["score"] / last2[0]["max_score"])
                trend = "improving" if delta > 0.05 else ("declining" if delta < -0.05 else "stable")

        insight_type = None
        if mastery_pct < cfg["weak_threshold"] * 100:
            insight_type = "individual_consistent_struggle"
        elif mastery_pct >= cfg["master_threshold"] * 100 and trend != "declining":
            insight_type = "mastery_achieved"
        elif trend == "declining":
            insight_type = "performance_decline"

        if insight_type:
            insights_to_save.append(StudentTopicInsight(
                student_id=student_id,
                topic_id=topic_id,
                mastery_pct=round(mastery_pct, 1),
                attempts=len(attempts),
                trend=trend,
                insight_type=insight_type,
                updated_at=datetime.now(timezone.utc),
            ))

    if insights_to_save:
        for ins in insights_to_save:
            existing = session.exec(
                select(StudentTopicInsight).where(
                    StudentTopicInsight.student_id == student_id,
                    StudentTopicInsight.topic_id == ins.topic_id
                )
            ).first()
            if existing:
                existing.mastery_pct = ins.mastery_pct
                existing.attempts = ins.attempts
                existing.trend = ins.trend
                existing.insight_type = ins.insight_type
                existing.updated_at = ins.updated_at
            else:
                session.add(ins)
        session.commit()
        logger.info("Generated %d insights for student %s", len(insights_to_save), student_id)