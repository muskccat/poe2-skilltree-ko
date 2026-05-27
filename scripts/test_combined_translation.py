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

def parse_csd_both(csd_path: Path) -> list:
    try:
        with open(csd_path, encoding="utf-16", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return []

    results = []
    blocks = re.split(r"\n\s*description\s*\n", content)

    for block in blocks[1:]:
        lines = block.split("\n")
        if not lines:
            continue
        m = re.match(r"\s+\d+\s+(.+)", lines[0])
        if not m:
            continue
        stat_names = m.group(1).strip().split()

        default_section = re.split(r'\n\s*lang\s+"', block)[0]
        ko_match = re.search(r'lang\s+"Korean"\s*\n(.*?)(?=\n\s*lang\s+"|$)', block, re.DOTALL)

        if not ko_match:
            continue

        en_tmpls = re.findall(r'#\s+"([^"]*)"', default_section)
        ko_tmpls = re.findall(r'#\s+"([^"]*)"', ko_match.group(1))

        if en_tmpls and ko_tmpls:
            for en_t, ko_t in zip(en_tmpls, ko_tmpls):
                results.append({
                    "stats": stat_names,
                    "en": en_t.strip(),
                    "ko": ko_t.strip()
                })

    return results

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

print("Loading data files...")
ggg = load_json(GGG_JSON)
ko_list = load_json(KO_SKILLS)
stats_list = load_json(STATS_JSON)

csd_rules = []
for p in [CSD_MAIN, CSD_PASSIVE]:
    csd_rules.extend(parse_csd_both(p))

compiled_rules = []
for rule in csd_rules:
    en_tmpl = rule["en"]
    ko_tmpl = rule["ko"]
    en_clean = clean_markup(en_tmpl)
    ko_clean = clean_markup(ko_tmpl)
    
    parts = re.split(r'\{(\d+)(?::[^}]*)?\}', en_clean)
    regex_parts = []
    val_indices = []
    
    for idx, part in enumerate(parts):
        if idx % 2 == 0:
            regex_parts.append(re.escape(part))
        else:
            regex_parts.append(r'([+-]?\d+(?:\.\d+)?)')
            val_indices.append(int(part))
            
    pattern_str = "^" + "".join(regex_parts) + "$"
    try:
        rx = re.compile(pattern_str, re.IGNORECASE)
        compiled_rules.append({
            "rx": rx,
            "val_indices": val_indices,
            "ko_tmpl": ko_clean
        })
    except Exception as e:
        pass

ko_by_graphid = {
    str(item["PassiveSkillGraphId"]): item
    for item in ko_list
    if item.get("PassiveSkillGraphId")
}
stat_by_rid = {
    str(item["_rid"]): item.get("Id", "")
    for item in stats_list
}

# Add default templates dictionary too
ko_templates = {}
for rule in csd_rules:
    for stat_name in rule["stats"]:
        if stat_name and stat_name not in ko_templates:
            ko_templates[stat_name] = rule["ko"]

def translate_stat_via_csd(s):
    for rule in compiled_rules:
        m = rule["rx"].match(s)
        if m:
            groups = m.groups()
            values = {}
            for val, placeholder_idx in zip(groups, rule["val_indices"]):
                try:
                    num_val = float(val) if '.' in val else int(val)
                except ValueError:
                    num_val = val
                values[placeholder_idx] = num_val
                
            result = rule["ko_tmpl"]
            for placeholder_idx, val in values.items():
                if isinstance(val, (int, float)):
                    val_str = str(val)
                    result = result.replace(f"{{{placeholder_idx}:+d}}", f"+{val_str}" if val >= 0 else val_str)
                    result = result.replace(f"{{{placeholder_idx}}}", val_str)
                else:
                    result = result.replace(f"{{{placeholder_idx}}}", str(val))
                
            result = re.sub(
                r"\{(\d+):[^}]*\}",
                lambda match: str(values.get(int(match.group(1)), "")),
                result,
            )
            return result
    return None

mismatches = 0
total_checked = 0
matched_via_csd = 0
matched_via_db = 0

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
        # 1. Try CSD matching from English string if available
        translated = None
        if i < len(eng_stats):
            clean_eng = clean_markup(eng_stats[i])
            translated = translate_stat_via_csd(clean_eng)
            
        if translated is not None:
            ko_stats.append(translated)
            matched_via_csd += 1
        else:
            # 2. Fall back to old db-value formatting
            stat_id = stat_by_rid.get(str(rid), "")
            template = ko_templates.get(stat_id, "")
            if not template:
                has_fallback = True
                break
            ko_stats.append(apply_template(template, values_all[i:]))
            matched_via_db += 1
            
    if not has_fallback:
        total_checked += 1
        def extract_all_nums(stats):
            return [float(x) if '.' in x else int(x) for x in re.findall(r'-?\d+(?:\.\d+)?', "".join(stats))]
            
        eng_nums = sorted(extract_all_nums(eng_stats))
        ko_nums = sorted(extract_all_nums(ko_stats))
        
        if len(ko_nums) == len(eng_nums) + 1 and 1 in ko_nums:
            temp = list(ko_nums)
            temp.remove(1)
            if temp == eng_nums:
                continue
                
        if eng_nums != ko_nums:
            mismatches += 1
            if mismatches <= 5:
                print(f"Mismatch Key: {key} ({node.get('name')})")
                print(f"  ENG stats: {eng_stats}")
                print(f"  KO stats : {ko_stats}")

print(f"Total checked: {total_checked}")
print(f"Matched via CSD: {matched_via_csd}")
print(f"Matched via DB: {matched_via_db}")
print(f"Remaining mismatches: {mismatches}")
