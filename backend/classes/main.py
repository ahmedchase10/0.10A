from typing import Any, Dict

from sqlmodel import Session, select

from backend.models import AppError
from backend.server.db.dbModels import Class


def _clean_text(value: str) -> str:
	return value.strip()


def create_teacher_class(
	session: Session,
	teacher_payload: Dict[str, Any],
	*,
	name: str,
	subject: str,
) -> Dict[str, Any]:
	teacher_id = int(teacher_payload["id"])
	clean_name = _clean_text(name)
	clean_subject = _clean_text(subject)

	if len(clean_name) < 2:
		raise AppError("CLASSES_INVALID_NAME", "Class name is too short.", 400)
	if len(clean_subject) < 2:
		raise AppError("CLASSES_INVALID_SUBJECT", "Subject is too short.", 400)

	existing = session.exec(
		select(Class).where(
			Class.teacher_id == teacher_id,
			Class.name == clean_name,
			Class.subject == clean_subject,
		)
	).first()
	if existing:
		raise AppError(
			"CLASSES_ALREADY_EXISTS",
			"Class already exists for this subject.",
			409,
		)

	class_record = Class(
		name=clean_name,
		subject=clean_subject,
		teacher_id=teacher_id,
	)
	session.add(class_record)
	session.commit()
	session.refresh(class_record)

	return {
		"success": True,
		"class": {
			"id": class_record.id,
			"name": class_record.name,
			"subject": class_record.subject,
			"teacher_id": class_record.teacher_id,
			"created_at": class_record.created_at,
		},
	}


def get_teacher_classes(
	session: Session,
	teacher_payload: Dict[str, Any],
) -> Dict[str, Any]:
	teacher_id = int(teacher_payload["id"])
	rows = session.exec(
		select(Class)
		.where(Class.teacher_id == teacher_id)
		.order_by(Class.created_at.desc())
	).all()

	return {
		"success": True,
		"classes": [
			{
				"id": row.id,
				"name": row.name,
				"subject": row.subject,
				"teacher_id": row.teacher_id,
				"created_at": row.created_at,
			}
			for row in rows
		],
	}

