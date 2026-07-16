import os
import json

log_dir = r"C:\Users\myane\.gemini\antigravity\brain\fb4773c8-7646-44ca-a50e-eabf85b2f0df\.system_generated\logs"
transcript_path = os.path.join(log_dir, "transcript_full.jsonl")

with open(transcript_path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if "DolphinLoader.jsx" in line:
            try:
                data = json.loads(line)
                step_idx = data.get("step_index")
                content = data.get("content", "")
                print(f"Index {idx}, Step {step_idx}: Type={data.get('type')}, Source={data.get('source')}")
                # Check for tool_calls or if the code is in content
                if "tool_calls" in data:
                    print("  Tool calls in data:")
                    for tc in data["tool_calls"]:
                        print(f"    Name: {tc.get('name') or tc.get('method')}")
                        args = tc.get("args") or tc.get("arguments")
                        if args:
                            print(f"    Args keys: {list(args.keys())}")
                            if "CodeContent" in args:
                                print(f"      CodeContent length: {len(args['CodeContent'])}")
                                with open(f"scratch/recovered_{step_idx}.jsx", "w", encoding="utf-8") as out:
                                    out.write(args["CodeContent"])
                            if "ReplacementContent" in args:
                                print(f"      ReplacementContent length: {len(args['ReplacementContent'])}")
            except Exception as e:
                print(f"Error on line {idx}: {e}")
