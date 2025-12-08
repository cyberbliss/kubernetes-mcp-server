#!/usr/bin/env python3
"""
Test script for Kubernetes MCP Server with ServiceAccount token authentication.

This script tests the token passthrough mechanism using the MCP Python SDK's
streamable HTTP client transport.

Usage:
    export TOKEN=$(kubectl create token default -n default --duration=10m)
    uv run --with mcp main.py
"""

import asyncio
import os
import sys

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


# Get configuration from environment
TOKEN = os.environ.get("TOKEN")
MCP_ENDPOINT = os.environ.get("MCP_ENDPOINT", "http://localhost:9080/mcp")
NAMESPACE = os.environ.get("NAMESPACE", "default")


async def test_mcp_client():
    """Test MCP client with Authorization header."""
    
    if not TOKEN:
        print("ERROR: TOKEN environment variable not set", file=sys.stderr)
        print("Usage: export TOKEN=$(kubectl create token default -n default --duration=10m)", file=sys.stderr)
        sys.exit(1)
    
    print(f"Connecting to MCP server at {MCP_ENDPOINT}")
    print(f"Using namespace: {NAMESPACE}")
    print(f"Using token: {TOKEN[:20]}...{TOKEN[-20:]}\n")

    # Connect to streamable HTTP server with Authorization header
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        async with streamablehttp_client(MCP_ENDPOINT, headers=headers, timeout=30.0) as (
            read_stream,
            write_stream,
            get_session_id,
        ):
            # Create a session using the client streams
            async with ClientSession(read_stream, write_stream) as session:
                # 1. Initialize the connection
                print("1. Initializing connection...")
                result = await session.initialize()
                print(f"   Server: {result.serverInfo.name} v{result.serverInfo.version}")
                print(f"   Protocol version: {result.protocolVersion}")
                session_id = get_session_id()
                if session_id:
                    print(f"   Session ID: {session_id}")

                # 2. List available tools
                print("\n2. Listing available tools...")
                tools = await session.list_tools()
                print(f"   Found {len(tools.tools)} tools:")
                for tool in tools.tools[:5]:  # Show first 5
                    desc = tool.description or "(no description)"
                    print(f"   - {tool.name}: {desc[:60]}...")
                if len(tools.tools) > 5:
                    print(f"   ... and {len(tools.tools) - 5} more")

                # 3. Call pods_list tool
                print(f"\n3. Calling pods_list tool (namespace={NAMESPACE})...")
                try:
                    pods_result = await session.call_tool("pods_list", arguments={"namespace": NAMESPACE})
                    content_str = str(pods_result.content)[:300]
                    print(f"   Result: {content_str}...")
                    print("   ✅ Successfully called pods_list")
                except Exception as e:
                    print(f"   ❌ Error calling pods_list: {e}")

                # 4. Call resources_list tool for ConfigMaps
                print(f"\n4. Calling resources_list tool (ConfigMaps in {NAMESPACE})...")
                try:
                    resources_result = await session.call_tool(
                        "resources_list",
                        arguments={
                            "apiVersion": "v1",
                            "kind": "ConfigMap",
                            "namespace": NAMESPACE
                        }
                    )
                    content_str = str(resources_result.content)[:300]
                    print(f"   Result: {content_str}...")
                    print("   ✅ Successfully called resources_list")
                except Exception as e:
                    print(f"   ❌ Error calling resources_list: {e}")

        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_mcp_client())
