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
                step_type = data.get("type")
                
                # Print keys and values
                print(f"Index {idx}, Step {step_idx}: Type={step_type}")
                # Print any keys that contain the content of the file
                for k, v in data.items():
                    if isinstance(v, str) and "DolphinLoader" in v:
                        print(f"  Key '{k}' contains 'DolphinLoader'. Length: {len(v)}")
                        # If length is long, let's write it to a file
                        if len(v) > 2000:
                            with open(f"scratch/recovered_raw_{step_idx}_{k}.txt", "w", encoding="utf-8") as out:
                                out.write(v)
                            print(f"    Saved raw value of '{k}' to scratch/recovered_raw_{step_idx}_{k}.txt")
            except Exception as e:
                pass
