#!/usr/bin/env python3
"""
CSUCI Student Success Navigator - Local Development Server.
Combines frontend file serving and backend Lambda emulation into a single server.
"""

import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Set paths so we can import lambda packages
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, "lambda"))
sys.path.insert(0, os.path.join(ROOT_DIR, "lambda", "orchestrator"))

def load_env():
    """Load environment variables from the .env file in the root directory."""
    env_path = os.path.join(ROOT_DIR, ".env")
    if not os.path.exists(env_path):
        print(f"[*] Warning: .env file not found at {env_path}")
        print("[*] Please copy .env.example to .env and configure your BEDROCK_KB_ID and AWS credentials.")
        return False
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()
    print("[*] Loaded environment variables from .env")
    return True

class CombinedServerHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        """Map GET requests to the frontend/ directory (preferring dist if built)."""
        translated = super().translate_path(path)
        relative_path = os.path.relpath(translated, os.getcwd())
        
        # Determine the base folder to serve from: prefer 'frontend/dist' if a build exists,
        # otherwise fallback to 'frontend/'
        dist_path = os.path.join(ROOT_DIR, "frontend", "dist")
        if os.path.exists(os.path.join(dist_path, "index.html")):
            base_dir = dist_path
        else:
            base_dir = os.path.join(ROOT_DIR, "frontend")
            
        if relative_path == "." or relative_path == "":
            return os.path.join(base_dir, "index.html")
            
        return os.path.join(base_dir, relative_path)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        """Handle POST requests, specifically routing /chat to the Lambda handler."""
        if self.path == "/chat":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            print(f"\n[POST /chat] Received request: {post_data}")
            
            # Map request to Lambda API Gateway event structure
            event = {
                "httpMethod": "POST",
                "headers": {key: val for key, val in self.headers.items()},
                "body": post_data
            }
            
            try:
                # Import handler dynamically to ensure environment is fully loaded
                from handler import lambda_handler
                
                # Run the actual orchestrator logic
                lambda_response = lambda_handler(event, None)
                
                # Return result to client
                status_code = lambda_response.get("statusCode", 200)
                response_body = lambda_response.get("body", "{}")
                headers = lambda_response.get("headers", {})
                
                self.send_response(status_code)
                for key, val in headers.items():
                    self.send_header(key, val)
                self.end_headers()
                self.wfile.write(response_body.encode("utf-8"))
                
                print(f"[POST /chat] Success! Response sent: {response_body[:200]}...")
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                err_response = {"error": f"Local Server Error: {str(e)}"}
                self.wfile.write(json.dumps(err_response).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

def run(port=5000):
    load_env()
    server_address = ("", port)
    httpd = HTTPServer(server_address, CombinedServerHandler)
    print(f"\n========================================================")
    print(f"CSUCI Navigator local combined server running!")
    print(f"UI URL: http://localhost:{port}")
    print(f"Live API Endpoint (for settings): http://localhost:{port}/chat")
    print(f"========================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local server...")
        httpd.server_close()

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run(port)
