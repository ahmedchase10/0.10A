# Grading Agent — Frontend Contract

All endpoints are under `/agents/grading`. Auth via `Authorization: Bearer <JWT>`.

---

## Overview — Full Frontend Flow

```
Phase 1 — Build a Blueprint (one-time per exam)
  1. POST /exam-papers          → upload exam question paper → exam_paper_id
  2. POST /analyse              → SSE: agent reads exam + lessons + correction
                                   → blueprint_saved { blueprint_id }

Phase 2 — Grade Students (repeat per class/batch)
  3. POST /grade                → multipart: blueprint + student PDFs
                                   → { first_session_id, sessions[] }
  4. GET  /sessions/{id}/stream → SSE: agent grades one student
                                   → question_result events → interrupt { breakdown }
  5. POST /sessions/{id}/review → teacher approves/edits/cancels
                                   → { next_session_id }   ← open next stream
  6. Repeat step 4–5 until next_session_id is null (batch complete)
```

---

## Exam Papers

Class-scoped exam question papers. Upload once, reuse for any blueprint.

---

### `POST /agents/grading/exam-papers`
Upload an exam question paper PDF for a class.

**Request**: `multipart/form-data`
| Field | Type | Required | Notes |
|---|---|---|---|
| `class_id` | int | ✅ | Must be your class |
| `file` | PDF | ✅ | The exam question paper |

**Response 200**:
```json
{
  "success": true,
  "exam_paper": {
    "id": 1,
    "class_id": 5,
    "filename": "exam1_2026.pdf",
    "size": 204800,
    "created_at": "2026-04-24T10:00:00"
  },
  "duplicate": false
}
```
`duplicate: true` — same file already uploaded for this class. Returns existing row, no new file saved.

---

### `GET /agents/grading/exam-papers?class_id={id}`
List all exam papers for a class.

**Response 200**:
```json
{
  "success": true,
  "exam_papers": [
    { "id": 1, "class_id": 5, "filename": "exam1_2026.pdf", "size": 204800, "created_at": "..." }
  ]
}
```

---

### `DELETE /agents/grading/exam-papers/{id}`
Delete an exam paper. The physical file is only removed from disk if no other class references the same file (teacher may assign the same exam to multiple classes).

**Response 200**:
```json
{ "success": true, "deleted": 1 }
```

---

## Blueprints — Phase 1

Teacher-scoped. Reusable across any class. One blueprint per exam style.

---

### `POST /agents/grading/analyse`
Analyse the exam paper and build the correction blueprint. **Returns SSE stream**.

**Request**: `multipart/form-data`
| Field | Type | Required | Notes |
|---|---|---|---|
| `exam_paper_id` | int | ✅ | From `POST /exam-papers` |
| `lesson_file_ids` | string (JSON array) | ❌ | e.g. `'["uuid1","uuid2"]'` — files must be embedded |
| `correction_pdf` | PDF file | ❌ | Teacher's model answer — **deleted from server after analysis** |
| `preferences` | string | ❌ | e.g. "Q1: 4pts. Deduct 1pt for missing units." |
| `style_guide` | string | ❌ | e.g. "Math: show all steps. Essays: min 3 arguments." |
| `title` | string | ✅ | e.g. "Exam 1 Correction – 2026" |
| `reasoning` | bool | ❌ | Default `false`. `true` = enable LLM thinking mode |

**SSE Event Stream** (listen until `done` or `error`):
```
event: thinking
data: " I need to read the exam structure first..."

event: content
data: " Reading exam paper..."

event: tool_call
data: {"type":"tool_call","name":"read_pdf_as_images","args":{"file_path":"...","max_px":768},"id":"tc_1"}

event: tool_result
data: {"type":"tool_result","name":"read_pdf_as_images","content":"Loaded read_pdf_as_images (14230 chars)","tool_call_id":"tc_1"}

event: tool_call
data: {"type":"tool_call","name":"rag_retrieve","args":{"query":"how to grade vector questions","doc_ids":["uuid1"],"max_px":512},"id":"tc_2"}

event: tool_result
data: {"type":"tool_result","name":"rag_retrieve","content":"Loaded rag_retrieve (8912 chars)","tool_call_id":"tc_2"}

event: blueprint_ready
data: {}

event: blueprint_saved
data: {"blueprint_id": 42, "title": "Exam 1 Correction – 2026"}

event: done
data: 
```

On error:
```
event: error
data: Error message string
```

**Frontend flow**:
1. Listen until `event: blueprint_saved` → store `blueprint_id`.
2. `event: blueprint_ready` fires just before `blueprint_saved` — use it to show a "Blueprint saved!" UI state.
3. `event: thinking` — display in a collapsible "reasoning" panel, not the main chat.
4. `event: content` — display in main progress area.

---

### `GET /agents/grading/blueprints`
List all teacher's non-deleted blueprints (teacher-scoped across all classes).

