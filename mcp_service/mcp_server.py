import os
import sys

# Asegurar path de mattermost-agents-hub
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from mcp_service.tools.mattermost_tools import (
    mattermost_get_my_profile,
    mattermost_list_my_teams,
    mattermost_list_my_channels,
    mattermost_get_channel_by_name,
    mattermost_get_channel_posts,
    mattermost_get_thread,
    mattermost_create_post,
    mattermost_search_posts,
)

mcp = FastMCP("mattermost-gateway")

mcp.tool()(mattermost_get_my_profile)
mcp.tool()(mattermost_list_my_teams)
mcp.tool()(mattermost_list_my_channels)
mcp.tool()(mattermost_get_channel_by_name)
mcp.tool()(mattermost_get_channel_posts)
mcp.tool()(mattermost_get_thread)
mcp.tool()(mattermost_create_post)
mcp.tool()(mattermost_search_posts)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ["http", "sse"]:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8017))
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.transport_security = None
        print(f"Iniciando mattermost-gateway en modo SSE (http://{host}:{port}/sse)...")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
