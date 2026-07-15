"""
Interactive terminal client for the CSUCI Student Success Navigator.
Allows direct conversational testing of the backend without a front end.
"""

import os
import sys
import traceback
import json

# Setup imports
PROJECT_ROOT = "/Users/aalindkale/Downloads/CSUCI Student Success Navigation"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda/orchestrator"))

from handler import lambda_handler

def load_env():
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

def start_chat():
    load_env()
    print("====================================================")
    print("🎓 CSUCI Student Success Navigator — Terminal Client")
    print("====================================================")
    print("Chatting with Bedrock Knowledge Base. Type 'exit' to quit.\n")

    history = []
    session_id = None

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # Build mock API GW event
        event = {
            "httpMethod": "POST",
            "path": "/chat",
            "body": {
                "message": user_input,
                "history": history,
                "sessionId": session_id
            }
        }

        # Call the actual backend orchestrator
        try:
            response = lambda_handler(event, None)
        except Exception as e:
            print("\n❌ Lambda Handler Crashed:")
            traceback.print_exc()
            print("\n" + "-"*52 + "\n")
            continue

        try:
            body = json.loads(response["body"])
        except Exception as e:
            print(f"\n❌ Error parsing response body: {e}")
            print(f"Raw Response: {response}")
            print("\n" + "-"*52 + "\n")
            continue

        session_id = body.get("sessionId")
        answered = body.get("answered", False)
        answer = body.get("answer")
        citations = body.get("citations", [])
        escalation = body.get("escalation")

        print("\nBot:")
        if answered and answer:
            print(answer)
            # Print citations if available
            if citations:
                print("\nSources Cited:")
                for src in citations:
                    print(f"  • {src['title']} ({src['url']})")
            
            # Save to history for multi-turn
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": answer})
        else:
            print("⚠️ (Escalation Triggered)")
            if escalation:
                print(f"  We are transferring you to the {escalation['office']} department.")
                print(f"  Phone: {escalation['contact']['phone']}")
                print(f"  URL:   {escalation['contact']['url']}")
                print(f"  Draft Ticket Summary: {escalation['ticket_draft']['summary']}")
        
        print("\n" + "-"*52 + "\n")

if __name__ == "__main__":
    start_chat()
