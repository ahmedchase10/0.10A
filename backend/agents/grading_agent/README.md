# Grading Agent — Full Architecture & Implementation Plan

> **Status**: Phase 1 (blueprint/analyse) ✅ implemented.  
> Phase 2 (student grading queue) redesign ⚙️ in progress.  
> Use this document as the single source of truth when resuming.

---

## Table of Contents
1. [Overview](#overview)
2. [Data Models](#data-models)
3. [File Storage Layout](#file-storage-layout)
4. [API Endpoints — Full Reference](#api-endpoints)
5. [LangGraph Architecture](#langgraph-architecture)
6. [Phase 1: Blueprint / Analyse](#phase-1-blueprint--analyse)
7. [Phase 2: Student Grading Queue](#phase-2-student-grading-queue)
8. [SSE Event Reference](#sse-event-reference)
9. [Key Design Decisions](#key-design-decisions)
10. [Outstanding TODO List](#outstanding-todo-list)

---

## Overview

The grading agent is a **two-phase system**:

```
Phase 1 — Blueprint Creation
  Teacher uploads exam paper (class-scoped) →
  Teacher selects: exam paper + lessons (RAG) + optional correction PDF + preferences →
  Agent reads everything, understands grading criteria →
  LangGraph checkpoint suspended = THE BLUEPRINT (stored in Postgres)
  Correction PDF deleted from disk after analysis (one-time artifact)

Phase 2 — Student Grading Queue
  Teacher selects blueprint + class + exam type →
  Teacher submits {student_id → exam_pdf} pairs →
  Backend saves PDFs permanently, creates ordered GradingSession queue →
  For each student (one at a time, sequential):
    Fork blueprint checkpoint → student thread (agent starts fresh from blueprint)
    Stream grading → question_result events → interrupt event
    Teacher reviews: sees why each question got its mark
    Teacher approves / edits individual question scores / cancels (skip)
    Grade saved to DB → next_session_id returned → repeat
```

The blueprint is **NOT** a JSON column. It is the **suspended LangGraph checkpoint** saved in Postgres after Phase 1. Forking it (SQL copy) for each student means the agent already has the full exam context and only needs to read one student's paper.

---

## Data Models

### `ExamPaper` (NEW — to be added)
**Class-scoped.** Teacher uploads the exam question paper for a class. Separate from student answer PDFs.

```
exam_papers
  id           : int PK
  class_id     : FK → classes.id  (INDEX)
  teacher_id   : FK → teachers.id (INDEX, for fast teacher-owned queries)
  filename     : str (max 255)
  file_path    : str (max 512)   — uploads/exam_papers/{teacher_id}/{uuid}.pdf
  file_hash    : str (sha256, max 64)
  size         : int
  created_at   : datetime

UNIQUE CONSTRAINT: (class_id, file_hash)  — no duplicate papers in same class
```

**Deduplication on delete**: when deleting an `ExamPaper` row, only unlink the actual file from disk if **no other** `ExamPaper` row references the same `file_hash` across ALL classes. This handles teachers who teach the same exam to multiple classes.

### `GradingBlueprint` (EXISTS — minor update)
**Teacher-scoped. Reusable across classes.** One teacher might use the same blueprint for Class 5A and 5B.

```
grading_blueprints
  id                  : int PK
  teacher_id          : FK → teachers.id
  title               : str (max 120)         — e.g. "Correction Exam 1 – 2026"
  analysis_thread_id  : str (uuid)            — LangGraph thread ID = the blueprint checkpoint
  exam_paper_id       : int FK → exam_papers.id  NULLABLE  ← NEW (display only; agent uses path)
  exam_file_path      : str (max 512)         — absolute path used by agent (survives exam paper deletion)
  correction_file_path: str NULLABLE          — deleted from disk after analysis; kept as null after
  lesson_doc_ids      : str (JSON array)      — Upload UUIDs used in RAG
  preferences         : str                   — when to deduct points, point allocation, etc.
  style_guide         : str                   — math / essay / structured answer formatting
  blueprint_json      : str                   — structured Q/criteria summary (display only)
  deleted             : bool (default False)  — soft-delete; checkpoint hard-deleted on /delete
  created_at          : datetime
```

### `ExamUpload` (EXISTS — internal only)
**Student answer PDFs.** Created internally by `POST /grade`. Never exposed as a separate upload endpoint. Teacher never references ExamUpload IDs directly.

```
exam_uploads
  id          : str (uuid) PK
  teacher_id  : FK → teachers.id
  filename    : str (max 255)
  file_path   : str (max 512)   — uploads/exams/{teacher_id}/{uuid}.pdf
  file_hash   : str (sha256)
  size        : int
  created_at  : datetime
```

### `GradingSession` (EXISTS — add `queue_position`)
**One per student per batch run.**

```
grading_sessions
  id              : str (uuid) PK
  blueprint_id    : FK → grading_blueprints.id
  class_id        : FK → classes.id
  exam_type_id    : FK → exam_types.id
  student_id      : FK → students.id
  exam_upload_id  : FK → exam_uploads.id
  thread_id       : str (uuid)    — LangGraph checkpoint for this student's session
  batch_id        : str (uuid)    — groups all sessions from one /grade call
  queue_position  : int           ← NEW — sort order within batch (alphabetical by student name)
  status          : str           — pending | reviewing | approved | cancelled
  created_at      : datetime
```

### `GradingQuestionResult` (EXISTS — unchanged)
Written when teacher approves/edits a session.

```
grading_question_results
  id               : int PK
  session_id       : FK → grading_sessions.id
  question_number  : int
  question_label   : str (max 20)   — e.g. "Q1a"
  max_points       : float
  awarded_points   : float          — final value (teacher_override if edited)
  reasoning        : str            — agent's explanation for this mark
  teacher_override : bool           — True if teacher changed the agent's score
```

---

## File Storage Layout

```
uploads/
  exam_papers/
    {teacher_id}/
      {uuid}.pdf          ← ExamPaper files (class-scoped but stored by teacher)
  exams/
    {teacher_id}/
      {uuid}.pdf          ← Student answer PDFs (ExamUpload rows)
      corrections/
        {uuid}.pdf        ← Correction PDFs (DELETED after analysis — never stays)
```

---

## API Endpoints

### Exam Papers (class-scoped)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents/grading/exam-papers` | Upload exam paper PDF for a class |
| `GET` | `/agents/grading/exam-papers?class_id=` | List exam papers for a class |
| `DELETE` | `/agents/grading/exam-papers/{id}` | Delete; smart file unlink (check other classes) |

**POST /exam-papers** — `multipart/form-data`:
```
class_id : int  (Form)
file     : PDF  (File)
```
Returns:
```json
{
  "success": true,
  "exam_paper": { "id": 1, "filename": "...", "size": 0, "created_at": "..." },
  "duplicate": false
}
```

---

### Blueprints (teacher-scoped)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents/grading/analyse` | Phase 1: create blueprint (SSE) |
| `GET` | `/agents/grading/blueprints` | List teacher's blueprints |
| `GET` | `/agents/grading/blueprints/{id}` | Get single blueprint |
| `DELETE` | `/agents/grading/blueprints/{id}` | Soft-delete + hard-delete checkpoint |

**POST /analyse** — `multipart/form-data`:
```
exam_paper_id   : int   (Form)      — from /exam-papers
lesson_file_ids : str   (Form)      — JSON array of Upload UUIDs
correction_pdf  : PDF   (File, opt) — deleted from disk after analysis
preferences     : str   (Form, opt) — grading criteria (when to deduct, etc.)
style_guide     : str   (Form, opt) — math/essay formatting expectations
title           : str   (Form)      — "Correction Exam 1 – 2026"
reasoning       : bool  (Form)      — enable LLM thinking mode
```
SSE events: `thinking`, `content`, `tool_call`, `tool_result`, `blueprint_ready`, `blueprint_saved`, `error`, `done`

**blueprint_saved** payload:
```json
{ "blueprint_id": 1, "title": "Correction Exam 1 – 2026" }
```

---

### Grading Sessions (Phase 2)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents/grading/grade` | Create batch of grading sessions |
| `GET` | `/agents/grading/sessions` | List sessions (filter by batch_id / class_id / blueprint_id) |
| `GET` | `/agents/grading/sessions/{id}/stream` | SSE: grade one student |
| `POST` | `/agents/grading/sessions/{id}/review` | Teacher approves/edits/cancels → grade saved |

**POST /grade** — `multipart/form-data`:
```
blueprint_id  : int               (Form)
class_id      : int               (Form)
exam_type_id  : int               (Form)
student_ids   : int[]             (Form, repeated) — one per student
exam_pdfs     : PDF[]             (File, repeated) — SAME index = same student
```
Backend:
1. Validates all student_ids belong to class
2. Zips `(student_id, pdf)` pairs — indices must match
3. Fetches student names from DB
4. Sorts pairs **alphabetically by student name**
5. Saves each PDF permanently to `uploads/exams/{teacher_id}/`
6. Creates `ExamUpload` + `GradingSession` rows with `queue_position` = sorted order

Returns:
```json
{
  "success": true,
  "batch_id": "uuid",
  "first_session_id": "uuid",
  "sessions": [
    { "session_id": "uuid", "student_id": 1, "student_name": "Alice", "queue_position": 0 },
    { "session_id": "uuid", "student_id": 2, "student_name": "Bob",   "queue_position": 1 }
  ]
}
```

**GET /sessions/{id}/stream** — SSE:
- Forks blueprint checkpoint → student thread (idempotent SQL copy)
- Resumes grading graph with student exam path
- Streams: `thinking`, `content`, `tool_call`, `tool_result`, `question_result`, `interrupt`, `error`, `done`
- Query param: `force_restart=true` to re-run a crashed session

**question_result** event (one per question):
```json
{
  "type": "question_result",
  "question_number": 1,
  "label": "Q1",
  "max_points": 4.0,
  "awarded_points": 3.0,
  "reasoning": "Identified X correctly but missed Y (-1pt)."
}
```

**interrupt** event (grading complete, waiting for teacher):
```json
{
  "type": "interrupt",
  "breakdown": [
    { "question_number": 1, "label": "Q1", "max_points": 4.0, "awarded_points": 3.0, "reasoning": "..." }
  ]
}
```

**POST /sessions/{id}/review** — JSON body:
```json
{
  "decisions": [
    { "question_number": 1, "awarded_points": 3.0 },
    { "question_number": 2, "awarded_points": 2.5 }
  ],
  "action": "approve"
}
```
`action`: `"approve"` saves grade + question results | `"cancel"` skips student (no grade saved)

Returns:
```json
{
  "success": true,
  "action": "approved",
  "session_id": "uuid",
  "total_awarded": 15.5,
  "total_max": 20.0,
  "normalised_grade": 15.5,
  "grade": { ... },
  "next_session_id": "uuid-or-null"
}
```
Frontend uses `next_session_id` to immediately start `GET /sessions/{next_id}/stream`.  
When `next_session_id` is `null` — batch is complete.

---

## LangGraph Architecture

### Graph: `grading_graph` (single unified graph)

```
START
  ↓
bp_agent_node  ←─────────────── (loops while tool_calls)
  ↓ tool_calls                              ↑
bp_tools_node ───────────────────────────────┘
  ↓ no tool_calls
bp_interrupt_node  ← interrupt() HERE = THE BLUEPRINT CHECKPOINT
  │                  suspended, waiting for {"student_exam_path": "..."}
  ↓ resume
grade_agent_node ←──────────────(loops while tool_calls)
  ↓ tool_calls                              ↑
grade_tools_node ───────────────────────────┘
  ↓ no tool_calls
grade_interrupt_node  ← interrupt() HERE = teacher HIL
  │                     suspended, waiting for teacher decisions
  ↓ resume
END
```

### Blueprint Phase Tools
- `read_pdf_as_images(file_path, max_px)` — reads exam paper + correction PDF
- `rag_retrieve(query, doc_ids, max_px)` — semantic search over lesson pages in Weaviate

### Grading Phase Tools
- `read_pdf_as_images(file_path, max_px)` — reads student answer PDF only

### max_px Strategy (agent decides per call)
| Content Type | max_px |
|---|---|
| Plain short-answer text | 512 |
| Dense text, tables, formulas | 768 |
| Diagrams, graphs, figures | 1280 |
| Highly detailed technical visuals | 1536 |

### Checkpoint / Memory
- Checkpointer: `AsyncPostgresSaver` (shared pool in `backend/agents/db.py`)
- Blueprint thread: `analysis_thread_id` stored in `GradingBlueprint`
- Student thread: `GradingSession.thread_id` — forked from blueprint via `fork_thread()`
- Thinking/reasoning tokens: extracted from `delta.reasoning` via `ChatOpenAIWithReasoning`, stored in `additional_kwargs["reasoning"]` but **NOT sent back to LLM** (read + streamed to frontend only)
- `preserve_thinking: True` in `chat_template_kwargs` (vLLM param)

### LLM Configuration (`_make_llm`)
```python
ChatOpenAIWithReasoning(
    model=VLM_MODEL,
    base_url=HF_ENDPOINT_URL,
    streaming=True,
    max_tokens=8192,
    temperature=0.6 (reasoning) / 0.7 (no reasoning),
    top_p=0.95 / 0.8,
    extra_body={
        "top_k": 20,
        "think": reasoning,
        "chat_template_kwargs": {
            "enable_thinking": reasoning,
            "preserve_thinking": True,
        },
    },
)
```

---

## Phase 1: Blueprint / Analyse

### Flow
1. Teacher uploads exam paper PDF → `POST /exam-papers` → gets `exam_paper_id`
2. Teacher fills analyse form: exam_paper_id + lessons + optional correction + prefs + title
3. `POST /analyse` (SSE):
   - Validates all lesson `Upload` rows exist and are `embedded=True`
   - Looks up `ExamPaper` row → gets `file_path`
   - Saves correction PDF to `uploads/exams/{teacher_id}/corrections/` (if provided)
   - Creates fresh LangGraph thread (`analysis_thread_id = uuid4()`)
   - Runs `bp_agent_node` loop → agent reads exam + correction via `read_pdf_as_images`, uses `rag_retrieve` if needed
   - Graph suspends at `bp_interrupt_node` → **that checkpoint IS the blueprint**
   - Saves `GradingBlueprint` row (with `exam_paper_id`, `exam_file_path`, `analysis_thread_id`)
   - **Deletes correction PDF from disk** (one-time artifact — never stored long-term)
   - Sets `correction_file_path = None` on blueprint after deletion
   - Emits `blueprint_saved` SSE event → `done`

### System Prompt (`_BP_SYSTEM`)
Tells agent to:
1. Call `read_pdf_as_images(exam_file_path, max_px)` — read the exam
2. If correction provided: `read_pdf_as_images(correction_file_path, max_px)`
3. If clarification needed: `rag_retrieve(query, doc_ids, max_px)`
4. Apply teacher preferences and style guide
5. Output a concise blueprint summary (one question per line: label, max points, criteria)

---

## Phase 2: Student Grading Queue

### Flow
1. Teacher selects blueprint + class + exam_type
2. Teacher assigns each student their PDF: `{student_id, pdf}` pairs
3. `POST /grade`:
   - Validates blueprint not deleted
   - Validates class ownership
   - Validates exam_type belongs to class
   - Validates all student_ids are enrolled in class
   - Saves each PDF → `ExamUpload` row
   - Fetches student names → sorts pairs alphabetically
   - Creates `GradingSession` rows with `queue_position`
   - Returns `first_session_id`
4. Frontend opens `GET /sessions/{first_session_id}/stream`
5. Agent grades student → emits `question_result` per question → emits `interrupt`
6. Frontend shows breakdown with edit controls
7. Teacher reviews → `POST /sessions/{id}/review`
   - `approve`: saves `GradingQuestionResult` rows, normalises to 0–20, calls `save_grade()`
   - `cancel`: marks session cancelled, no grade written
   - Both return `next_session_id` (next pending in batch) or `null` (batch done)
8. Repeat from step 4 for `next_session_id`

### Forking (Critical)
```
blueprint checkpoint (analysis_thread_id)
    ↓ fork_thread() — SQL copy of all 3 checkpoint tables
student checkpoint (GradingSession.thread_id)
    ↓ Command(resume={"student_exam_path": "..."})
grade_agent_node runs — agent already has full exam context
```
`fork_thread()` uses `ON CONFLICT DO NOTHING` — idempotent, safe to call twice (e.g. on reconnect).

### Grade Normalisation
```
normalised = (total_awarded / total_max) * 20
clamped to [0.0, 20.0]
```

### Resuming After Disconnect
- Teacher logs back in
- `GET /sessions?batch_id=X` — sees pending sessions
- Teacher opens stream for the first `pending` session
- If session was `reviewing` (stream crashed mid-grading): use `force_restart=true`

---

## SSE Event Reference

All events: `event: {type}\ndata: {json}\n\n`

| Event | When | Data |
|-------|------|------|
| `thinking` | LLM reasoning chunk | `"token string"` |
| `content` | LLM answer chunk | `"token string"` |
| `tool_call` | Agent invoking a tool | `{"type","name","args","id"}` |
| `tool_result` | Tool returned | `{"type","name","content","tool_call_id"}` |
| `blueprint_ready` | Graph suspended at bp_interrupt | `{}` |
| `blueprint_saved` | Blueprint row written to DB | `{"blueprint_id":1,"title":"..."}` |
| `question_result` | One question graded | `{"question_number","label","max_points","awarded_points","reasoning"}` |
| `interrupt` | All questions graded, waiting for teacher | `{"breakdown":[...]}` |
| `error` | Fatal error | `"error message"` |
| `done` | Stream finished normally | `""` |

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Blueprint storage | LangGraph Postgres checkpoint | Full agent context preserved; no context re-injection |
| Blueprint scope | Teacher-scoped | Reusable across classes teaching same subject |
| Exam paper storage | Class-scoped `ExamPaper` table | Separates concern from student answer PDFs |
| Correction PDF | Deleted after analysis | One-time artifact; no long-term value |
| Student PDF storage | Permanent (`uploads/exams/`) | Needed for HITL resume after disconnect |
| Queue processing | Sequential (one student at a time) | Prevents context window bloat; clear teacher UX |
| Student sort order | Alphabetical by student name | Deterministic and user-friendly |
| Exam dedup | `(class_id, file_hash)` unique | Prevents duplicate uploads per class |
| File dedup on delete | Check other classes before unlinking | Same exam used in multiple classes |
| Reasoning tokens | Read + stream to frontend; NOT sent back to LLM | Avoids logic drift from wrong prior reasoning |
| Grade scale | Normalised 0–20 | Standard in the platform |
| `queue_position` | Set at `/grade` time, immutable | Stable ordering for resume |

---

## Outstanding TODO List

### Models (`backend/server/db/dbModels.py`)
- [x] Add `ExamPaper` table
- [x] Add `exam_paper_id` (nullable FK) to `GradingBlueprint`
- [x] Add `queue_position: int` to `GradingSession`
- [x] Update `__all__`

### Alembic Migration
- [x] `b4f1e2a3c5d6_grading_exam_papers_queue_position.py` — adds `exam_papers` table, `grading_blueprints.exam_paper_id`, `grading_sessions.queue_position`

### Route (`backend/server/routes/grading_route.py`)
- [x] `_stream_graph` helper function added (blocking bug fixed)
- [x] `POST /exam-papers`, `GET /exam-papers`, `DELETE /exam-papers/{id}` added
- [x] `POST /analyse` updated: accepts `exam_paper_id` (Form), deletes correction PDF after analysis
- [x] Old `POST /exam-uploads`, `DELETE /exam-uploads/{id}` removed
- [x] `POST /grade` rewritten: multipart `student_ids[]` + `exam_pdfs[]`, sorted alphabetically, queue created
- [x] `POST /sessions/{id}/review` updated: returns `next_session_id`
- [x] Student enrollment validation added to `/grade`

### Agent (`backend/agents/grading_agent/agent.py`)
- [x] No changes needed — graph topology is correct

### Frontend README (`backend/server/routes/README_GRADING_ROUTE.md`)
- [x] Updated: exam papers, new /analyse, /grade multipart flow, next_session_id, queue_position, resumption pattern, full error codes

---

## Implementation Order (when resuming)

```
1. dbModels.py  — add ExamPaper, update Blueprint + Session
2. Alembic      — one migration for all 3 changes
3. grading_route.py — in this order:
   a. _stream_graph helper (fixes blocking bug first)
   b. Exam paper endpoints
   c. /analyse update
   d. /grade rewrite
   e. /review update (next_session_id)
   f. Remove old /exam-uploads
4. README_GRADING_ROUTE.md — update for frontend
```

