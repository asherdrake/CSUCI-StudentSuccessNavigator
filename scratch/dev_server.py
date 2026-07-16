"""
Lightweight local development server for the Student Success Navigator.
Serves a local HTTP server on port 8000 mapping requests to the Lambda handler.

Allows the React team to test against the live backend locally.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

# Setup python path imports (derived from this file's location — never hardcode,
# this repo runs on multiple machines/OSes)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lambda/orchestrator"))

from handler import lambda_handler

def load_env():
    """Load local environment configurations."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()
        print("Loaded environment variables from .env")

class LambdaDevHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST,OPTIONS")

    def do_OPTIONS(self):
        """Handle CORS preflight requests from React app."""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        """Forward requests to the orchestrator lambda handler."""
        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")

        # Construct the API Gateway event proxy payload
        event = {
            "httpMethod": "POST",
            "path": "/chat",
            "headers": {"Content-Type": "application/json"},
            "body": post_data,
            "isBase64Encoded": False,
            "requestContext": {"http": {"method": "POST"}},
        }

        print(f"\n---> Received request: {post_data}")

        # Call the actual Lambda orchestrator handler
        response = lambda_handler(event, None)

        # Parse output
        status_code = response.get("statusCode", 500)
        response_body = response.get("body", "{}")

        # Send response back to browser/React
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        
        self.wfile.write(response_body.encode("utf-8"))
        print(f"<--- Responded with status {status_code}: {response_body}")

def run_server(port=8000):
    load_env()
    server_address = ("", port)
    httpd = HTTPServer(server_address, LambdaDevHandler)
    # No emoji here: Windows consoles default to cp1252 and crash on it.
    print(f"\nCSUCI Student Navigator local backend server running on http://localhost:{port}/chat")
    print("Press Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
