# =============================================
# DIGI-SCHOOL AI — Attendance Agent
# Built with LangGraph + llama3.1:8b via Ollama
# =============================================

from typing import Annotated, TypedDict, Optional
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from backend.models import AgentRequest, AgentResponse, AgentAction, AttendanceAction, FlagAction
from backend.tools.attendance_tools import (
    get_students_for_class,
    get_today_attendance,
    mark_attendance,
    flag_student,
    check_absence_threshold,
)


# ─── Agent state ─────────────────────────────

class AttendanceState(TypedDict):
    messages:   list          # full message history for the LLM
    teacher_id: int
    jwt_token:  str
    context:    dict          # classes + students passed from frontend
    actions:    list          # collected AgentAction objects
    done:       bool


# ─── Tools list ──────────────────────────────

TOOLS = [
    get_students_for_class,
    get_today_attendance,
    mark_attendance,
    flag_student,
    check_absence_threshold,
]

# ─── LLM setup ───────────────────────────────

def _build_llm():
    return ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0,          # deterministic — important for tools
    ).bind_tools(TOOLS)


# ─── System prompt ───────────────────────────

def _build_system_prompt(teacher_name: str, today: str, context: dict) -> str:
    classes_str  = "\n".join(f"  - ID {c['id']}: {c['name']}" for c in context.get("classes", []))
    students_str = "\n".join(
        f"  - ID {s['id']}: {s['name']} (class {s['class_name']}, class_id={s['class_id']})"
        for s in context.get("students", [])
    )

    return f"""You are the Attendance Agent for Digi-School AI, an intelligent assistant for teachers.

Today's date: {today}
Teacher: {teacher_name}

Your job:
1. Read the teacher's voice note or text input.
2. Identify every student mentioned and their attendance status (absent, late, present, excused).
3. Use the tools to mark attendance for each student you identify.
4. If a student has been mentioned as disruptive or problematic, use flag_student with type 'behavior'.
5. Use check_absence_threshold after marking absences to detect if auto-flagging is needed.
6. Call tools one at a time. Do not guess student IDs — use get_students_for_class first if needed.
7. Once all actions are done, respond with a clear summary of what you did.

Rules:
- Status codes: P = Present, A = Absent, L = Late, E = Excused
- If a student name is ambiguous, use get_students_for_class to find the correct ID.
- Never invent student IDs. Only use IDs from the context or tool results.
- If a teacher says "everyone was present" mark all students P.
- Only flag for absences if check_absence_threshold shows they exceed the threshold.

Available classes for this teacher:
{classes_str}

Available students:
{students_str}
"""


# ─── Graph nodes ─────────────────────────────

def agent_node(state: AttendanceState) -> AttendanceState:
    """Main LLM reasoning node."""
    llm = _build_llm()
    response = llm.invoke(state["messages"])
    state["messages"].append(response)

    # If no more tool calls → agent is done
    if not getattr(response, "tool_calls", None):
        state["done"] = True

    return state


def tool_node_with_token(state: AttendanceState) -> AttendanceState:
    """
    Custom tool node that injects jwt_token and teacher_id into
    tools that need them (mark_attendance, flag_student).
    """
    last_message = state["messages"][-1]
    tool_calls   = getattr(last_message, "tool_calls", [])

    tool_map = {t.name: t for t in TOOLS}
    results  = []

    for tc in tool_calls:
        tool_name = tc["name"]
        tool_args = dict(tc["args"])

        # Inject auth into write tools
        if tool_name in ("mark_attendance", "flag_student"):
            tool_args["jwt_token"]  = state["jwt_token"]
            tool_args["teacher_id"] = state["teacher_id"]

        # Inject teacher_id into read tools
        if tool_name in ("get_students_for_class", "get_today_attendance"):
            tool_args["teacher_id"] = state["teacher_id"]

        tool_fn = tool_map.get(tool_name)
        if tool_fn:
            try:
                result = tool_fn.invoke(tool_args)
            except Exception as e:
                result = {"success": False, "message": str(e)}
        else:
            result = {"success": False, "message": f"Unknown tool: {tool_name}"}

        # Collect action for the response summary
        if tool_name == "mark_attendance" and isinstance(result, dict) and result.get("success"):
            state["actions"].append({
                "type":        "attendance",
                "description": result["message"],
                "data":        tool_args,
            })
        elif tool_name == "flag_student" and isinstance(result, dict) and result.get("success"):
            state["actions"].append({
                "type":        "flag",
                "description": result["message"],
                "data":        tool_args,
            })

        results.append(
            ToolMessage(
                tool_call_id=tc["id"],
                content=str(result),
            )
        )

    state["messages"].extend(results)
    return state


def should_continue(state: AttendanceState) -> str:
    """Router: keep looping if there are tool calls, stop when done."""
    if state.get("done"):
        return "end"
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"


# ─── Build the graph ─────────────────────────

def build_attendance_graph() -> StateGraph:
    graph = StateGraph(AttendanceState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node_with_token)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )

    graph.add_edge("tools", "agent")

    return graph.compile()


# ─── Public entry point ───────────────────────

async def run_attendance_agent(request: AgentRequest, jwt_token: str) -> AgentResponse:
    """
    Called by main.py when POST /agent/run arrives.
    Returns a structured AgentResponse.
    """
    today   = request.context.date
    context = {
        "classes":  [c.model_dump() for c in request.context.classes],
        "students": [s.model_dump() for s in request.context.students],
    }

    system_prompt = _build_system_prompt(
        teacher_name=request.teacher.name,
        today=today,
        context=context,
    )

    initial_state: AttendanceState = {
        "messages":   [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.input),
        ],
        "teacher_id": request.teacher.id,
        "jwt_token":  jwt_token,
        "context":    context,
        "actions":    [],
        "done":       False,
    }

    graph  = build_attendance_graph()
    result = await graph.ainvoke(initial_state)

    # Extract final text response from last AI message
    final_text = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            final_text = msg.content
            break

    if not final_text:
        action_count = len(result["actions"])
        final_text = f"Attendance agent completed {action_count} action(s)."

    return AgentResponse(
        summary=final_text,
        actions=[AgentAction(**a) for a in result["actions"]],
        raw={"message_count": len(result["messages"])},
    )