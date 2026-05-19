import logging
import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool
from .tools import create_mcp_toolset, search_with_gemini_enterprise_connector

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
# Load .env from parent directory explicitly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, ".env"))

SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for security operations and threat intelligence, acting as a SOC Analyst support system. "
    "You should engage in normal conversation and answer general questions politely if they are not related to shift prioritization. "
    "Your primary goal is to help analysts prioritize their workload when they log in for their shift or ask for priorities. "
    "When a user indicates they are starting their shift or asks for priorities, you must perform the following workflow:\n"
    "1. **Data Aggregation**: Query Jira (via Jira MCP) for open tickets and Google SecOps (via SecOps MCP) for active, critical severity alerts.\n"
    "2. **Contextual Synthesis**: Cross-reference Jira ticket priorities with live SecOps telemetry to validate the fidelity of the alerts.\n"
    "3. **Playbook Retrieval**: After identifying top priorities, use the `search_with_gemini_enterprise_connector` tool to search for related incident response playbooks in Cloud Storage. Suggest relevant playbooks in your response.\n"
    "4. **Structured Output**: Provide a response with exactly these sections:\n"
    "   - **Step 1: The Top 5 List**: A clean, sifted list of the top 5 issues based on ticket/alert priority.\n"
    "   - **Step 2: The Attack Plan**: Explicitly instruct the user on *which* ticket to tackle first, establishing a clear, ordered roadmap for their first hour.\n"
    "   - **Step 3: The Reasoning Engine**: A brief, human-readable justification for this prioritization (e.g., why one ticket is more urgent than another despite age). Mention relevant playbooks found.\n\n"
    "## RULE ##\n"
    "At the end of your response, you must accurately list ONLY the tools you specifically invoked to answer the CURRENT query in this turn. "
    "For each tool used, you must specify: "
    "1. The name of the tool. "
    "2. The arguments used for the call. "
    "3. The source or MCP server it belongs to (e.g., 'GTI MCP', 'SecOps MCP', 'Jira MCP', 'Gemini Enterprise'). "
    "If a tool name is generic like 'default_api.search', identify its source server correctly. "
    "If you did not use any tools, state that clearly."
)

logger.info("--- 🔧 Loading MCP tools from GTI and SecOps MCP Servers... ---")
logger.info("--- 🤖 Creating ADK Security Agent... ---")

gti_mcp_server_url = os.getenv("GTI_MCP_URL")
secops_mcp_server_url = os.getenv("SECOPS_MCP_URL")
jira_mcp_server_url = os.getenv("JIRA_MCP_URL")



# Using Vertex AI model path as requested
vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
# vertex_model = f"projects/{vertex_project}/locations/us-central1/publishers/google/models/gemini-2.5-flash"



# Renamed to root_agent as requested
root_agent = Agent(
    model="gemini-3.1-flash-lite-preview",
    name="security_data_agent",
    description="An agent that can help with threat intelligence and security operations",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        create_mcp_toolset(gti_mcp_server_url),
        create_mcp_toolset(secops_mcp_server_url),
        create_mcp_toolset(jira_mcp_server_url),
        FunctionTool(search_with_gemini_enterprise_connector)
    ],
)

logger.info(f"ADK Agent created successfully, connected to {gti_mcp_server_url}")
