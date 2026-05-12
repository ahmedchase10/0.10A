import logging
from typing import List, Dict, Any
from sqlmodel import Session, select
from datetime import datetime, timezone

from backend.server.db.dbModels import ExamTopicPerformance, StudentTopicInsight
from backend.agents.grading_agent.aggregator import run_aggregation_for_student

logger = logging.getLogger(__name__)

def save_grading_and_trigger_insights(
    session: Session,
    exam_id: str,
    student_id: str,
    class_id: int,
    exam_type: str,
    breakdown: List[Dict[str, Any]],
) -> Dict[str, Any]:
    inserted = 0
    for q in breakdown:
        topic_id = q.get("topic_id", "unmapped")
        if topic_id == "unmapped":
            logger.warning("Skipping unmapped question %s for exam %s", q.get("question_number"), exam_id)
            continue

        row = ExamTopicPerformance(
            exam_id=exam_id,
            student_id=student_id,
            class_id=class_id,  # 🔥 Use passed class_id directly
            exam_type=exam_type,
            topic_id=topic_id,
            score=float(q.get("awarded_points", 0)),
            max_score=float(q.get("max_points", 0)),
            feedback=q.get("reasoning", ""),
            created_at=datetime.now(timezone.utc),
        )
        session.add(row)
        inserted += 1

    session.commit()
    logger.info("Saved %d topic performance rows for student %s, exam %s", inserted, student_id, exam_id)

    # Trigger student-level aggregation
    run_aggregation_for_student(session, student_id, exam_type, class_id)

    return {"success": True, "rows_inserted": inserted}