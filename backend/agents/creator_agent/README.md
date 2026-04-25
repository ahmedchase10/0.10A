# Creator Agent — Full Architecture & Implementation Plan

> **Status**: Implementation in progress.  
> Use this document as the single source of truth when resuming.

---

## Table of Contents
1. [Overview](#overview)
2. [Data Models](#data-models)
3. [File Storage Layout](#file-storage-layout)
4. [Preprocessing Pipeline](#preprocessing-pipeline)
5. [API Endpoints — Full Reference](#api-endpoints)
6. [LangGraph Architecture](#langgraph-architecture)
7. [Phase 1: Exam Creation Loop](#phase-1-exam-creation-loop)
8. [Phase 2: Student Evaluator Loop](#phase-2-student-evaluator-loop)
9. [SSE Event Reference](#sse-event-reference)
10. [Key Design Decisions](#key-design-decisions)
11. [Outstanding TODO List](#outstanding-todo-list)

---

## Overview

The creator agent generates exams for a teacher based on selected lesson PDFs and structured preferences.

```
Preprocessing (triggered at upload time, runs in background)
  Teacher uploads lesson PDF →
  PyMuPDF extracts text per page →
  Tesseract OCR fills pages with < 100 chars of extracted text →
  Ollama Qwen 1.7B receives full text → returns structured JSON overview →
  Upload.overview column written to Postgres

Exam Generation (SSE stream)
  Teacher selects doc_ids + preferences (topics, difficulty split, exercise types, count, title) →
  Agent reads doc overviews via get_doc_overviews tool →
  Agent decides which pages to retrieve via rag_retrieve tool →
  Agent generates exam JSON draft (questions + suggested answers + difficulty + points) →
  Evaluator node tries to answer each question using rag_retrieve as a "student" →
  If weak questions found AND loop_count < 2 → back to creator node with feedback →
  Otherwise → final exam emitted → saved to GeneratedExam table →
  Session stays open for teacher refinements ("make Q3 harder", etc.)
```

---

## Data Models

### `Upload` (EXISTS — add `overview` column)

```
uploads
  ...existing columns...
  overview : JSONB NULLABLE — structured doc overview, null until preprocessed
```

The overview JSON shape:
```json
{
  "sections": [
    {
      "title": "Chapter 1 — Introduction to ML",
      "subsections": [
        {
          "title": "What is Machine Learning?",
          "topics": ["Definition and scope", "Types: supervised, unsupervised, reinforcement"]
        }
      ]
    }
  ]
}
```

### `GeneratedExam` (NEW)

```
generated_exams
  id           : int PK
  teacher_id   : FK → teachers.id  (INDEX)
  thread_id    : str (uuid, max 36)
  title        : str (max 120)
  doc_ids      : str (JSON array of Upload UUIDs)
  preferences  : str (JSON string)
  exam_json    : str (TEXT — final exam JSON)
  loop_count   : int (default 0)
  created_at   : datetime
```

---

## File Storage Layout

No new folders needed. Creator agent only reads existing lesson PDFs from `uploads/classes/{class_id}/`.

---

## Preprocessing Pipeline

### Location
`backend/agents/creator_agent/preprocessor.py`

### Trigger
Hooked into `embed_upload_task` in `backend/lessons/main.py` — runs in the same background thread after embedding completes.

### Steps (per document)

```
1. Open PDF with PyMuPDF (fitz)
2. For each page:
   a. Extract text via page.get_text("text")
   b. IF len(text.strip()) < 100:
        render page to image (fitz pixmap, zoom=1.5)
        run Tesseract OCR (pytesseract, lang='fra+eng')
        use OCR text instead
3. Concatenate: "=== Page 1 ===\n{text}\n=== Page 2 ===\n..."
4. POST to Ollama Qwen (local): stream=false, think=false, temperature=0.1
5. Parse JSON → validate "sections" key
6. Write Upload.overview to Postgres
```

### Failure Handling
- Ollama offline or bad JSON → log error, leave `Upload.overview = null`
- `POST /agents/creator/retry-overview` re-queues all `overview IS NULL` uploads for a class

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents/creator/generate` | Start or resume exam generation (SSE) |
| `GET` | `/agents/creator/sessions` | List teacher's exam sessions |
| `GET` | `/agents/creator/sessions/{id}` | Get session details + exam_json |
| `DELETE` | `/agents/creator/sessions/{id}` | Delete session + checkpoint |
| `POST` | `/agents/creator/retry-overview` | Re-queue overview for `overview IS NULL` uploads |

---

### POST /agents/creator/generate

`application/json` body:
```json
{
  "session_id": null,
  "doc_ids": ["uuid1", "uuid2"],
  "title": "Mid-term Exam 2026",
  "preferences": {
    "topics": ["KNN", "Decision Trees"],
    "difficulty_distribution": { "easy": 20, "medium": 70, "hard": 10 },
    "exercise_types": ["mcq", "open", "table"],
    "question_count": 10,
    "total_points": 20,
    "language": "French",
    "notes": "Focus on practical examples."
  },
  "reasoning": true
}
```

- `session_id = null` → new session
- `session_id = "uuid"` → resume (teacher refines: "make Q3 harder")
- `doc_ids` must be `embedded=True`
- `overview IS NULL` allowed but agent is warned

SSE events: `thinking`, `content`, `tool_call`, `tool_result`, `evaluator_feedback`, `exam_draft`, `exam_saved`, `error`, `done`

**exam_saved** payload: `{"session_id": "uuid", "title": "...", "loop_count": 1}`

---

### GET /agents/creator/sessions

Query: `limit`, `offset`

---

### GET /agents/creator/sessions/{id}

Returns session + full `exam_json`.

---

### DELETE /agents/creator/sessions/{id}

Deletes row + hard-deletes LangGraph checkpoint.

---

### POST /agents/creator/retry-overview

Body: `{"class_id": 1}`  
Returns: `{"success": true, "queued": ["uuid1", "uuid2"]}`

---

## LangGraph Architecture

### Graph: `creator_graph`

```
START
  ↓
creator_node  ←──────────────────────────(loops while tool_calls)
  ↓ tool_calls                                        ↑
creator_tools_node ─────────────────────────────────┘
  ↓ no tool_calls
evaluator_node  ←────────────────────────(loops while tool_calls)
  ↓ tool_calls                                        ↑
evaluator_tools_node ───────────────────────────────┘
  ↓ no tool_calls
route_after_eval
  ├── loop_count < 2 AND weak questions → creator_node
  └── otherwise → END
```

### Agent State

```python
class CreatorState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    doc_ids: List[str]
    preferences: dict
    reasoning: bool
    loop_count: int             # evaluator loop counter (max 2)
    exam_draft: Optional[dict]  # last generated exam JSON
    evaluator_feedback: Optional[str]
```

### Tools

**Creator node**: `get_doc_overviews(doc_ids)` + `rag_retrieve(query, doc_ids, max_px)`  
**Evaluator node**: `rag_retrieve(query, doc_ids, max_px)` only

### Checkpoint / Memory
- `AsyncPostgresSaver` (shared pool in `backend/agents/db.py`)
- Thread ID stored in `GeneratedExam.thread_id`
- Stateful: teacher can refine in same session
- Reasoning: streamed to frontend, NOT sent back to LLM

### LLM Config
Same as pedagogical + grading agents:
```python
ChatOpenAIWithReasoning(
    model=VLM_MODEL, base_url=HF_ENDPOINT_URL, streaming=True,
    max_tokens=8192, temperature=0.6/0.7, top_p=0.95/0.8,
    extra_body={"top_k": 20, "think": reasoning,
                "chat_template_kwargs": {"enable_thinking": reasoning, "preserve_thinking": True}}
)
```

---

## Phase 1: Exam Creation Loop

### System Prompt (`_CREATOR_SYSTEM`)
1. Call `get_doc_overviews` first to understand document structure
2. Respect preferences: difficulty split, types, count, total points, language
3. Call `rag_retrieve` for each question — every question must be grounded in retrieved material
4. Output exam as structured JSON block: `{questions: [{id, text, type, difficulty, max_points, suggested_answer, source_doc_id, source_hint}]}`
5. If `evaluator_feedback` is in the system prompt: fix flagged questions specifically

---

## Phase 2: Student Evaluator Loop

### Purpose
Evaluator acts as a "student" — uses `rag_retrieve` to verify each question is answerable from the selected docs. Flags questions the material does not support.

### Max loops: 2
`loop_count`: 0 → 1 → 2 → stop (include warning note instead of looping).

### Evaluator output
```json
{"flagged": [{"question_id": "q3", "reason": "No page covers binary trees"}], "pass": false}
```

---

## SSE Event Reference

| Event | When | Data |
|-------|------|------|
| `thinking` | LLM reasoning chunk | `"token string"` |
| `content` | LLM answer chunk | `"token string"` |
| `tool_call` | Agent invoking a tool | `{"type","name","args","id"}` |
| `tool_result` | Tool returned | `{"type","name","content","tool_call_id"}` |
| `evaluator_feedback` | Evaluator found weak questions | `{"flagged":[...],"loop_count":1}` |
| `exam_draft` | Creator produced a draft | `{"questions":[...]}` |
| `exam_saved` | Final exam written to DB | `{"session_id","title","loop_count"}` |
| `error` | Fatal error | `"error message"` |
| `done` | Stream finished normally | `""` |

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Overview storage | `Upload.overview` JSONB column | Colocated with upload row, no extra table |
| Overview trigger | Same background task as embedding | One worker per upload |
| Overview failure | `null` + retry button | Same UX as `embedded=False` |
| OCR fallback | Tesseract (CPU) for pages < 100 chars | Handles scanned pages without wasting VLM |
| Session statefulness | LangGraph AsyncPostgresSaver | Teacher can refine in same session |
| Evaluator loop cap | 2 max | Prevents infinite loops |
| Evaluator tools | Only `rag_retrieve` | Evaluator = student, only uses material |
| Reasoning tokens | Stream only, not sent back to LLM | Same as all other agents |

---

## Outstanding TODO List

### Models (`backend/server/db/dbModels.py`)
- [x] Add `overview: Optional[dict]` JSONB nullable column to `Upload`
- [x] Add `GeneratedExam` table
- [x] Update `__all__`

### Alembic Migration
- [x] `ALTER TABLE uploads ADD COLUMN overview JSONB`
- [x] `CREATE TABLE generated_exams`

### Preprocessor (`backend/agents/creator_agent/preprocessor.py`)
- [x] `generate_overview_task(file_path, upload_id, db_url)`
- [x] PyMuPDF + Tesseract + Ollama chain
- [x] JSON validation + DB write

### Lessons integration (`backend/lessons/main.py`)
- [x] Hook `generate_overview_task` into `embed_upload_task`
- [x] Add `overview_ready` to `list_lesson_uploads` response

### Tools (`backend/agents/creator_agent/tools.py`)
- [x] `get_doc_overviews(doc_ids)`
- [x] Re-export `rag_retrieve`

### Agent (`backend/agents/creator_agent/agent.py`)
- [x] `CreatorState`, prompts, nodes, graph

### Route (`backend/server/routes/creator_route.py`)
- [x] All 5 endpoints + registered in `index.py`

### Frontend README
- [x] `backend/server/routes/README_CREATOR_ROUTE.md`

---

## Implementation Order (when resuming)

```
1. dbModels.py  — Upload.overview + GeneratedExam + __all__
2. Alembic      — one migration for both changes
3. preprocessor.py
4. lessons/main.py  — hook + overview_ready in list
5. creator_agent/tools.py
6. creator_agent/agent.py
7. creator_route.py
8. server/index.py  — register router
9. README_CREATOR_ROUTE.md
```
