import json
import re
from pathlib import Path

poe2_dir = Path(r"D:\KS\자료들\_게임\POE2")
GGG_JSON    = poe2_dir / "data_ggg_05.json"
KO_SKILLS   = poe2_dir / "ggpk_workspace/parsed/passiveskills_ko.json"
STATS_JSON  = poe2_dir / "ggpk_workspace/parsed/stats.json"
CSD_MAIN    = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/stat_descriptions.csd"
CSD_PASSIVE = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/passive_skill_stat_descriptions.csd"

def load_json(path: Path) -> object:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def parse_csd_korean(csd_path: Path) -> dict:
    try:
        with open(csd_path, encoding="utf-16", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {}

    templates = {}
    blocks = re.split(r"\n\s*description\s*\n", content)

    for block in blocks[1:]:
        lines = block.split("\n")
        if not lines:
            continue
        m = re.match(r"\s+\d+\s+(.+)", lines[0])
        if not m:
            continue
        stat_names = m.group(1).strip().split()

        ko_match = re.search(r'lang\s+"Korean"\s*\n(.*?)(?=\n\s*lang\s+"|$)', block, re.DOTALL)
        if not ko_match:
            continue

        ko_section = ko_match.group(1)
        tmpl_match = re.search(r'#\s+"([^"]*)"', ko_section)
        if not tmpl_match:
            continue

        template = tmpl_match.group(1).strip()
        for stat_name in stat_names:
            if stat_name and stat_name not in templates:
                templates[stat_name] = template

    return templates

def clean_markup(text: str) -> str:
    text = re.sub(r"\[(?:[^\[\]|]*\|)?([^\[\]]*)\]", r"\1", text)
    return text

def apply_template(template: str, values: list) -> str:
    result = template
    for i, v in enumerate(values):
        v_str = str(v)
        result = result.replace(f"{{{i}:+d}}", f"+{v_str}" if not v_str.startswith("-") else v_str)
        result = result.replace(f"{{{i}}}", v_str)
    
    result = re.sub(
        r"\{(\d+):[^}]*\}",
        lambda m: str(values[int(m.group(1))]) if int(m.group(1)) < len(values) else "",
        result,
    )
    return clean_markup(result)

ggg = load_json(GGG_JSON)
ko_list = load_json(KO_SKILLS)
stats_list = load_json(STATS_JSON)

ko_templates = {}
for csd_path in [CSD_MAIN, CSD_PASSIVE]:
    ko_templates.update(parse_csd_korean(csd_path))

ko_by_graphid = {
    str(item["PassiveSkillGraphId"]): item
    for item in ko_list
    if item.get("PassiveSkillGraphId")
}
stat_by_rid = {
    str(item["_rid"]): item.get("Id", "")
    for item in stats_list
}

mismatches = 0
total_checked = 0
for key, node in ggg["nodes"].items():
    if key == "root":
        continue
    
    ko_node = ko_by_graphid.get(key)
    if not ko_node:
        continue
        
    stat_rids = ko_node.get("Stats", [])
    if not stat_rids:
        continue
        
    eng_stats = node.get("stats", [])
    
    values_all = [
        ko_node.get("Stat1Value", 0),
        ko_node.get("Stat2Value", 0),
        ko_node.get("Stat3Value", 0),
        ko_node.get("Stat4Value", 0),
        ko_node.get("Stat5Value", 0),
    ]
    
    ko_stats = []
    has_fallback = False
    
    for i, rid in enumerate(stat_rids):
        stat_id = stat_by_rid.get(str(rid), "")
        template = ko_templates.get(stat_id, "")
        if not template:
            has_fallback = True
            break
            
        # PASS values_all[i:] instead of values_all!
        ko_stats.append(apply_template(template, values_all[i:]))
        
    if not has_fallback:
        total_checked += 1
        def extract_all_nums(stats):
            return [float(x) if '.' in x else int(x) for x in re.findall(r'-?\d+(?:\.\d+)?', "".join(stats))]
            
        # Compare set of numbers to ignore order differences (e.g. 1 6 0 vs 1 0 6)
        eng_nums = sorted(extract_all_nums(eng_stats))
        ko_nums = sorted(extract_all_nums(ko_stats))
        
        # Filter out 1-second matches or minor mismatches if necessary, but let's do exact set check
        if eng_nums != ko_nums:
            # Check if it's just due to 1-second or something
            # E.g. "Regenerate 0.5% of maximum Life per second" -> numbers: [0.5]
            # Korean: "1초마다 최대 생명력의 0.5% 재생" -> numbers: [1, 0.5]
            # If the only difference is an extra 1 in Korean, it's correct!
            if len(ko_nums) == len(eng_nums) + 1 and 1 in ko_nums:
                temp = list(ko_nums)
                temp.remove(1)
                if temp == eng_nums:
                    continue
            mismatches += 1
            if mismatches <= 10:
                print(f"Mismatch Key: {key} ({node.get('name')})")
                print(f"  ENG stats: {eng_stats}")
                print(f"  KO stats : {ko_stats}")
                print(f"  ENG nums : {eng_nums}")
                print(f"  KO nums  : {ko_nums}")

print(f"Total checked: {total_checked}")
print(f"Total actual value mismatches: {mismatches}")
