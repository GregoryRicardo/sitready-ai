import uuid

from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


APP_NAME = "siteready_ai"
USER_ID = "web_user"
TASKMASTER_TOOL = "run_taskmaster_workflow"


async def run_taskmaster_via_adk(contractor_id: str) -> dict:
    """Run the Taskmaster workflow through the ADK/Gemini agent once.

    The Gemini agent is responsible for selecting the authoritative
    Taskmaster tool. The Taskmaster tool remains responsible for policy,
    persistence, human approval, actions, notifications, and verification.
    """
    contractor_id = contractor_id.strip().upper()
    if not contractor_id:
        raise ValueError("contractor_id is required.")

    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    prompt = (
        "Run the complete SiteReady Taskmaster workflow for contractor "
        f"{contractor_id}. You MUST use the run_taskmaster_workflow tool "
        "and return its structured result. Do not execute follow-up actions "
        "outside that tool."
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    tool_result: dict | None = None
    final_text: str | None = None

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        _capture_taskmaster_tool_response(event, tool_result_holder := locals())
        if event.is_final_response() and event.content and event.content.parts:
            texts = [
                part.text
                for part in event.content.parts
                if getattr(part, "text", None)
            ]
            if texts:
                final_text = "\n".join(texts)

    tool_result = tool_result_holder.get("tool_result")
    if tool_result is None:
        raise RuntimeError(
            "ADK completed without returning a run_taskmaster_workflow tool result."
            + (f" Agent response: {final_text}" if final_text else "")
        )

    if not isinstance(tool_result, dict):
        raise RuntimeError("Taskmaster tool returned a non-object result.")

    return tool_result


def _capture_taskmaster_tool_response(event: Event, holder: dict) -> None:
    """Capture the authoritative Taskmaster tool response from an ADK event."""
    for function_response in event.get_function_responses() or []:
        if getattr(function_response, "name", None) != TASKMASTER_TOOL:
            continue

        response = getattr(function_response, "response", None)
        if isinstance(response, dict):
            holder["tool_result"] = response
