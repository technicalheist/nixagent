#!/usr/bin/env python3
"""
AI Agent Application

This application allows you to interact with an AI agent that can use various tools
to answer questions and perform tasks. It uses the new generic Agent framework.
"""

from dotenv import load_dotenv
load_dotenv()

import sys
import argparse
import json
from nixagent import Agent

def main():
    parser = argparse.ArgumentParser(
        description="AI Agent that can use tools to answer questions and perform tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('question', nargs='?', help='The question to ask the agent')
    parser.add_argument('-q', '--question', dest='question_flag', help='Alternative to positional argument')
    parser.add_argument('--no-save', action='store_true', help='Do not save the conversation history')
    parser.add_argument('--messages-file', default='messages.json', help='Filename to save history')
    
    args = parser.parse_args()
    
    question = args.question or args.question_flag
    
    # Initialize the core agent
    agent = Agent(
        name="Main",
        system_prompt="You are a highly capable AI assistant that uses available tools to accomplish the user's goals. You must analyze the task carefully and execute the appropriate actions."
    )
    
    if not question:
        print("🤖 AI Agent - Interactive Mode")
        print("=" * 50)
        print("Ask me anything! I can help you with various tasks using my tools.")
        print("Type 'quit', 'exit', or 'q' to end the session.")
        print()
        
        while True:
            try:
                question = input("❓ Your question: ").strip()
                if question.lower() in ['quit', 'exit', 'q', '']:
                    print("👋 Goodbye!")
                    break
                
                print("\n🔄 Processing your request...")
                print("-" * 30)
                
                result = agent.run(user_prompt=question)
                print(f"\n✅ Final Result:\n{result}")
                
                if not args.no_save:
                    with open(args.messages_file, "w") as f:
                        json.dump(agent.messages, f, indent=2, default=str)
                    print(f"\n💾 Conversation saved to: {args.messages_file}")
                
                print("\n" + "=" * 50)
                
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    else:
        print(f"🤖 AI Agent - Processing: {question}")
        print("=" * 50)
        
        try:
            result = agent.run(user_prompt=question)
            print(f"\n✅ Final Result:\n{result}")
            
            if not args.no_save:
                with open(args.messages_file, "w") as f:
                    json.dump(agent.messages, f, indent=2, default=str)
                print(f"\n💾 Conversation saved to: {args.messages_file}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