**Response 200**:
```json
{
  "success": true,
  "blueprints": [
    {
      "id": 42,
      "title": "Exam 1 Correction – 2026",
      "exam_paper_id": 1,
      "lesson_doc_ids": ["uuid1", "uuid2"],
      "preferences": "Q1: 4pts. Deduct 1pt...",
      "style_guide": "Show all steps.",
      "deleted": false,
      "created_at": "2026-04-24T10:00:00"
    }
  ]
}
```
`exam_paper_id` — display which exam this was built from (may be `null` if paper was deleted, blueprint still works).

---

### `GET /agents/grading/blueprints/{id}`
Single blueprint detail.

**Response 200** — same shape as list item.

---

### `DELETE /agents/grading/blueprints/{id}`
Soft-delete: metadata row kept, LangGraph checkpoint freed from Postgres.
Existing student grading sessions are **not** affected.

**Response 200**:
```json
{ "success": true, "deleted": 42 }
```

---

## Grading Sessions — Phase 2

---

### `POST /agents/grading/grade`
Submit a batch of student exam PDFs for grading. Creates one `GradingSession` per student, sorted alphabetically by student name.

**Request**: `multipart/form-data`

> ⚠️ **Critical**: `student_ids` and `exam_pdfs` are parallel lists — the i-th student ID corresponds to the i-th PDF. Use the same field name repeated for each student.

| Field | Type | Required | Notes |
|---|---|---|---|
| `blueprint_id` | int | ✅ | From `POST /analyse` |
| `class_id` | int | ✅ | Must be your class |
| `exam_type_id` | int | ✅ | Must belong to `class_id` |
| `student_ids` | int (repeated) | ✅ | One per student, all must be enrolled |
| `exam_pdfs` | PDF (repeated) | ✅ | Same count as `student_ids` |

**Example** (fetch API):
```js
const form = new FormData();
form.append("blueprint_id", "42");
form.append("class_id", "5");
form.append("exam_type_id", "3");

// Repeat for each student — SAME index = same student
form.append("student_ids", "10");
form.append("exam_pdfs", alicePdf, "alice.pdf");

form.append("student_ids", "11");
form.append("exam_pdfs", bobPdf, "bob.pdf");

fetch("/agents/grading/grade", { method: "POST", body: form, headers: { Authorization: `Bearer ${token}` } });
```

**Response 200**:
```json
{
  "success": true,
  "batch_id": "uuid-batch",
  "first_session_id": "uuid-s1",
  "sessions": [
    { "session_id": "uuid-s1", "student_id": 10, "student_name": "Alice Dupont",  "queue_position": 0 },
    { "session_id": "uuid-s2", "student_id": 11, "student_name": "Bob Martin",    "queue_position": 1 }
  ]
}
```
Sessions are returned in alphabetical order. `first_session_id` points to queue position 0 — open this stream immediately.

---

### `GET /agents/grading/sessions/{session_id}/stream`
Stream grading for one student. **Returns SSE stream**.

**Query params**:
| Param | Default | Description |
|---|---|---|
| `force_restart` | `false` | Re-run a crashed session (clears previous results, re-forks from blueprint) |

**Returns 409** if session status is not `pending` and `force_restart=false`.

**SSE Event Stream**:
```
event: thinking
data: " The student seems to have answered Q1 partially..."

event: content
data: " Grading Q1..."

event: tool_call
data: {"type":"tool_call","name":"read_pdf_as_images","args":{"file_path":"...","max_px":768},"id":"tc_1"}

event: tool_result
data: {"type":"tool_result","name":"read_pdf_as_images","content":"Loaded student exam (9841 chars)","tool_call_id":"tc_1"}

event: question_result
data: {"type":"question_result","question_number":1,"label":"Q1","max_points":4.0,"awarded_points":3.0,"reasoning":"Correctly identified KNN as instance-based but omitted distance metric (-1pt)."}

event: question_result
data: {"type":"question_result","question_number":2,"label":"Q2","max_points":6.0,"awarded_points":6.0,"reasoning":"Full derivation with correct formula. All steps shown."}

event: interrupt
data: {"type":"interrupt","breakdown":[
  {"question_number":1,"label":"Q1","max_points":4.0,"awarded_points":3.0,"reasoning":"..."},
  {"question_number":2,"label":"Q2","max_points":6.0,"awarded_points":6.0,"reasoning":"..."}
]}

event: done
data: 
```

**Frontend flow**:
1. Render `question_result` events as they arrive — build the per-question card UI incrementally.
2. On `event: interrupt` — the full `breakdown` array is the authoritative list. Show teacher the review UI.
3. Teacher edits scores per question (or leaves as-is), then clicks Approve or Cancel.
4. Call `POST /sessions/{id}/review`.

---

### `POST /agents/grading/sessions/{session_id}/review`
Submit teacher review after the `interrupt` event.

