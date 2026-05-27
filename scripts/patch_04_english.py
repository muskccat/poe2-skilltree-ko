#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_04_PATH = REPO_ROOT / "app/public/data/data-0.4.json"

def main():
    if not DATA_04_PATH.exists():
        print(f"Error: {DATA_04_PATH} does not exist.")
        return

    print("Loading current 0.4 data...")
    with open(DATA_04_PATH, encoding="utf-8") as f:
        current_data = json.load(f)

    print("Fetching English 0.4 data from git history...")
    git_show_cmd = ["git", "show", "ab859ae:app/public/data/data-0.4.json"]
    try:
        git_output = subprocess.check_output(git_show_cmd)
        english_data = json.loads(git_output.decode("utf-8"))
    except Exception as e:
        print(f"Error getting git history: {e}")
        return

    cur_nodes = current_data.get("nodes", {})
    eng_nodes = english_data.get("nodes", {})

    print("Patching English fields to current 0.4 data...")
    patched_count = 0
    for key, cur_node in cur_nodes.items():
        if key == "root":
            continue
        eng_node = eng_nodes.get(key)
        if eng_node:
            if "name" in eng_node:
                cur_node["nameEn"] = eng_node["name"]
            if "stats" in eng_node:
                cur_node["statsEn"] = eng_node["stats"]
            patched_count += 1

    print(f"Patched {patched_count} nodes in 0.4 data.")

    print(f"Saving patched data back to {DATA_04_PATH}...")
    with open(DATA_04_PATH, "w", encoding="utf-8") as f:
        # Save as single line to keep the same format or minified style
        json.dump(current_data, f, ensure_ascii=False, separators=(",", ":"))

    print("Finished patching 0.4 data.")

if __name__ == "__main__":
    main()
