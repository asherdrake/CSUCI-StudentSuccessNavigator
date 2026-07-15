"""
Verification script to test Bedrock connection using live credentials.
"""

import os
import sys

# Add project root and lambda directories to the python path
sys.path.insert(0, "/Users/aalindkale/Downloads/CSUCI Student Success Navigation")
sys.path.insert(0, "/Users/aalindkale/Downloads/CSUCI Student Success Navigation/lambda")
sys.path.insert(0, "/Users/aalindkale/Downloads/CSUCI Student Success Navigation/lambda/orchestrator")

def load_env():
    """Manually parse .env file to avoid external dependency python-dotenv"""
    env_path = "/Users/aalindkale/Downloads/CSUCI Student Success Navigation/.env"
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        return False
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()
    return True

def test_connection():
    if not load_env():
        return

    print("=== BEDROCK CONNECTION TEST ===")
    kb_id = os.environ.get("BEDROCK_KB_ID")
    region = os.environ.get("AWS_REGION", "us-west-2")
    
    print(f"Loaded Knowledge Base ID: {kb_id}")
    print(f"Target AWS Region:        {region}")
    print("---------------------------------------")

    try:
        from retriever import retrieve_context
    except ImportError as e:
        print(f"Failed to import retriever: {e}")
        return

    print("Querying Bedrock Knowledge Base for 'registration'...")
    results = retrieve_context("registration", top_k=2)

    if not results:
        print("\n❌ Verification Failed: No results returned.")
        print("This usually happens because:")
        print("1. Your AWS session token / credentials in the terminal are expired.")
        print("2. The Knowledge Base ID is incorrect or deployed in a different region.")
        print("3. Your IAM user/role doesn't have 'bedrock:Retrieve' permissions.")
        print("\nTo refresh credentials, run in your terminal: 'aws configure' or check your AWS SSO login.")
    else:
        print("\n✅ Verification Success! Connected to Bedrock.")
        print(f"Retrieved {len(results)} chunks from the Knowledge Base:\n")
        for i, chunk in enumerate(results, start=1):
            print(f"[{i}] Score: {chunk['score']:.4f}")
            print(f"    Source Title: {chunk['source_title']}")
            print(f"    Source URL:   {chunk['source_url']}")
            print(f"    Snippet:      {chunk['text'][:120]}...\n")

if __name__ == "__main__":
    test_connection()
