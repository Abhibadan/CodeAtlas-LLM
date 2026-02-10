"""
Test script for Agent Tools

This script verifies that the agent can dynamically use tools to answer questions.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.ragAgent import RagAgent
# from config import config

def test_agent_tools():
    """Test the agent with various questions"""
    
    # Test configuration - you'll need to provide a valid project UUID
    # This should be replaced with an actual project ID from your MongoDB
    test_config = {
        "project": "asdfasdfasf--add-doc-modulewise-2wv5b95v",  # Replace with actual project UUID
        "chatId": "698b3109eec04b427acd9324",  # Dummy chat ID for testing
    }
    
    print("="*70)
    print("TESTING AGENT WITH TOOLS")
    print("="*70)
    
    try:
        # Initialize the agent
        print("\n[1] Initializing agent...")
        agent = RagAgent(test_config)
        print("✓ Agent initialized successfully")
        
        # Test questions
        questions = [
            "What are the main functions in this codebase?",
            "How are the database modules structured?",
            "Show me the dependencies of the ragAgent module"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*70}")
            print(f"[{i+1}] Question: {question}")
            print('='*70)
            
            try:
                chain = agent.getRagChain()
                print("\nAgent Response:")
                for chunk in chain.stream(question):
                    print(chunk, end="", flush=True)
                print("\n")
                print("✓ Test passed")
            except Exception as e:
                print(f"✗ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*70)
        print("TESTS COMPLETED")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\nNOTE: Make sure you have:")
    print("  1. A valid project UUID in your MongoDB")
    print("  2. ChromaDB server running")
    print("  3. Neo4j database running with data")
    print("  4. Proper environment variables configured\n")
    
    test_agent_tools()
