import logging
import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool
from .tools import create_mcp_toolset, create_vertexai_mcp_toolset, search_with_gemini_enterprise_connector

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
# Load .env from parent directory explicitly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))

SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for security operations and threat intelligence. "
    "Your purpose is to use the provided tools to query VirusTotal for threat intelligence, "
    "Google SecOps (Chronicle) for security events, alerts, and entity information, "
    "Google Drive (via Discovery Engine) for related documents, "
    "and Jira for issue tracking and incident management. "
    "Help the user analyze potential threats, investigate security incidents, and manage related Jira issues. "
    "If the user asks about anything unrelated to cybersecurity or incident management, "
    "politely state that you cannot help with that topic."
)

logger.info("--- 🔧 Loading MCP tools from GTI and SecOps MCP Servers... ---")
logger.info("--- 🤖 Creating ADK Security Agent... ---")

gti_mcp_server_url = os.getenv("GTI_MCP_URL")
secops_mcp_server_url = os.getenv("SECOPS_MCP_URL")
jira_mcp_server_url = os.getenv("JIRA_MCP_URL")



# Using Vertex AI model path as requested
vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
vertex_model = f"projects/{vertex_project}/locations/us-central1/publishers/google/models/gemini-2.5-flash"



# Renamed to root_agent as requested
root_agent = Agent(
    model=vertex_model,
    name="security_data_agent",
    description="An agent that can help with threat intelligence and security operations",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        create_mcp_toolset(gti_mcp_server_url),
        create_mcp_toolset(secops_mcp_server_url),
        create_mcp_toolset(jira_mcp_server_url),
        # create_vertexai_mcp_toolset(),
        FunctionTool(search_with_gemini_enterprise_connector)
    ],
)

logger.info(f"ADK Agent created successfully, connected to {gti_mcp_server_url}")
logger.info(f"Using Vertex AI model: {vertex_model}")
