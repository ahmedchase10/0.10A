# Creator Agent — Frontend API Reference

> **Base path**: `/agents/creator`  
> **Auth**: All endpoints require `Authorization: Bearer <token>` (teacher JWT).

---

## Table of Contents
1. [Generate Exam (SSE)](#1-post-agentscreatorgenerate)
2. [List Sessions](#2-get-agentscreatorsessions)
3. [Get Session](#3-get-agentscreatorsessionsid)
4. [Delete Session](#4-delete-agentscreatorsessionsid)
5. [Retry Overview](#5-post-agentscreatorretry-overview)
6. [SSE Event Reference](#sse-event-reference)
7. [Lesson Upload Changes](#lesson-upload-changes)
8. [Session Resume Flow](#session-resume-flow)
9. [Error Codes](#error-codes)

---

## 1. POST /agents/creator/generate

Start a new exam generation session or continue an existing one.

**Request**: `Content-Type: application/json`

```json
{
  "session_id": null,
  "doc_ids": ["uuid1", "uuid2"],
  "title": "Mid-term Exam 2026",
  "preferences": {
    "topics": ["KNN", "Decision Trees", "Overfitting"],
    "difficulty_distribution": { "easy": 20, "medium": 70, "hard": 10 },
    "exercise_types": ["mcq", "open"],
    "question_count": 10,
    "total_points": 20,
    "language": "French",
    "notes": "Focus on practical examples. Avoid pure theory."
  },
  "prompt": "Generate the exam based on the preferences.",
  "reasoning": false
}
```

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | int \| null | No | `null` = new session. Integer = resume existing session (for refinements like "make Q3 harder") |
| `doc_ids` | string[] | Yes | Upload IDs (must all be `embedded=true`) |
| `title` | string | Yes | Teacher-defined title (only used on new session) |
| `preferences.topics` | string[] | No | Topics to focus on. Empty = use all topics from the docs |
| `preferences.difficulty_distribution` | object | No | Percentages summing to 100: `{easy, medium, hard}` |
| `preferences.exercise_types` | string[] | No | Allowed: `"mcq"`, `"open"`, `"table"`, `"fill"`, `"true-false"` |
| `preferences.question_count` | int | No | Default 10, max 50 |
| `preferences.total_points` | float | No | Default 20.0 |
| `preferences.language` | string | No | Language for questions. Default `"French"` |
| `preferences.notes` | string | No | Free-text additional instructions |
| `prompt` | string | No | Message for this turn. On resume, this is the refinement instruction (e.g. `"Make question 3 harder"`) |
| `reasoning` | bool | No | Enable LLM thinking mode. Default `false` |

**Response**: `text/event-stream` (SSE)

See [SSE Event Reference](#sse-event-reference) for the full event list.

---

## 2. GET /agents/creator/sessions

List the teacher's exam generation sessions.

**Query params**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 20 | Max results (1–100) |
| `offset` | int | 0 | Pagination offset |

**Response**:
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": 1,
      "title": "Mid-term Exam 2026",
      "doc_ids": ["uuid1", "uuid2"],
      "loop_count": 1,
      "has_exam": true,
      "created_at": "2026-04-25T10:00:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0 }
}
```

`has_exam`: `true` when the agent successfully produced and saved an exam JSON. `false` on a new session before generation completes.

---

## 3. GET /agents/creator/sessions/{id}

Get full session details including the generated exam.

**Response**:
```json
{
  "success": true,
  "session": {
    "session_id": 1,
    "title": "Mid-term Exam 2026",
    "doc_ids": ["uuid1"],
    "preferences": {
      "topics": ["KNN"],
      "difficulty_distribution": { "easy": 20, "medium": 70, "hard": 10 },
      "exercise_types": ["mcq", "open"],
      "question_count": 10,
      "total_points": 20,
      "language": "French",
      "notes": ""
    },
    "exam": {
      "questions": [
        {
          "id": "q1",
          "text": "What does KNN stand for?",
          "type": "mcq",
          "difficulty": "easy",
          "max_points": 1.0,
          "options": ["A. K-Nearest Nodes", "B. K-Nearest Neighbors", "C. K-Net Network", "D. K-Null Nodes"],
          "suggested_answer": "B. K-Nearest Neighbors",
          "source_doc_id": "uuid1",
          "source_hint": "Introduction section, page 2"
        }
      ]
    },
    "loop_count": 1,
    "created_at": "2026-04-25T10:00:00Z"
  }
}
```

`exam` is `null` if generation has not yet completed.

---

## 4. DELETE /agents/creator/sessions/{id}

Delete a session and its LangGraph checkpoint.

**Response**:
```json
{
  "success": true,
  "deleted": { "session_id": 1, "title": "Mid-term Exam 2026" }
}
```

---

## 5. POST /agents/creator/retry-overview

Re-queue document overview generation for all lesson uploads in a class where the overview is missing (`overview_ready = false`). Same pattern as the embedding retry button.

**Request**:
```json
{ "class_id": 1 }
```

**Response**:
```json
{ "success": true, "queued": ["uuid1", "uuid3"] }
```

Returns the list of Upload IDs that were queued. Empty array = all overviews already generated.

---

## SSE Event Reference

All SSE events follow the format: `event: {type}\ndata: {payload}\n\n`

The `data` field is always a **JSON string** for structured events, or a **plain string** for token events.

### `thinking`
Streaming token of the LLM's internal reasoning (only when `reasoning=true`).
```
event: thinking
data: " need to consider the difficulty..."
```
Display in a collapsible "Thinking..." section separate from the main chat.

### `content`
Streaming token of the LLM's response text.
```
event: content
data: "Generating your exam based on the K-Nearest Neighbors chapter..."
```
Accumulate tokens into the chat message bubble.

### `tool_call`
Agent is about to invoke a tool.
```
event: tool_call
data: {"type":"tool_call","name":"get_doc_overviews","args":{"doc_ids":["uuid1"]},"id":"call_abc"}
```
Show a brief "Analysing document structure..." indicator.

### `tool_result`
Tool returned a result (only for `get_doc_overviews` — rag results are sent to LLM only).
```
event: tool_result
data: {"type":"tool_result","name":"get_doc_overviews","content":"[{...}]","tool_call_id":"call_abc"}
```
Optional display.

### `exam_draft`
The creator has produced an exam draft (may be revised if evaluator loops).
```
event: exam_draft
data: {"questions":[{"id":"q1","text":"...","type":"mcq","difficulty":"easy",...}]}
```
You can show a preview of the draft. If `evaluator_feedback` arrives after, some questions may be revised.

### `evaluator_feedback`
The evaluator found questions not grounded in the documents and the creator will revise.
```
event: evaluator_feedback
data: {"flagged":[{"question_id":"q3","reason":"No page covers binary trees"}],"loop_count":1}
```
Show "Agent is revising flagged questions..." indicator.

### `exam_saved`
Final exam has been saved to the database. This is the terminal success event before `done`.
```
event: exam_saved
data: {"session_id":1,"title":"Mid-term Exam 2026","loop_count":1}
```
`loop_count` tells you how many revision rounds happened (0 = exam passed on first try).

### `error`
A fatal error occurred.
```
event: error
data: "Upload uuid1 not found."
```

### `done`
Stream closed normally. Always emitted last.
```
event: done
data: ""
```

---

## Lesson Upload Changes

The lesson list endpoint (`GET /lessons?class_id=X`) now includes a new field per upload:

```json
{
  "id": "uuid1",
  "name": "KNN Chapter.pdf",
  "size": 204800,
  "embedded": true,
  "overview_ready": true,
  "created_at": "..."
}
```

**`overview_ready`**: `true` when the document overview has been generated by the local Ollama model.  
- `false` = overview pending (Ollama may be offline or still processing)
- The creator agent still works when `overview_ready=false` but the agent will rely more on `rag_retrieve` and may be slightly less efficient at topic selection

**Recommended UI behavior**:
- Show a small indicator (e.g. icon badge) on lesson docs that have `overview_ready=false`
- Add a "Retry Overview" button (calls `POST /agents/creator/retry-overview`) when any selected doc has `overview_ready=false`

---

## Session Resume Flow

The creator agent is stateful — you can continue in the same session to refine the exam.

```
1. Teacher opens /generate with session_id=null → SSE stream → exam_saved event
2. Teacher reviews the generated exam → wants changes
3. Teacher sends: POST /agents/creator/generate with:
     { "session_id": 1, "prompt": "Make question 3 harder. Add one more MCQ about Euclidean distance." }
4. Agent resumes from checkpoint → knows all previous context → refines and regenerates
5. New exam_saved with updated exam_json
```

The `doc_ids`, `title`, and `preferences` on a resume call are ignored — the session already has them.  
Only `session_id`, `prompt`, and `reasoning` are relevant on resume.

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `CREATOR_DOC_NOT_FOUND` | 404 | One of the `doc_ids` does not exist |
| `CREATOR_DOC_NOT_EMBEDDED` | 400 | One or more docs not yet embedded — wait or trigger retry-embed |
| `CREATOR_SESSION_NOT_FOUND` | 404 | `session_id` does not exist or belongs to another teacher |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Action not allowed for this teacher |
| `VALIDATION_ERROR` | 422 | Invalid request body (e.g. `question_count` > 50) |