**Request JSON**:
```json
{
  "decisions": [
    { "question_number": 1, "awarded_points": 2.5 },
    { "question_number": 2, "awarded_points": 6.0 }
  ],
  "action": "approve"
}
```

| Field | Type | Notes |
|---|---|---|
| `action` | `"approve"` \| `"cancel"` | Cancel = skip student, no grade saved |
| `decisions` | array | Send **all** questions — even unchanged ones. Backend computes which were overridden. |

**Response 200 (approve)**:
```json
{
  "success": true,
  "action": "approved",
  "session_id": "uuid-s1",
  "total_awarded": 8.5,
  "total_max": 10.0,
  "normalised_grade": 17.0,
  "grade": {
    "id": 55,
    "class_id": 5,
    "student_id": 10,
    "exam_type_id": 3,
    "value": 17.0
  },
  "next_session_id": "uuid-s2"
}
```

**Response 200 (cancel)**:
```json
{
  "success": true,
  "action": "cancelled",
  "session_id": "uuid-s1",
  "next_session_id": "uuid-s2"
}
```

`next_session_id`:
- **String** → open `GET /sessions/{next_session_id}/stream` immediately.
- **`null`** → batch is complete, all students graded or skipped.

`normalised_grade` = `(total_awarded / total_max) × 20`, clamped to `[0, 20]`.

---

### `GET /agents/grading/sessions`
List grading sessions. Sorted by `queue_position`.

**Query params** (all optional):
| Param | Type | Description |
|---|---|---|
| `blueprint_id` | int | Filter by blueprint |
| `batch_id` | string | Filter by batch run |
| `class_id` | int | Filter by class |

**Response 200**:
```json
{
  "success": true,
  "sessions": [
    {
      "id": "uuid-s1",
      "blueprint_id": 42,
      "class_id": 5,
      "exam_type_id": 3,
      "student_id": 10,
      "batch_id": "uuid-batch",
      "queue_position": 0,
      "status": "approved",
      "created_at": "2026-04-24T10:05:00"
    }
  ]
}
```

**Session statuses**:
| Status | Meaning |
|---|---|
| `pending` | Created, not yet streamed |
| `reviewing` | Stream complete, waiting for teacher review |
| `approved` | Grade saved to DB |
| `cancelled` | Teacher skipped this student — no grade |

**Resuming after disconnect**: query `GET /sessions?batch_id=X` to find pending sessions. Stream the first one with `status=pending` ordered by `queue_position`.

---

## Resumption Pattern

If the teacher closes the tab mid-batch:

```js
// On page load — check for an in-progress batch
const { sessions } = await fetch(`/agents/grading/sessions?batch_id=${savedBatchId}`).then(r => r.json());

const nextPending = sessions
  .filter(s => s.status === "pending" || s.status === "reviewing")
  .sort((a, b) => a.queue_position - b.queue_position)[0];

if (nextPending) {
  // For "reviewing" sessions (stream crashed after grading was done):
  const streamUrl = nextPending.status === "reviewing"
    ? `/agents/grading/sessions/${nextPending.id}/stream?force_restart=true`
    : `/agents/grading/sessions/${nextPending.id}/stream`;
  openStream(streamUrl);
}
```

---

## Error Codes

| Code | HTTP | Meaning |
|---|---|---|
| `GRADING_INVALID_FILE` | 400 | File is not a PDF |
| `GRADING_INVALID_PARAMS` | 400 | Bad parameter format / count mismatch |
| `GRADING_FILE_NOT_FOUND` | 404 | Lesson file not found |
| `GRADING_FILE_NOT_EMBEDDED` | 422 | Lesson file not yet embedded in Weaviate |
| `GRADING_PAPER_NOT_FOUND` | 404 | Exam paper not found |
| `GRADING_PAPER_FORBIDDEN` | 403 | Not your exam paper |
| `GRADING_BLUEPRINT_NOT_FOUND` | 404 | Blueprint not found |
| `GRADING_BLUEPRINT_FORBIDDEN` | 403 | Not your blueprint |
| `GRADING_BLUEPRINT_DELETED` | 404 | Blueprint has been soft-deleted |
| `GRADING_INVALID_EXAM_TYPE` | 404 | exam_type_id not in this class |
| `GRADING_STUDENT_NOT_ENROLLED` | 404 | student_id not enrolled in class |
| `GRADING_SESSION_NOT_FOUND` | 404 | Session not found |
| `GRADING_SESSION_FORBIDDEN` | 403 | Not your session |
| `GRADING_SESSION_NOT_PENDING` | 409 | Session already ran (use `force_restart=true`) |
| `GRADING_SESSION_NOT_REVIEWING` | 409 | Session not in `reviewing` state |
| `GRADING_DATA_MISSING` | 404 | Blueprint or exam upload missing for session |
