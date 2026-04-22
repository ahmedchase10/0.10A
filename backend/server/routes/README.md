# Routes README (Frontend)

This file documents what the frontend should send and expect for the pedagogical agent routes.

## Base

All endpoints here are mounted under `/agents`.

Auth is required:

- Header: `Authorization: Bearer <JWT>`

## 1) Session Endpoints (JSON)

### `POST /agents/sessions`

Create a new chat session.

Request body:

```json
{
  "class_id": 12,
  "title": "Chapter 3 prep"
}
```

Response:

```json
{
  "success": true,
  "session": {
    "thread_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "class_id": 12,
    "title": "Chapter 3 prep",
    "created_at": "2026-04-22T20:21:55.000000"
  }
}
```

### `GET /agents/sessions?class_id=<id>`

List sessions for a class.

Response:

```json
{
  "success": true,
  "sessions": [
    {
      "thread_id": "...",
      "class_id": 12,
      "title": "Chapter 3 prep",
      "created_at": "2026-04-22T20:21:55.000000"
    }
  ]
}
```

### `GET /agents/sessions/{thread_id}`

Get one session metadata.

Response:

```json
{
  "success": true,
  "session": {
    "thread_id": "...",
    "class_id": 12,
    "title": "Chapter 3 prep",
    "created_at": "2026-04-22T20:21:55.000000"
  }
}
```

### `DELETE /agents/sessions/{thread_id}`

Delete a session.

Response:

```json
{
  "success": true,
  "deleted": "<thread_id>"
}
```

## 2) Pedagogical Endpoint (SSE)

### `POST /agents/pedagogical`

This endpoint returns an SSE stream (`text/event-stream`) over POST.

Request body:

```json
{
  "thread_id": "<session_thread_id>",
  "file_ids": ["<upload_id_1>", "<upload_id_2>"],
  "prompt": "Explain photosynthesis from lesson 2",
  "reasoning": true
}
```

Notes:

- `file_ids` must be valid embedded upload IDs.
- `reasoning=true` enables thinking stream.
- Reusing the same `thread_id` continues the same memory/checkpoint.

## SSE Events Emitted

Each frame looks like:

```text
event: <event_name>
data: <string_payload>

```

Event names used by backend:

- `thinking` -> reasoning token chunk
- `content` -> answer token chunk
- `tool_call` -> tool invocation metadata (JSON string)
- `tool_result` -> tool result metadata (JSON string)
- `error` -> fatal error message
- `done` -> stream finished

Typical timeline:

1. many `thinking` events
2. then many `content` events
3. final `done`

Tool events may appear between phases.

## Payload Shape Per Event

- `thinking`: plain string token/chunk
- `content`: plain string token/chunk
- `tool_call`: JSON string (use `JSON.parse`)
- `tool_result`: JSON string (use `JSON.parse`)
- `error`: plain string
- `done`: usually empty string

Example stream frames:

```text
event: thinking
data: Here

event: thinking
data: 's

event: content
data: Here is the explanation...

event: tool_call
data: {"type":"tool_call","name":"rag_retrieve","args":{"query":"..."}}

event: done
data:

```

## Frontend Implementation Guide

Because this is POST SSE, `EventSource` is usually not suitable.
Use `fetch` + `ReadableStream` and parse SSE frames manually.

### Minimal Browser Parser

```js
async function streamPedagogical({ token, body, onEvent }) {
  const res = await fetch('/agents/pedagogical', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok || !res.body) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop() || '';

    for (const frame of frames) {
      let event = 'message';
      let data = '';

      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        if (line.startsWith('data:')) data += line.slice(5).trimStart();
      }

      onEvent({ event, data });

      if (event === 'done') return;
      if (event === 'error') throw new Error(data || 'Stream error');
    }
  }
}
```

### Suggested UI State

Maintain separate buffers:

- `thinkingText` (append `thinking` data)
- `answerText` (append `content` data)

And state flags:

- `isStreaming`
- `isDone`
- `streamError`

### Tool Events

```js
if (event === 'tool_call' || event === 'tool_result') {
  const payload = JSON.parse(data);
  // optional: show tool activity timeline
}
```

## Error Cases

Immediate HTTP errors before stream starts (JSON/text body):

- `404` file/session not found
- `422` file not embedded
- `403` forbidden class/session access

Runtime stream error:

- `event: error` + message

Handle both HTTP-level and stream-level errors.

## Quick Integration Checklist

- Create or select a `thread_id` via `/agents/sessions` endpoints.
- Ensure chosen `file_ids` are embedded.
- Send `reasoning: true` if thinking stream is needed.
- Parse SSE frames from POST response body.
- Handle `thinking`, `content`, `tool_call`, `tool_result`, `error`, `done`.
- Reuse same `thread_id` for memory continuity.

