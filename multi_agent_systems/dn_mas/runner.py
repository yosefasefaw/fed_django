import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import dn_mas


async def dn_mas_runner(initial_state):
    APP_NAME = "dn_mas"
    USER_ID = "system"

    session_id = str(uuid.uuid4())
    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
        state=initial_state,
    )

    agent_runner = Runner(
        app_name=APP_NAME,
        agent=dn_mas,
        session_service=session_service,
        artifact_service=None,
        memory_service=None,
    )

    # Create the initial message to trigger the pipeline
    user_message = types.Content(
        role="user",
        parts=[
            types.Part(text="Please process the articles and provide a cited summary.")
        ],
    )

    # Run the agent pipeline to completion
    async for event in agent_runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=user_message,
    ):
        pass  # Process all events to completion

    # Retrieve the session to access the updated state with output_keys
    completed_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    return completed_session.state
