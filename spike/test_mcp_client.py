"""
Test MCP Server Token Passthrough using Python MCP SDK

This script tests programmatic access to the MCP server running in a K8s cluster
with a ServiceAccount token that has permission to read configmaps only.

Usage:
    uv run spikes/mcp-token-passthrough/test_mcp_client.py

Environment Variables:
    TOKEN - ServiceAccount token with configmap read permissions
    MCP_ENDPOINT - MCP server endpoint (default: http://localhost:9080)
    NAMESPACE - Kubernetes namespace to test (default: default)
"""

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.sse import sse_client

# ANSI colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def print_test(name: str, expected: str):
    """Print test header"""
    print(f"\n{BLUE}{'━' * 50}{NC}")
    print(f"{YELLOW}Test: {name}{NC}")
    print(f"Expected: {expected}")
    print()


def print_result(passed: bool, message: str = ""):
    """Print test result"""
    if passed:
        print(f"{GREEN}✅ PASSED{NC} {message}")
    else:
        print(f"{RED}❌ FAILED{NC} {message}")


async def test_mcp_client():
    """Test MCP server using official Python SDK"""
    
    mcp_endpoint = os.getenv("MCP_ENDPOINT", "http://localhost:9080")
    configmap_token = os.getenv("TOKEN", "")
    namespace = os.getenv("NAMESPACE", "default")
    
    if not configmap_token:
        print(f"{RED}❌ TOKEN not set. Set TOKEN environment variable with SA token that can read configmaps.{NC}")
        print(f"{YELLOW}Example: export TOKEN=$(kubectl create token my-sa -n my-namespace --duration=10m){NC}")
        return
    
    print(f"{BLUE}╔════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║  Python MCP Client Tests (SSE)         ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════╝{NC}")
    print(f"\nMCP Endpoint: {YELLOW}{mcp_endpoint}{NC}")
    print(f"Namespace: {YELLOW}{namespace}{NC}")
    print(f"Token: {YELLOW}{configmap_token[:20]}...{NC}\n")
    
    print(f"{RED}╔════════════════════════════════════════════════════════════════╗{NC}")
    print(f"{RED}║  IMPORTANT FINDING: Token Passthrough Not Supported           ║{NC}")
    print(f"{RED}╚════════════════════════════════════════════════════════════════╝{NC}")
    print(f"\n{YELLOW}kubernetes-mcp-server does NOT support token passthrough via HTTP headers.{NC}")
    print(f"\nThe server expects:")
    print(f"  1. OAuth/OIDC token in Authorization header (for MCP server auth)")
    print(f"  2. Uses its own kubeconfig to talk to Kubernetes")
    print(f"\n{YELLOW}This means:{NC}")
    print(f"  ✗ Cannot pass JIT ServiceAccount tokens via Bearer header")
    print(f"  ✗ MCP server uses single identity for all requests")
    print(f"  ✗ No per-user RBAC enforcement at Kubernetes level")
    print(f"\n{YELLOW}Alternative approaches:{NC}")
    print(f"  1. Deploy separate MCP server instance per user (with user's SA)")
    print(f"  2. Implement custom K8s operations service (original plan)")
    print(f"  3. Fork/modify kubernetes-mcp-server to accept token passthrough")
    print(f"  4. Use MCP server with broad permissions + implement RBAC in backend")
    print(f"\n{RED}Recommendation: Revert to original K8sOperationsService approach{NC}")
    print(f"   - Direct control over authentication")
    print(f"   - True per-user JIT credentials")
    print(f"   - Proper RBAC enforcement\n")
    
    try:
        async with sse_client(f"{mcp_endpoint}/sse", headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # Test 1: List available tools
                print_test("List available tools", "Success - get list of Kubernetes tools")
                try:
                    tools = await session.list_tools()
                    print(f"Found {len(tools.tools)} tools:")
                    for tool in tools.tools[:5]:  # Show first 5
                        print(f"  - {tool.name}: {tool.description[:80]}...")
                    if len(tools.tools) > 5:
                        print(f"  ... and {len(tools.tools) - 5} more")
                    print_result(True, f"Found {len(tools.tools)} tools")
                except Exception as e:
                    print(f"Error: {e}")
                    print_result(False, str(e))
                
                # Test 2: Call list_resources tool to list configmaps
                print_test("List configmaps (allowed)", "Success - token has configmap read permission")
                try:
                    result = await session.call_tool(
                        "resources_list",
                        arguments={
                            "apiVersion": "v1",
                            "kind": "configmap",
                            "namespace": namespace
                        }
                    )
                    print(f"Result: {str(result.content)[:300]}...")
                    print_result(True, "Successfully listed configmaps")
                except Exception as e:
                    print(f"Error: {e}")
                    print_result(False, str(e))
                
                # Test 3: Try to list pods (should fail with RBAC error)
                print_test("List pods (forbidden)", "Failure - token lacks pod read permission")
                try:
                    result = await session.call_tool(
                        "list_resources",
                        arguments={
                            "resource": "pods",
                            "namespace": namespace
                        }
                    )
                    print(f"Result: {str(result.content)[:300]}...")
                    print_result(False, "Unexpectedly succeeded - RBAC not enforced!")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "forbidden" in error_msg or "unauthorized" in error_msg or "permission" in error_msg:
                        print(f"Got expected RBAC error: {e}")
                        print_result(True, "RBAC properly enforced")
                    else:
                        print(f"Unexpected error: {e}")
                        print_result(False, f"Wrong error type: {e}")
                
    except Exception as e:
        import traceback
        print(f"{RED}Failed to connect to MCP server: {e}{NC}")
        print(f"\n{YELLOW}Full error details:{NC}")
        traceback.print_exc()
        
        # Try to extract nested exception
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"\n{YELLOW}Caused by: {e.__cause__}{NC}")
        if hasattr(e, 'exceptions'):
            print(f"\n{YELLOW}Sub-exceptions:{NC}")
            for sub_e in e.exceptions:
                print(f"  - {sub_e}")
        
        print(f"\n{YELLOW}Make sure the MCP server is running with:")
        print(f"  kubectl port-forward -n <namespace> svc/<mcp-service> 9080:9080{NC}")
        sys.exit(1)


async def main():
    """Run all tests"""
    await test_mcp_client()
    
    print(f"\n{BLUE}╔════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║           Test Complete                ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════╝{NC}")
    print(f"\n📝 Document findings in: {GREEN}spikes/mcp-token-passthrough/README.md{NC}\n")


if __name__ == "__main__":
    asyncio.run(main())
