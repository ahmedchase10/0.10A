import logging
from typing import Dict, List
from sqlmodel import Session, select, func
from datetime import datetime, timezone
from backend.server.db.dbModels import ExamTopicPerformance, CohortTopicInsight

logger = logging.getLogger(__name__)

SCOPE_RULES = {"DS": ["TD", "TP"], "EXAMEN": ["TD", "TP", "DS"]}
WEAK_THRESHOLD = 0.5
COHORT_WEAK_PCT_THRESHOLD = 0.6


def run_cohort_aggregation_for_class(session: Session, class_id: int, exam_type: str):
    allowed_types = SCOPE_RULES.get(exam_type, ["TD", "TP"])

    rows = session.exec(
        select(ExamTopicPerformance)
        .where(
            ExamTopicPerformance.class_id == class_id,  # 🔥 CRITICAL FILTER
            ExamTopicPerformance.exam_type.in_(allowed_types)
        )
    ).all()

    # Group by topic
    topic_data: Dict[str, List[Dict]] = {}
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
            sid = str(a["student_id"])  # Explicitly cast to string (hashable)
            if sid not in student_mastery:
                student_mastery[sid] = []
            student_mastery[sid].append(a["score"] / a["max_score"] if a["max_score"] > 0 else 0)

        avg_per_student = {sid: sum(scores) / len(scores) for sid, scores in student_mastery.items()}
        cohort_avg = sum(avg_per_student.values()) / len(avg_per_student) if avg_per_student else 0
        weak_pct = sum(1 for v in avg_per_student.values() if v < WEAK_THRESHOLD) / len(
            avg_per_student) if avg_per_student else 0

        if weak_pct >= COHORT_WEAK_PCT_THRESHOLD:
            insights_to_save.append(CohortTopicInsight(
                class_id=class_id,
                topic_id=topic_id,
                exam_type_scope=exam_type,
                cohort_avg_pct=round(cohort_avg * 100, 1),
                weak_student_pct=round(weak_pct * 100, 1),
                insight_type="cohort_topic_weakness",
                recommendation=f"Schedule a targeted review session on this topic. {round(weak_pct * 100)}% of the class is below 50% mastery.",
                updated_at=datetime.now(timezone.utc),
            ))

    if insights_to_save:
        # Upsert cohort insights
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


# backend/agents/insights/aggregator.py
import logging
from typing import Dict, List, Any
from sqlmodel import Session, select, func
from sqlalchemy import case

from backend.server.db.dbModels import ExamTopicPerformance, StudentTopicInsight

logger = logging.getLogger(__name__)

SCOPE_RULES = {
    "DS": ["TD", "TP"],
    "EXAMEN": ["TD", "TP", "DS"],
}

WEIGHTS = {"TD": 0.3, "TP": 0.3, "DS": 0.7, "EXAMEN": 1.0}
MIN_ATTEMPTS = 2
WEAK_THRESHOLD = 0.5
MASTER_THRESHOLD = 0.85


def run_aggregation_for_student(session: Session, student_id: str, latest_exam_type: str):
    """Compute mastery %, trends, and flag insights for a student."""
    allowed_types = SCOPE_RULES.get(latest_exam_type, ["TD", "TP"])

    # Fetch scoped performance rows
    rows = session.exec(
        select(ExamTopicPerformance)
        .where(
            ExamTopicPerformance.student_id == student_id,
            ExamTopicPerformance.exam_type.in_(allowed_types),
        )
        .order_by(ExamTopicPerformance.created_at)
    ).all()

    # Group by topic
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
        if len(attempts) < MIN_ATTEMPTS:
            continue

        # Weighted mastery
        weighted_sum = sum((a["score"] / a["max_score"]) * WEIGHTS.get(str(a["type"]), 0.3)for a in attempts if a["max_score"] > 0)
        weight_total = sum(WEIGHTS.get(str(a["type"]), 0.3)for a in attempts if a["max_score"] > 0)
        mastery_pct = (weighted_sum / weight_total) * 100 if weight_total > 0 else 0

        # Simple trend (last 2 attempts)
        trend = "stable"
        if len(attempts) >= 2:
            last2 = attempts[-2:]
            trend = "stable"
            if len(attempts) >= 2:
                last2 = [a for a in attempts[-2:] if a["max_score"] > 0]
                if len(last2) == 2:
                    delta = (last2[1]["score"] / last2[1]["max_score"]) - (last2[0]["score"] / last2[0]["max_score"])
                    trend = "improving" if delta > 0.05 else ("declining" if delta < -0.05 else "stable")

        # Flag insight type
        insight_type = None
        if mastery_pct < WEAK_THRESHOLD * 100:
            insight_type = "individual_consistent_struggle"
        elif mastery_pct >= MASTER_THRESHOLD * 100 and trend != "declining":
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