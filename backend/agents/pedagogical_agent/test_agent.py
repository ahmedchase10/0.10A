"""
Raw SSE dump utility for the pedagogical-agent model endpoint.

This file intentionally contains ONE test flow only:
- Send a streaming chat/completions request directly to the model endpoint
- Dump every raw SSE frame to an output file

Use it when you want to inspect the exact wire payload (including delta keys)
without going through LangChain or LangGraph abstractions.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

import requests

# Allow direct script execution: python backend/agents/pedagogical_agent/test_agent.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import HF_ENDPOINT_URL, HF_TOKEN, VLM_MODEL


def _iso_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _resolve_chat_url(endpoint_base: str) -> str:
    base = endpoint_base.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _build_payload(model: str, prompt: str, thinking: bool, max_tokens: int) -> Dict:
    # Keep payload explicit so raw SSE behavior is easy to reason about in dumps.
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.6 if thinking else 0.7,
        "top_p": 0.95 if thinking else 0.8,
        # Some OpenAI-compatible servers ignore this; others map it to parser behavior.
        "chat_template_kwargs": {
            "enable_thinking": thinking,
            "preserve_thinking": True,
        },
        # Some servers use this newer switch directly.
        "think": thinking,
    }


def _write_lines(path: Path, lines: Iterable[str], append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as f:
        for line in lines:
            f.write(line)
            if not line.endswith("\n"):
                f.write("\n")


def _header_block(label: str, url: str, model: str, thinking: bool) -> str:
    return (
        "\n"
        "------------------------------------------------------------\n"
        f"RAW SSE DUMP  [{label}]\n"
        f"timestamp: {_iso_now()}\n"
        f"url: {url}\n"
        f"model: {model}\n"
        f"thinking: {'ON' if thinking else 'OFF'}\n"
        "------------------------------------------------------------\n"
    )


def _run_single_dump(
    *,
    url: str,
    token: str,
    model: str,
    prompt: str,
    thinking: bool,
    out_file: Path,
    append: bool,
    timeout: int,
    max_tokens: int,
) -> int:
    payload = _build_payload(model=model, prompt=prompt, thinking=thinking, max_tokens=max_tokens)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    lines = [
        _header_block("REQUEST", url, model, thinking),
        "request_payload_json:\n",
        json.dumps(payload, ensure_ascii=True, indent=2),
        "\n\n",
    ]
    _write_lines(out_file, lines, append=append)

    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout) as resp:
            if resp.status_code >= 400:
                body = resp.text
                err_lines = [
                    _header_block("HTTP_ERROR", url, model, thinking),
                    f"status: {resp.status_code}\n",
                    "body:\n",
                    body,
                    "\n",
                ]
                _write_lines(out_file, err_lines, append=True)
                print(f"[{('ON' if thinking else 'OFF')}] HTTP {resp.status_code} (written to {out_file})")
                return 1

            start_lines = [
                _header_block("SSE_STREAM_START", url, model, thinking),
            ]
            _write_lines(out_file, start_lines, append=True)

            frame_count = 0
            data_count = 0
            done_seen = False

            # Keep empty lines to preserve SSE frame boundaries in the dump.
            for raw_line in resp.iter_lines(decode_unicode=True):
                line = raw_line if raw_line is not None else ""
                _write_lines(out_file, [line], append=True)

                if line.startswith("data:"):
                    data_count += 1
                    if line.strip() == "data: [DONE]":
                        done_seen = True
                if line == "":
                    frame_count += 1

            end_lines = [
                _header_block("SSE_STREAM_END", url, model, thinking),
                f"frames: {frame_count}\n",
                f"data_lines: {data_count}\n",
                f"done_seen: {done_seen}\n",
            ]
            _write_lines(out_file, end_lines, append=True)

            print(
                f"[{('ON' if thinking else 'OFF')}] stream saved -> {out_file} "
                f"(frames={frame_count}, data_lines={data_count}, done={done_seen})"
            )
            return 0

    except requests.RequestException as exc:
        err_lines = [
            _header_block("REQUEST_EXCEPTION", url, model, thinking),
            f"error: {exc}\n",
        ]
        _write_lines(out_file, err_lines, append=True)
        print(f"[{('ON' if thinking else 'OFF')}] request error: {exc}")
        return 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Single-purpose raw SSE dump tester for an OpenAI-compatible endpoint."
    )
    parser.add_argument(
        "--endpoint",
        default=HF_ENDPOINT_URL,
        help="Endpoint base URL (e.g. .../v1) or full .../chat/completions URL.",
    )
    parser.add_argument(
        "--token",
        default=HF_TOKEN,
        help="Bearer token. Defaults to HF_TOKEN from backend config.",
    )
    parser.add_argument(
        "--model",
        default=VLM_MODEL,
        help="Model id to request.",
    )
    parser.add_argument(
        "--prompt",
        default="Explain the derivative of x^2 in one short paragraph.",
        help="Prompt to send.",
    )
    parser.add_argument(
        "--thinking",
        choices=["on", "off", "both"],
        default="both",
        help="Run with thinking ON, OFF, or both sequentially.",
    )
    parser.add_argument(
        "--output",
        default="dump_rawsse.txt",
        help="Output dump file path.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to output file instead of overwrite.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="max_tokens sent to the endpoint.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if not args.token:
        print("Missing token: pass --token or set HF_TOKEN in environment.")
        return 2

    chat_url = _resolve_chat_url(args.endpoint)
    out_file = Path(args.output).resolve()

    modes = [args.thinking] if args.thinking in {"on", "off"} else ["on", "off"]

    # First run honors --append; subsequent runs in the same invocation always append.
    first_write_append = args.append
    exit_codes = []

    for i, mode in enumerate(modes):
        code = _run_single_dump(
            url=chat_url,
            token=args.token,
            model=args.model,
            prompt=args.prompt,
            thinking=(mode == "on"),
            out_file=out_file,
            append=(first_write_append if i == 0 else True),
            timeout=args.timeout,
            max_tokens=args.max_tokens,
        )
        exit_codes.append(code)

    return 0 if all(code == 0 for code in exit_codes) else 1


if __name__ == "__main__":
    sys.exit(main())
