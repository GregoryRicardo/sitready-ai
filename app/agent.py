from google.adk.agents import Agent
from google.adk.models import Gemini

from agent.tools.contractor_tools import get_contractor
from agent.tools.readiness_tools import assess_contractor_readiness

from agent.tools.followup_orchestration import (
    create_followup_actions_for_readiness,
)

MODEL = "gemini-3.6-flash"


def lookup_contractor(contractor_id: str) -> dict:
    """
    Retrieve a contractor's details from SiteReady AI.

    Use this tool when the user asks for information about a
    specific contractor and provides a contractor ID such as C001.
    """
    return get_contractor(contractor_id)


root_agent = Agent(
    name="siteready_agent",
    model=Gemini(model=MODEL),
    instruction="""
You are SiteReady AI, an autonomous contractor-readiness assistant.

Your job is to help users assess contractor readiness using
verified SiteReady AI data.

Rules:

1. Do not invent contractor information.

2. Use the available tools to retrieve factual information.

3. Clearly distinguish retrieved facts from conclusions.

4. Do not make legal claims or invent H&S requirements.

5. When a contractor ID is supplied and the user asks for
   contractor information, use the contractor lookup tool.

6. When the user asks to assess, evaluate, check, or determine
   the readiness of a contractor, use the readiness assessment tool.

7. The readiness assessment tool is the authoritative source for
   the contractor's readiness status, risk level, and identified issues.
   Do not calculate or override the readiness result yourself.

8. Present readiness results clearly, including:
   - Contractor
   - Readiness status
   - Risk level
   - Issues identified

9. Give concise, professional responses.

10. Never claim that an action was created, completed, or updated
    unless a tool actually performed that operation.
""",
    tools=[
        lookup_contractor,
        assess_contractor_readiness,
	create_followup_actions_for_readiness,
    ],
)