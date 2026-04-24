"""
Gradio test UI for the pedagogical agent SSE stream.
Connects directly to the FastAPI /agents/pedagogical endpoint and
renders each event type in its own panel — exactly what the frontend sees.

Run:
    python -m backend.agents.pedagogical_agent.gradio_agent_test
or:
    cd C:\\Users\\Dusty\\PycharmProjects\\Digi-School
    python backend/agents/pedagogical_agent/gradio_agent_test.py
"""
import json
import re
import httpx
import gradio as gr

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TOKEN    = ""          # paste your JWT here or leave blank for no auth


# ── SSE parser ────────────────────────────────────────────────────────────────

def _parse_sse_line(line: str) -> tuple[str | None, str | None]:
    """Return (event_type, data) from a raw SSE line pair, or (None, None)."""
    return None, None  # handled below in the generator


def stream_agent(
    base_url: str,
    token: str,
    thread_id: str,
    file_ids_raw: str,
    prompt: str,
    reasoning: bool,
) -> tuple[str, str, str, str, str]:
    """
    Generator that yields updated (thinking, content, tool_calls, tool_results, raw_log)
    tuples on every SSE event.
    """
    url      = base_url.rstrip("/") + "/agents/pedagogical"
    file_ids = [f.strip() for f in re.split(r"[,\s]+", file_ids_raw.strip()) if f.strip()]

    headers = {"Accept": "text/event-stream"}
    if token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    payload = {
        "thread_id": thread_id.strip(),
        "file_ids":  file_ids,
        "prompt":    prompt,
        "reasoning": reasoning,
    }

    thinking_buf    = ""
    content_buf     = ""
    tool_calls_buf  = ""
    tool_results_buf = ""
    raw_log         = ""

    current_event = "message"
    current_data  = ""

    try:
        with httpx.Client(timeout=300) as client:
            with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = resp.read().decode()
                    raw_log += f"[HTTP {resp.status_code}] {body}\n"
                    yield thinking_buf, content_buf, tool_calls_buf, tool_results_buf, raw_log
                    return

                for raw_line in resp.iter_lines():
                    raw_log += raw_line + "\n"

                    if raw_line.startswith("event:"):
                        current_event = raw_line[len("event:"):].strip()
                        current_data  = ""

                    elif raw_line.startswith("data:"):
                        current_data = raw_line[len("data:"):].strip()

                    elif raw_line == "":
                        # blank line = end of SSE frame → dispatch
                        ev   = current_event
                        data = current_data

                        if ev == "thinking":
                            thinking_buf += data
                        elif ev == "content":
                            content_buf += data
                        elif ev == "tool_call":
                            try:
                                obj = json.loads(data)
                                tool_calls_buf += (
                                    f"▶ {obj.get('name','?')}(\n"
                                    f"  {json.dumps(obj.get('args',{}), indent=2)}\n"
                                    f"  id={obj.get('id','')}\n)\n\n"
                                )
                            except Exception:
                                tool_calls_buf += data + "\n"
                        elif ev == "tool_result":
                            try:
                                obj = json.loads(data)
                                tool_results_buf += (
                                    f"◀ {obj.get('name','?')}:\n"
                                    f"  {obj.get('content','')}\n\n"
                                )
                            except Exception:
                                tool_results_buf += data + "\n"
                        elif ev == "error":
                            content_buf += f"\n\n⚠️ ERROR: {data}"
                        elif ev == "done":
                            raw_log += "[DONE]\n"

                        # reset for next frame
                        current_event = "message"
                        current_data  = ""

                        yield thinking_buf, content_buf, tool_calls_buf, tool_results_buf, raw_log

    except Exception as exc:
        raw_log += f"\n[EXCEPTION] {exc}\n"
        yield thinking_buf, content_buf, tool_calls_buf, tool_results_buf, raw_log


# ── Gradio UI ─────────────────────────────────────────────────────────────────

def run(base_url, token, thread_id, file_ids_raw, prompt, reasoning):
    thinking    = ""
    content     = ""
    tool_calls  = ""
    tool_results = ""
    raw_log     = ""

    for thinking, content, tool_calls, tool_results, raw_log in stream_agent(
        base_url, token, thread_id, file_ids_raw, prompt, reasoning
    ):
        yield thinking, content, tool_calls, tool_results, raw_log


with gr.Blocks(title="Pedagogical Agent — SSE Tester", theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🧪 Pedagogical Agent — SSE Stream Tester\nExactly what the frontend receives, split by event type.")

    with gr.Row():
        base_url_box = gr.Textbox(label="FastAPI Base URL", value=DEFAULT_BASE_URL, scale=3)
        token_box    = gr.Textbox(label="JWT Token (Bearer)", value=DEFAULT_TOKEN,  scale=4, type="password")

    with gr.Row():
        thread_id_box  = gr.Textbox(label="Thread ID (session)", placeholder="my-test-session-001", scale=2)
        file_ids_box   = gr.Textbox(label="File IDs (comma/space separated)", placeholder="uuid1, uuid2", scale=3)
        reasoning_chk  = gr.Checkbox(label="Enable Thinking (reasoning)", value=True, scale=1)

    prompt_box = gr.Textbox(label="Prompt", lines=3, placeholder="Ask something about the uploaded docs…")

    submit_btn = gr.Button("▶ Send", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 💭 Thinking")
            thinking_out = gr.Textbox(label="", lines=12, interactive=False, show_copy_button=True)
        with gr.Column():
            gr.Markdown("### 💬 Answer")
            content_out  = gr.Textbox(label="", lines=12, interactive=False, show_copy_button=True)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🔧 Tool Calls")
            tool_calls_out   = gr.Textbox(label="", lines=8, interactive=False, show_copy_button=True)
        with gr.Column():
            gr.Markdown("### 📥 Tool Results")
            tool_results_out = gr.Textbox(label="", lines=8, interactive=False, show_copy_button=True)

    with gr.Accordion("📡 Raw SSE Log", open=False):
        raw_log_out = gr.Textbox(label="", lines=20, interactive=False, show_copy_button=True)

    submit_btn.click(
        fn=run,
        inputs=[base_url_box, token_box, thread_id_box, file_ids_box, prompt_box, reasoning_chk],
        outputs=[thinking_out, content_out, tool_calls_out, tool_results_out, raw_log_out],
    )


if __name__ == "__main__":
    demo.launch(server_port=7861, share=False)

