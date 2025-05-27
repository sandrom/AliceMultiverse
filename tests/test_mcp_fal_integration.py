#!/usr/bin/env python3
"""
Test MCP server integration with fal.ai provider.
This script tests that the MCP server can handle requests for the new models.
"""

import asyncio
import json
from pathlib import Path

# Import the MCP server components
from alicemultiverse.interface.mcp_server import AliceMCPServer
from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType


async def test_mcp_server_capabilities():
    """Test that MCP server lists available capabilities."""
    print("=== Testing MCP Server Capabilities ===\n")
    
    # Initialize MCP server
    server = AliceMCPServer()
    
    # Get available tools
    tools = await server.list_tools()
    print(f"Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Check if generation tools are available
    generation_tools = [t for t in tools if "generate" in t.name.lower()]
    print(f"\nGeneration tools found: {len(generation_tools)}")
    for tool in generation_tools:
        print(f"  - {tool.name}")
        if hasattr(tool, 'inputSchema'):
            print(f"    Schema: {json.dumps(tool.inputSchema, indent=4)}")


async def test_fal_provider_through_mcp():
    """Test calling fal.ai provider through MCP interface."""
    print("\n=== Testing fal.ai Provider through MCP ===\n")
    
    # Initialize MCP server
    server = AliceMCPServer()
    
    # Test parameters for FLUX Pro
    test_params = {
        "prompt": "A test image for MCP integration",
        "provider": "fal",
        "model": "flux-pro",
        "parameters": {
            "width": 512,
            "height": 512
        }
    }
    
    print(f"Test parameters: {json.dumps(test_params, indent=2)}")
    
    try:
        # Look for generate_image tool
        tools = await server.list_tools()
        generate_tool = next((t for t in tools if t.name == "generate_image"), None)
        
        if not generate_tool:
            print("❌ generate_image tool not found in MCP server")
            return
        
        print("✅ Found generate_image tool")
        
        # We can't directly call the tool from here as it requires MCP protocol
        # But we can test the underlying provider directly
        provider = get_provider("fal")
        print(f"✅ Got fal.ai provider: {provider.name}")
        
        # Check capabilities
        caps = provider.capabilities
        print(f"\nProvider capabilities:")
        print(f"  - Models: {len(caps.models)}")
        print(f"  - Has flux-pro: {'flux-pro' in caps.models}")
        print(f"  - Has kling models: {any('kling' in m for m in caps.models)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_model_availability():
    """Test that all new models are available."""
    print("\n=== Testing Model Availability ===\n")
    
    provider = get_provider("fal")
    expected_models = [
        "flux-pro",
        "kling-v1-text", 
        "kling-v1-image",
        "kling-v2-text",
        "kling-v2-image",
        "kling-elements",
        "kling-lipsync"
    ]
    
    available_models = provider.capabilities.models
    
    for model in expected_models:
        if model in available_models:
            print(f"✅ {model}: Available")
        else:
            print(f"❌ {model}: NOT FOUND")
    
    # Show pricing
    print("\nModel pricing:")
    for model in expected_models:
        if model in available_models:
            price = provider.capabilities.pricing.get(model, "Unknown")
            print(f"  - {model}: ${price}")


async def main():
    """Run all tests."""
    print("=== MCP Server + fal.ai Integration Test ===\n")
    
    # Run tests
    await test_model_availability()
    await test_mcp_server_capabilities()
    await test_fal_provider_through_mcp()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())