import os
import json

log_dir = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\.system_generated\logs"
transcript_path = os.path.join(log_dir, "transcript_full.jsonl")

# Let's inspect Step index 223, 225 or 227
target_steps = [223, 225, 227, 150]

with open(transcript_path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        try:
            data = json.loads(line)
            step_idx = data.get("step_index")
            if step_idx in target_steps:
                print(f"Step {step_idx}:")
                # Look for tool calls
                tool_calls = data.get("tool_calls", [])
                for tc in tool_calls:
                    method = tc.get("method")
                    args = tc.get("args", {})
                    print(f"  Tool: {method}")
                    # If write_to_file or replace_file_content, print details
                    if "CodeContent" in args:
                        print("  CodeContent found! Length:", len(args["CodeContent"]))
                        # Save it to a temp file so we can view it
                        with open(f"scratch/recovered_step_{step_idx}.js", "w", encoding="utf-8") as out:
                            out.write(args["CodeContent"])
                    elif "ReplacementContent" in args:
                        print("  ReplacementContent found! Length:", len(args["ReplacementContent"]))
                        print(args["ReplacementContent"][:300])
        except Exception as e:
            print(f"Error on line {idx}: {e}")
