import asyncio
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


APP_NAME = "siteready_ai"
USER_ID = "gregory"
SESSION_ID = str(uuid.uuid4())


async def main() -> None:
    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    prompt = "Assess the readiness of contractor C003."

    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    print("\n=== SiteReady AI ===")
    print(f"User: {prompt}\n")

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        print(f"Agent: {part.text}")


if __name__ == "__main__":
    asyncio.run(main())