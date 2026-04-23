"""
Gradio tester for direct Hugging Face OpenAI-compatible VLM endpoint streaming.

This bypasses FastAPI/LangGraph and talks to /chat/completions exactly like
the raw test utility, with richer controls for manual debugging.
"""

from __future__ import annotations

import base64
import json
import os
import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple
    
import gradio as gr
import requests
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import HF_ENDPOINT_URL, HF_TOKEN, VLM_MODEL


def _resolve_chat_url(endpoint_base: str) -> str:
    base = endpoint_base.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _new_session_id() -> str:
    return f"vlm-{uuid.uuid4()}"


def _image_to_data_url(img: Image.Image) -> str:
    buff = BytesIO()
    img.save(buff, format="PNG")
    raw = base64.b64encode(buff.getvalue()).decode("ascii")
    return f"data:image/png;base64,{raw}"


def _build_user_content(prompt: str, image: Optional[Image.Image]) -> Any:
    if image is None:
        return prompt
    return [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": _image_to_data_url(image)}},
    ]


def _strip_leading_think_block(text: str) -> str:
    """Remove a leading <think>...</think> block if present."""
    return re.sub(r"^\s*<think>.*?</think>\s*", "", text, flags=re.DOTALL)


def _sanitize_history_for_send(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure assistant history sent to the model never contains reasoning replay."""
    normalized: List[Dict[str, Any]] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if role != "assistant":
            normalized.append(msg)
            continue

        content = msg.get("content", "")
        if isinstance(content, str):
            content = _strip_leading_think_block(content)

        normalized.append({
            "role": "assistant",
            "content": content,
        })
    return normalized


def _extract_delta_content(delta: Dict[str, Any]) -> str:
    content = delta.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") in {"text", "output_text"}:
                txt = item.get("text")
                if isinstance(txt, str):
                    parts.append(txt)
        return "".join(parts)
    return ""


def _parse_sse_line(raw_line: str) -> Optional[Tuple[str, str, str, str, str]]:
    """Return incremental buckets: (thinking, content, tools, diag, error)."""
    if not raw_line:
        return None
    if not raw_line.startswith("data:"):
        return None

    payload = raw_line[len("data:") :].strip()
    if payload == "[DONE]":
        return "", "", "", "[DONE]\n", ""

    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        return "", "", "", f"bad_json: {payload[:240]}\n", ""

    choices = obj.get("choices") or []
    if not choices:
        return "", "", "", "", ""

    choice = choices[0]
    delta = choice.get("delta") or {}

    thinking = ""
    for key in ("reasoning", "reasoning_content"):
        val = delta.get(key)
        if isinstance(val, str):
            thinking += val

    content = _extract_delta_content(delta)

    tool_text = ""
    tool_calls = delta.get("tool_calls")
    if isinstance(tool_calls, list):
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            idx = call.get("index", "?")
            call_id = call.get("id", "")
            fn = call.get("function") or {}
            name = fn.get("name", "") if isinstance(fn, dict) else ""
            args = fn.get("arguments", "") if isinstance(fn, dict) else ""
            tool_text += f"tool_delta idx={idx} id={call_id} name={name} args_chunk={args}\n"

    finish = choice.get("finish_reason")
    diag = ""
    if finish:
        diag = f"finish_reason={finish}\n"

    return thinking, content, tool_text, diag, ""


def _stream_request(
    endpoint_url: str,
    token: str,
    model: str,
    messages: List[Dict[str, Any]],
    thinking: bool,
    temperature: float,
    top_p: float,
    max_tokens: int,
    seed: int,
    freq_penalty: float,
    presence_penalty: float,
    raw_mode: bool,
    timeout: int,
) -> Generator[Tuple[str, str, str, str, str], None, None]:
    chat_url = _resolve_chat_url(endpoint_url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "frequency_penalty": freq_penalty,
        "presence_penalty": presence_penalty,
        "chat_template_kwargs": {
            "enable_thinking": thinking,
            "preserve_thinking": True,
        },
        "think": thinking,
    }
    if seed >= 0:
        payload["seed"] = seed

    yield "", "", "", f"POST {chat_url}\n", ""

    try:
        with requests.post(
            chat_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=timeout,
        ) as resp:
            if resp.status_code >= 400:
                body = resp.text
                yield "", "", "", "", f"HTTP {resp.status_code}: {body}"
                return

            for raw_line in resp.iter_lines(decode_unicode=True):
                line = raw_line if raw_line is not None else ""
                if raw_mode:
                    yield "", "", "", f"raw: {line}\n", ""
                parsed = _parse_sse_line(line)
                if parsed is None:
                    continue
                yield parsed
    except requests.RequestException as exc:
        yield "", "", "", "", f"request_error: {exc}"


def _submit(
    endpoint_url: str,
    token: str,
    model: str,
    prompt: str,
    image: Optional[Image.Image],
    thinking: bool,
    temperature: float,
    top_p: float,
    max_tokens: int,
    seed: int,
    freq_penalty: float,
    presence_penalty: float,
    raw_mode: bool,
    timeout: int,
    start_new_session: bool,
    session_state: Dict[str, Any],
) -> Generator[Tuple[str, str, str, str, Dict[str, Any], str], None, None]:
    if not token:
        err = "Missing token. Set HF_TOKEN or paste token in UI."
        yield "", "", "", err, session_state, session_state.get("session_id", "")
        return
    if not prompt.strip():
        err = "Prompt is required."
        yield "", "", "", err, session_state, session_state.get("session_id", "")
        return

    state = dict(session_state or {})
    if start_new_session or not state.get("messages"):
        state = {
            "session_id": _new_session_id(),
            "messages": [],
        }

    state["messages"] = _sanitize_history_for_send(list(state.get("messages", [])))

    user_message = {
        "role": "user",
        "content": _build_user_content(prompt.strip(), image),
    }
    req_messages: List[Dict[str, Any]] = list(state["messages"]) + [user_message]

    thinking_acc = ""
    content_acc = ""
    tools_acc = ""
    diag_acc = f"session={state['session_id']}\n"

    yield thinking_acc, content_acc, tools_acc, diag_acc, state, state["session_id"]

    for t_add, c_add, tool_add, d_add, err in _stream_request(
        endpoint_url=endpoint_url,
        token=token,
        model=model,
        messages=req_messages,
        thinking=thinking,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        seed=seed,
        freq_penalty=freq_penalty,
        presence_penalty=presence_penalty,
        raw_mode=raw_mode,
        timeout=timeout,
    ):
        if t_add:
            thinking_acc += t_add
        if c_add:
            content_acc += c_add
        if tool_add:
            tools_acc += tool_add
        if d_add:
            diag_acc += d_add
        if err:
            diag_acc += f"error: {err}\n"
            yield thinking_acc, content_acc, tools_acc, diag_acc, state, state["session_id"]
            return

        yield thinking_acc, content_acc, tools_acc, diag_acc, state, state["session_id"]

    assistant_message: Dict[str, Any] = {
        "role": "assistant",
        "content": content_acc,
    }

    state["messages"] = req_messages + [assistant_message]
    diag_acc += f"saved_turns={len(state['messages'])}\n"
    yield thinking_acc, content_acc, tools_acc, diag_acc, state, state["session_id"]


def _new_session(session_state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], str, str, str]:
    state = {
        "session_id": _new_session_id(),
        "messages": [],
    }
    diag = "created_new_session\n"
    return state["session_id"], state, "", "", diag


def _clear_outputs(session_state: Dict[str, Any]) -> Tuple[str, str, str, Dict[str, Any], str]:
    state = dict(session_state or {"session_id": _new_session_id(), "messages": []})
    return "", "", "", state, state.get("session_id", "")


def build_app() -> gr.Blocks:
    default_state = {"session_id": _new_session_id(), "messages": []}

    with gr.Blocks(title="HF VLM Stream Tester") as demo:
        gr.Markdown("# HF VLM Stream Tester (Direct SSE)")
        gr.Markdown("Calls Hugging Face OpenAI-compatible endpoint directly, no FastAPI agent layer.")

        session_state = gr.State(default_state)

        with gr.Row():
            endpoint = gr.Textbox(label="Endpoint", value=HF_ENDPOINT_URL)
            token = gr.Textbox(label="HF Token", value=HF_TOKEN, type="password")
            model = gr.Textbox(label="Model", value=VLM_MODEL)

        with gr.Row():
            session_id = gr.Textbox(label="Session ID (local tester state)", value=default_state["session_id"])
            start_new = gr.Checkbox(label="Start new session on submit", value=False)
            btn_new = gr.Button("New Session")
            btn_clear = gr.Button("Clear Output")

        prompt = gr.Textbox(label="Prompt", lines=5, placeholder="Ask the model...")
        image = gr.Image(type="pil", label="Optional image (VLM)")

        with gr.Accordion("Model Params", open=True):
            with gr.Row():
                thinking = gr.Checkbox(label="Thinking", value=True)
                temperature = gr.Slider(0.0, 2.0, value=0.6, step=0.01, label="temperature")
                top_p = gr.Slider(0.0, 1.0, value=0.95, step=0.01, label="top_p")
                max_tokens = gr.Slider(1, 8192, value=2048, step=1, label="max_tokens")
            with gr.Row():
                seed = gr.Number(value=-1, precision=0, label="seed (-1 disables)")
                freq_penalty = gr.Slider(-2.0, 2.0, value=0.0, step=0.01, label="frequency_penalty")
                presence_penalty = gr.Slider(-2.0, 2.0, value=0.0, step=0.01, label="presence_penalty")
                timeout = gr.Slider(10, 600, value=180, step=1, label="timeout_sec")
            raw_mode = gr.Checkbox(label="Raw SSE to diagnostics", value=False)

        submit = gr.Button("Send", variant="primary")

        with gr.Row():
            thinking_box = gr.Textbox(label="Thinking Stream", lines=20)
            content_box = gr.Textbox(label="Final Content Stream", lines=20)
        with gr.Row():
            tools_box = gr.Textbox(label="Tool Events", lines=12)
            diag_box = gr.Textbox(label="Diagnostics / Raw SSE", lines=12)

        submit.click(
            fn=_submit,
            inputs=[
                endpoint,
                token,
                model,
                prompt,
                image,
                thinking,
                temperature,
                top_p,
                max_tokens,
                seed,
                freq_penalty,
                presence_penalty,
                raw_mode,
                timeout,
                start_new,
                session_state,
            ],
            outputs=[thinking_box, content_box, tools_box, diag_box, session_state, session_id],
        )

        btn_new.click(
            fn=_new_session,
            inputs=[session_state],
            outputs=[session_id, session_state, thinking_box, content_box, diag_box],
        )

        btn_clear.click(
            fn=_clear_outputs,
            inputs=[session_state],
            outputs=[thinking_box, content_box, tools_box, session_state, session_id],
        )

    return demo


def main() -> None:
    app = build_app()
    app.launch(server_name="127.0.0.1", server_port=7861, show_error=True)


if __name__ == "__main__":
    main()

