# Backend Integration Guide

This document outlines the FastAPI endpoints that need to be implemented or verified for full frontend compatibility.

## ✅ Already Implemented (Based on Your Repo)

### Authentication
- `POST /auth/register` - ✓ Implemented in `backend/server/routes/login_route.py`
- `POST /auth/login` - ✓ Implemented in `backend/server/routes/login_route.py`
- `GET /auth/me` - ✓ Implemented in `backend/server/auth/me.py`

### Lessons
- `POST /lessons/upload` - ✓ Implemented in `backend/server/routes/lessons_route.py`

## ❌ Needs Implementation

### Classes CRUD

**GET /classes**
```python
@router.get("/classes")
def get_classes(teacher: Dict[str, Any] = Depends(require_auth), session: Session = Depends(get_session)):
    """Fetch all classes for authenticated teacher"""
    classes = session.exec(
        select(Class).where(Class.teacher_id == teacher["id"])
    ).all()
    return {
        "success": True,
        "classes": [
            {
                "id": c.id,
                "name": c.name,
                "subject": c.subject,
                "period": c.period,
                "room": c.room,
                "school": c.school,
                "color": c.color,
                "created_at": c.created_at
            }
            for c in classes
        ]
    }
```

**POST /classes**
```python
class CreateClassRequest(BaseModel):
    name: str
    subject: Optional[str] = None
    period: Optional[str] = None
    room: Optional[str] = None
    school: Optional[str] = None
    color: Optional[str] = "#667eea"

@router.post("/classes")
def create_class(
    payload: CreateClassRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    """Create a new class"""
    new_class = Class(
        teacher_id=teacher["id"],
        name=payload.name,
        subject=payload.subject,
        period=payload.period,
        room=payload.room,
        school=payload.school,
        color=payload.color
    )
    session.add(new_class)
    session.commit()
    session.refresh(new_class)
    
    return {
        "success": True,
        "class": {
            "id": new_class.id,
            "name": new_class.name,
            "subject": new_class.subject,
            "period": new_class.period,
            "room": new_class.room,
            "school": new_class.school,
            "color": new_class.color,
            "created_at": new_class.created_at
        }
    }
```

**PUT /classes/{class_id}**
```python
@router.put("/classes/{class_id}")
def update_class(
    class_id: int,
    payload: CreateClassRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    """Update existing class"""
    cls = session.exec(
        select(Class).where(
            Class.id == class_id,
            Class.teacher_id == teacher["id"]
        )
    ).first()
    
    if not cls:
        raise AppError("CLASS_NOT_FOUND", "Class not found", 404)
    
    cls.name = payload.name
    cls.subject = payload.subject
    cls.period = payload.period
    cls.room = payload.room
    cls.school = payload.school
    cls.color = payload.color
    
    session.commit()
    session.refresh(cls)
    
    return {"success": True, "class": {...}}
```

**DELETE /classes/{class_id}**
```python
@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    """Delete a class"""
    cls = session.exec(
        select(Class).where(
            Class.id == class_id,
            Class.teacher_id == teacher["id"]
        )
    ).first()
    
    if not cls:
        raise AppError("CLASS_NOT_FOUND", "Class not found", 404)
    
    session.delete(cls)
    session.commit()
    
    return {"success": True, "message": "Class deleted"}
```

### Students (Future)

**GET /students?classId={id}**
```python
@router.get("/students")
def get_students(
    classId: Optional[int] = None,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    """Fetch students for a class or all students"""
    query = select(Student).join(Class).where(Class.teacher_id == teacher["id"])
    
    if classId:
        query = query.where(Student.class_id == classId)
    
    students = session.exec(query).all()
    return {"success": True, "students": [...]}
```

**POST /students**
```python
@router.post("/students")
def create_student(
    payload: CreateStudentRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    """Add a student to a class"""
    # Verify teacher owns the class
    # Create student record
    return {"success": True, "student": {...}}
```

### Attendance (Future)

**POST /attendance**
```python
@router.post("/attendance")
def mark_attendance(
    payload: MarkAttendanceRequest,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    """Mark student attendance"""
    # Implemented in backend/tools/attendance_tools.py
    # Needs route wrapper
    return {"success": True, "attendance": {...}}
```

**GET /attendance?classId={id}&date={date}**
```python
@router.get("/attendance")
def get_attendance(
    classId: int,
    date: Optional[str] = None,
    teacher: Dict[str, Any] = Depends(require_auth),
    session: Session = Depends(get_session)
):
    """Get attendance records"""
    return {"success": True, "attendance": [...]}
```

### Voice Processing (Future - Agent Integration)

**POST /voice/process**
```python
@router.post("/voice/process")
async def process_voice(
    audio: UploadFile = File(...),
    classId: int = Form(...),
    teacher: Dict[str, Any] = Depends(require_auth)
):
    """Process voice note and execute AI actions"""
    # 1. Transcribe audio (Whisper/Groq)
    # 2. Classify intent
    # 3. Execute tools via LangGraph agent
    # 4. Return structured results
    return {
        "success": True,
        "transcript": "...",
        "actions": [
            {"type": "attendance", "status": "completed", ...},
            {"type": "homework", "status": "completed", ...}
        ]
    }
```

## 📝 Database Models Required

Based on your schema, you need to create these SQLModel classes:

```python
# backend/server/db/dbModels.py

class Class(SQLModel, table=True):
    __tablename__ = "classes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(foreign_key="teachers.id")
    name: str = Field(max_length=100)
    period: Optional[str] = Field(default=None, max_length=50)
    room: Optional[str] = Field(default=None, max_length=50)
    subject: Optional[str] = Field(default=None, max_length=100)
    school: Optional[str] = Field(default=None, max_length=150)
    color: str = Field(default="#40916c", max_length=10)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Student(SQLModel, table=True):
    __tablename__ = "students"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="classes.id")
    name: str = Field(max_length=100)
    behavior: str = Field(default="Good", max_length=50)
    notes: str = Field(default="")
    parent_email: Optional[str] = Field(default=None, max_length=150)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Add Attendance, Grades, Homework, etc. as needed
```

## 🔄 Migration Steps

1. **Add Class model to dbModels.py**
2. **Run Alembic migration**: `python alembic/script.py "add classes table"`
3. **Create `/classes` route file**: `backend/server/routes/classes_route.py`
4. **Import and include router in** `backend/server/index.py`:
   ```python
   from backend.server.routes.classes_route import router as classes_router
   app.include_router(classes_router)
   ```
5. **Test endpoints** using the frontend

## ⚠️ Important Notes

- All endpoints must return standardized response format:
  ```json
  {
    "success": true,
    "data": {...}
  }
  ```
  Or on error:
  ```json
  {
    "success": false,
    "error": {
      "code": "ERROR_CODE",
      "message": "Human readable message"
    }
  }
  ```

- All protected routes must use `require_auth` dependency
- Database constraints should match the schema provided
- CORS must be enabled for `http://localhost:3000` in development

## 🧪 Testing

Use the frontend as an integration test:
1. Start backend: `uvicorn backend.server.index:app --reload`
2. Start frontend: `npm run dev`
3. Navigate to `http://localhost:3000`
4. Create account → Create class → Verify data in PostgreSQL

## 📚 References

- Your existing auth implementation: `backend/server/routes/login_route.py`
- Your database schema: `database/schema.sql`
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLModel docs: https://sqlmodel.tiangolo.com/