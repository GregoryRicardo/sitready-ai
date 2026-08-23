from google.adk.agents import Agent
from google.adk.models import Gemini


MODEL = "gemini-3.6-flash"


def lookup_contractor(contractor_id: str) -> dict:
    """
    Retrieve a contractor's details from SiteReady AI.

    Use this tool when the user asks for information about a
    specific contractor and provides a contractor ID such as C001.
    """
    from agent.tools.contractor_tools import get_contractor

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
5. When a contractor ID is supplied, use the contractor lookup tool.
6. Give concise, professional responses.
""",
    tools=[lookup_contractor],
)