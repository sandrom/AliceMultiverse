#!/usr/bin/env python3
"""Demonstration of Alice Orchestrator - The intelligent creative interface.

This example shows how AI assistants can interact with Alice using
natural language, and how Alice understands creative chaos.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.interface import ask_alice, AliceAPI, AliceMCP


async def demonstrate_natural_language():
    """Show natural language understanding."""
    print("\n🎨 Alice Natural Language Demo")
    print("=" * 50)
    
    # Example queries an AI might ask
    queries = [
        "Find that cyberpunk character with neon colors from last month",
        "Show me all the dark moody images we created yesterday",
        "Remember what styles we've been working with",
        "Create a futuristic city scene with vibrant neon lights",
        "Find images similar to the hero character",
        "What creative patterns have we been using?"
    ]
    
    for query in queries:
        print(f"\n🤖 AI: {query}")
        response = await ask_alice(query)
        
        print(f"🎨 Alice: {response['message']}")
        
        if response.get('suggestions'):
            print("   Suggestions:")
            for suggestion in response['suggestions']:
                print(f"   - {suggestion}")
        
        if response.get('data', {}).get('context'):
            print("   Context:", response['data']['context'])
        
        await asyncio.sleep(0.5)  # Pause for readability


async def demonstrate_creative_memory():
    """Show how Alice maintains creative memory."""
    print("\n\n🧠 Alice Creative Memory Demo")
    print("=" * 50)
    
    alice = AliceAPI()
    
    # Simulate creative session
    print("\n📝 Simulating creative work session...")
    
    # Search for inspiration
    await alice.request("Find cyberpunk references")
    await alice.request("Find neon color palettes")
    
    # Create based on findings
    await alice.request("Create a cyberpunk character with neon accents")
    
    # Check memory
    print("\n🔍 Checking Alice's memory...")
    memory = await alice.remember()
    
    print(f"🎨 Alice remembers:")
    if memory.get('memory'):
        for key, value in memory['memory'].items():
            print(f"   {key}: {value}")


async def demonstrate_mcp_integration():
    """Show MCP-style integration."""
    print("\n\n🔌 Alice MCP Integration Demo")
    print("=" * 50)
    
    # This is how an MCP server might expose Alice
    alice_mcp = AliceMCP()
    
    print("\n📡 MCP-style function calls:")
    
    # Search
    print("\n→ alice_mcp.search('retro futuristic images')")
    result = alice_mcp.search("retro futuristic images")
    print(f"← {result['message']}")
    
    # Create
    print("\n→ alice_mcp.create('a dreamy landscape with pastel colors')")
    result = alice_mcp.create("a dreamy landscape with pastel colors")
    print(f"← {result['message']}")
    
    # Remember
    print("\n→ alice_mcp.remember('style preferences')")
    result = alice_mcp.remember("style preferences")
    print(f"← {result['message']}")
    
    # Explore
    print("\n→ alice_mcp.explore('the cyberpunk theme')")
    result = alice_mcp.explore("the cyberpunk theme")
    print(f"← {result['message']}")


async def demonstrate_creative_chaos():
    """Show how Alice handles creative chaos."""
    print("\n\n🌪️  Alice Creative Chaos Demo")
    print("=" * 50)
    
    # Chaotic, non-linear queries like real creative work
    chaotic_queries = [
        "Where's that thing with the purple glow?",
        "Make it more... you know, like that other one",
        "The one from October but more intense",
        "Find stuff that feels like blade runner meets disney",
        "Remember that cool effect we did?",
        "Something dark but not too dark, with energy"
    ]
    
    alice = AliceAPI()
    
    for query in chaotic_queries:
        print(f"\n💭 Creative mind: {query}")
        response = await alice.request(query)
        print(f"🎨 Alice: {response['message']}")
        
        # Alice provides helpful suggestions for vague requests
        if response.get('suggestions'):
            print("   💡 Alice suggests:")
            for suggestion in response['suggestions'][:2]:
                print(f"      - {suggestion}")


async def main():
    """Run all demonstrations."""
    print("🎨 AliceMultiverse Orchestrator Demo")
    print("Showing how AI assistants interact with Alice")
    print("=" * 50)
    
    try:
        await demonstrate_natural_language()
        await demonstrate_creative_memory()
        await demonstrate_mcp_integration()
        await demonstrate_creative_chaos()
        
        print("\n\n✨ Demo Complete!")
        print("Alice is ready to orchestrate creative workflows.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Some features require database setup.")
        print("Run 'alembic upgrade head' to initialize the database.")


if __name__ == '__main__':
    asyncio.run(main())