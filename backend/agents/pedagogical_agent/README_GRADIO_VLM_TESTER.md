# Gradio VLM Direct Tester

This tester calls the Hugging Face OpenAI-compatible endpoint directly (`/chat/completions`) and streams raw SSE, without using your FastAPI agent route.

## File

- `backend/agents/pedagogical_agent/gradio_vlm_app.py`

## What it gives you

- Toggle thinking on/off (`think` + `chat_template_kwargs.enable_thinking`)
- Tune params (`temperature`, `top_p`, `max_tokens`, penalties, seed)
- Optional image input for VLM requests
- Local session memory (continue old messages or start a new one)
- Separate live panes for:
  - Thinking stream
  - Final content stream
  - Tool-call deltas
  - Diagnostics / optional raw SSE lines

## Install

From project root:

```powershell
python -m pip install -r backend\requirements.txt
```

## Run

From project root:

```powershell
python backend\agents\pedagogical_agent\gradio_vlm_app.py
```

Then open the local URL shown by Gradio (default `http://127.0.0.1:7861`).

## How session works in this tester

- This session is local to the Gradio app (in-memory), not server-side thread IDs.
- `Start new session on submit`: clears history before sending the next request.
- `New Session` button: immediate hard reset and fresh local session id.

## Notes

- Thinking tokens are parsed from `delta.reasoning` and `delta.reasoning_content`.
- Thinking is shown in the UI only and is not sent back in conversation history.
- Tool events are parsed from `delta.tool_calls` chunks.
- If your server changes stream fields, enable `Raw SSE to diagnostics` to inspect exact lines.

