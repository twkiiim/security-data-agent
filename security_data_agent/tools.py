import logging
import os
import re
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.protobuf.json_format import MessageToDict
from google.oauth2.credentials import Credentials
from google.adk.tools import ToolContext, FunctionTool
from .utils import get_id_token


logger = logging.getLogger(__name__)

def search_with_gemini_enterprise_connector(query_text: str, tool_context: ToolContext):
    """Performs a search using the official Google Cloud Discovery Engine client library (v1alpha)."""
    try:
        # token = _get_access_token_from_context(tool_context)
        # credentials = Credentials(token=token)
        # client = discoveryengine.SearchServiceClient(credentials=credentials)
        client = discoveryengine.SearchServiceClient()
        logger.info("Using token from context for SearchServiceClient")
    except Exception as e:
        logger.info(f"Falling back to default credentials for SearchServiceClient: {e}")
        client = discoveryengine.SearchServiceClient()
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_NUMBER")
    data_store = os.getenv("GEMINI_ENTERPRISE_DATA_STORE")
    serving_config = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/{data_store}/servingConfigs/default_search"

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query_text,
    )
    response = client.search(request)
    return [MessageToDict(result._pb) for result in response.results]


def create_mcp_toolset(url: str) -> McpToolset:
    if not url:
        raise ValueError("MCP URL cannot be None")
        
    if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
        logger.info(f"Connecting to local MCP server at {url}")
        params = StreamableHTTPConnectionParams(url=url)
    else:
        logger.info(f"Connecting to remote MCP server at {url}")
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        audience = f"{parsed_url.scheme}://{parsed_url.netloc}"
        token = get_id_token(audience)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        params = StreamableHTTPConnectionParams(url=url, headers=headers)
        
    return McpToolset(connection_params=params)


# CLIENT_AUTH_NAME = "security-agent-google-workspace"
CLIENT_AUTH_NAME = "security-agent-gws-oauth"

def _get_access_token_from_context(tool_context: ToolContext) -> str:
    """Helper method to dynamically parse the intercepted bearer token from the context state."""
    escaped_name = re.escape(CLIENT_AUTH_NAME)
    pattern = re.compile(fr"^{escaped_name}_\d+$")
    state_dict = tool_context.state.to_dict() if hasattr(tool_context.state, 'to_dict') else tool_context.state
    matching_keys = [k for k in state_dict.keys() if pattern.match(k)]
    if matching_keys:
        return state_dict.get(matching_keys[0])
    raise Exception(f"No bearer token found in ToolContext state matching pattern {pattern.pattern}")

