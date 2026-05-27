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
    # Replace placeholders with values
    for i, v in enumerate(values):
        # We need to handle both string and numeric values
        v_str = str(v)
        # E.g. {0:+d} or {0}
        result = result.replace(f"{{{i}:+d}}", f"+{v_str}" if not v_str.startswith("-") else v_str)
        result = result.replace(f"{{{i}}}", v_str)
    
    # Replace other formatting specifiers like {0:.1f}
    result = re.sub(
        r"\{(\d+):[^}]*\}",
        lambda m: str(values[int(m.group(1))]) if int(m.group(1)) < len(values) else "",
        result,
    )
    return clean_markup(result)

def extract_numbers_from_string(s):
    # Match floats and integers, including negative ones
    # but be careful with signs or percent signs
    # Let's match integers or floats
    return [float(x) if '.' in x else int(x) for x in re.findall(r'-?\d+(?:\.\d+)?', s)]

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
    
    # Match values from English stats instead of ko_node StatXValue
    ko_stats = []
    has_fallback = False
    
    for i, rid in enumerate(stat_rids):
        stat_id = stat_by_rid.get(str(rid), "")
        template = ko_templates.get(stat_id, "")
        if not template:
            has_fallback = True
            break
            
        # Extract values from corresponding English stat if exists
        values = []
        if i < len(eng_stats):
            values = extract_numbers_from_string(clean_markup(eng_stats[i]))
            
        # Fallback to database values if no numbers found or index out of range
        if not values:
            db_values = [
                ko_node.get("Stat1Value", 0),
                ko_node.get("Stat2Value", 0),
                ko_node.get("Stat3Value", 0),
                ko_node.get("Stat4Value", 0),
                ko_node.get("Stat5Value", 0),
            ]
            # Just take the i-th value or list of values
            values = [db_values[i]] if i < len(db_values) else [0]
            
        ko_stats.append(apply_template(template, values))
        
    if not has_fallback:
        # Check if numbers match now
        def extract_all_nums(stats):
            return re.findall(r'-?\d+(?:\.\d+)?', "".join(stats))
            
        eng_nums = extract_all_nums(eng_stats)
        ko_nums = extract_all_nums(ko_stats)
        if eng_nums != ko_nums:
            mismatches += 1
            if mismatches <= 10:
                print(f"Mismatch Key: {key}")
                print(f"  ENG stats: {eng_stats}")
                print(f"  KO stats : {ko_stats}")
                print(f"  ENG nums : {eng_nums}")
                print(f"  KO nums  : {ko_nums}")

print(f"Total mismatches with new logic: {mismatches}")
