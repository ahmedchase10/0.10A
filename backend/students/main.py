from typing import Any, Dict

from sqlmodel import Session, select

from backend.models import AppError
from backend.server.db.dbModels import Class, Student, StudentClass


def _clean_text(value: str) -> str:
	return value.strip()


def get_class_students(
	session: Session,
	teacher_payload: Dict[str, Any],
	*,
	class_id: int,
) -> Dict[str, Any]:
	teacher_id = int(teacher_payload["id"])

	# Verify teacher owns the class
	class_record = session.exec(
		select(Class).where(
			Class.id == class_id,
			Class.teacher_id == teacher_id,
		)
	).first()
	if not class_record:
		raise AppError(
			"CLASSES_NOT_FOUND",
			"Class not found or you don't have permission to access it.",
			404,
		)

	# Get all students in the class
	student_class_records = session.exec(
		select(StudentClass, Student)
		.join(Student, StudentClass.student_id == Student.id)
		.where(StudentClass.class_id == class_id)
		.order_by(StudentClass.created_at.desc())
	).all()

	return {
		"success": True,
		"students": [
			{
				"id": student.id,
				"name": sc.name,
				"email": student.email,
				"created_at": sc.created_at,
			}
			for sc, student in student_class_records
		],
	}


def add_student(
	session: Session,
	teacher_payload: Dict[str, Any],
	*,
	class_id: int,
	name: str,
	email: str,
) -> Dict[str, Any]:
	teacher_id = int(teacher_payload["id"])
	clean_name = _clean_text(name)
	clean_email = _clean_text(email).lower()

	if len(clean_name) < 2:
		raise AppError("STUDENTS_INVALID_NAME", "Student name is too short.", 400)
	if len(clean_email) < 3 or "@" not in clean_email:
		raise AppError("STUDENTS_INVALID_EMAIL", "Invalid email address.", 400)

	# Verify teacher owns the class
	class_record = session.exec(
		select(Class).where(
			Class.id == class_id,
			Class.teacher_id == teacher_id,
		)
	).first()
	if not class_record:
		raise AppError(
			"CLASSES_NOT_FOUND",
			"Class not found or you don't have permission to access it.",
			404,
		)

	# Check if student with this email exists
	student_record = session.exec(
		select(Student).where(Student.email == clean_email)
	).first()

	# Create student if doesn't exist
	if not student_record:
		student_record = Student(
			name=clean_name,
			email=clean_email,
		)
		session.add(student_record)
		session.commit()
		session.refresh(student_record)

	# Check if student is already in this class
	existing_enrollment = session.exec(
		select(StudentClass).where(
			StudentClass.class_id == class_id,
			StudentClass.student_id == student_record.id,
		)
	).first()
	if existing_enrollment:
		raise AppError(
			"STUDENTS_ALREADY_ENROLLED",
			"Student is already enrolled in this class.",
			409,
		)

	# Add student to class
	student_class_record = StudentClass(
		class_id=class_id,
		student_id=student_record.id,
		name=clean_name,
	)
	session.add(student_class_record)
	session.commit()
	session.refresh(student_class_record)

	return {
		"success": True,
		"student": {
			"id": student_record.id,
			"name": student_class_record.name,
			"email": student_record.email,
			"created_at": student_class_record.created_at,
		},
	}


def remove_student(
	session: Session,
	teacher_payload: Dict[str, Any],
	*,
	student_id: int,
	class_id: int,
) -> Dict[str, Any]:
	teacher_id = int(teacher_payload["id"])

	# Verify teacher owns the class
	class_record = session.exec(
		select(Class).where(
			Class.id == class_id,
			Class.teacher_id == teacher_id,
		)
	).first()
	if not class_record:
		raise AppError(
			"CLASSES_NOT_FOUND",
			"Class not found or you don't have permission to access it.",
			404,
		)

	# Find the student enrollment
	student_class_record = session.exec(
		select(StudentClass).where(
			StudentClass.class_id == class_id,
			StudentClass.student_id == student_id,
		)
	).first()
	if not student_class_record:
		raise AppError(
			"STUDENTS_NOT_ENROLLED",
			"Student is not enrolled in this class.",
			404,
		)

	# Remove student from class
	session.delete(student_class_record)
	session.commit()

	return {
		"success": True,
		"message": "Student removed from class successfully.",
	}
