import json
import re

with open(r"D:\KS\자료들\_게임\POE2\data_ggg_05.json", encoding="utf-8") as f:
    d_ggg = json.load(f)

with open(r"app/public/data/data-0.5.json", encoding="utf-8") as f:
    d_ko = json.load(f)

def extract_numbers(stats):
    nums = []
    for s in stats:
        # extract all integers or floats (e.g. 4, 15, +5, -0.2)
        found = re.findall(r'-?\d+(?:\.\d+)?', s)
        nums.extend(found)
    return nums

mismatches = []
for key, n_ko in d_ko["nodes"].items():
    if key == "root":
        continue
    n_ggg = d_ggg["nodes"].get(key)
    if not n_ggg:
        continue
    
    ggg_stats = n_ggg.get("stats", [])
    ko_stats = n_ko.get("stats", [])
    
    ggg_nums = extract_numbers(ggg_stats)
    ko_nums = extract_numbers(ko_stats)
    
    if ggg_nums != ko_nums:
        mismatches.append((key, n_ko.get("name"), ggg_stats, ko_stats, ggg_nums, ko_nums))

print(f"Total mismatches: {len(mismatches)}")
for m in mismatches[:20]:
    print(f"Key: {m[0]} ({m[1]})\n  ENG: {m[2]}\n  KO : {m[3]}")
