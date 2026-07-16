import os
import json

log_dir = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\.system_generated\logs"
transcript_path = os.path.join(log_dir, "transcript_full.jsonl")

if not os.path.exists(transcript_path):
    # Try transcript.jsonl
    transcript_path = os.path.join(log_dir, "transcript.jsonl")

print(f"Reading from: {transcript_path}")

try:
    with open(transcript_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    print(f"Total lines: {len(lines)}")
    # Find all references to DolphinLoader.jsx content
    # We look for steps that wrote or replaced content of DolphinLoader.jsx
    for idx, line in enumerate(lines):
        if "DolphinLoader.jsx" in line:
            print(f"Line {idx} mentions DolphinLoader.jsx")
            # Let's inspect the JSON data to find target content or code content
            try:
                data = json.loads(line)
                step_type = data.get("type")
                source = data.get("source")
                print(f"  Step index: {data.get('step_index')}, Type: {step_type}, Source: {source}")
            except Exception as e:
                pass
except Exception as e:
    print(f"Error: {e}")
