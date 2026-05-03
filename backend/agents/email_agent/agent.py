import os
from typing import List, Optional
from sqlmodel import Session, select
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.server.db.dbModels import Flags,StudentClass

# ─── LLM SETUP ────────────────────────────────────────────────────────────────
# Adjust model name if you pulled a different variant (e.g., qwen2.5:14b)
LLM_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.b")
llm = ChatOllama(model=LLM_MODEL, temperature=0.3)

# ─── OUTPUT SCHEMA ────────────────────────────────────────────────────────────
class EmailOutput(BaseModel):
    subject: str = Field(description="Professional, concise email subject line")
    body: str = Field(description="Full email body content, ready to send")

# ─── SYSTEM PROMPTS ───────────────────────────────────────────────────────────
SYSTEM_PROMPT_PARENT = """You are a professional, empathetic, and human-like email writer for teachers.
Your task is to write a clear, respectful, and constructive email to a student's parent.
Use the provided flags/context and teacher instructions to craft the email.
Maintain a professional yet warm tone. Avoid robotic, overly formal, or generic language.
Return ONLY a valid JSON object with "subject" and "body" keys. No markdown, no explanations, no extra text."""

SYSTEM_PROMPT_CUSTOM = """You are a professional, empathetic, and human-like email writer.
Your task is to write a clear, respectful, and well-structured email based on the teacher's instructions.
Maintain a professional yet warm tone. Avoid robotic, overly formal, or generic language.
Return ONLY a valid JSON object with "subject" and "body" keys. No markdown, no explanations, no extra text."""

# ─── CORE GENERATION LOGIC ────────────────────────────────────────────────────
def generate_email_service(
    session: Session,
    custom: bool,
    teacher_prompt: str,
    student_id: Optional[int] = None,
    class_id: Optional[int] = None,
    selected_flags: Optional[List[int]] = None,

) -> dict:
    """Stateless, single-turn email generation. No memory, no tools."""
    
    # 1️⃣ Fetch & format flags if not in custom mode
    flag_context = ""
    if not custom and student_id:
        stmt = select(Flags).where(Flags.student_id == student_id and Flags.class_id==class_id)
        if selected_flags:
            stmt = stmt.where(Flags.id.in_(selected_flags))
        
        flags = session.exec(stmt).all()
        if flags:
            flag_context = "\n".join([
                f"- {f.reason} (Recorded: {f.created_at.strftime('%Y-%m-%d')})"
                for f in flags
            ])
        else:
            flag_context = "No flags recorded for this student."

    # 2️⃣ Select system prompt based on mode
    system_prompt = SYSTEM_PROMPT_CUSTOM if custom else SYSTEM_PROMPT_PARENT

    # 3️⃣ Build user prompt
    user_parts = [f"Teacher Instructions: {teacher_prompt}"]
    if student_id:
        query= select(StudentClass.display_name).where(StudentClass.student_id == student_id and StudentClass.class_id == class_id)
        student_name=session.exec(query).first()
        user_parts.append(f"Student name: {student_name}")
    if flag_context:
        user_parts.append(f"Student Context/Flags:\n{flag_context}")
    
    user_prompt = "\n\n".join(user_parts) + "\n\nGenerate the email now. Return ONLY valid JSON."

    # 4️⃣ Build & invoke chain (stateless, linear)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ])

    chain = prompt | llm.with_structured_output(EmailOutput)
    
    try:
        result = chain.invoke({})
        return result.model_dump()
    except Exception as e:
        raise RuntimeError(f"LLM generation failed. Ensure Ollama is running with model '{LLM_MODEL}'. Error: {e}")