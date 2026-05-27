import json
import re
from pathlib import Path

poe2_dir = Path(r"D:\KS\자료들\_게임\POE2")
GGG_JSON    = poe2_dir / "data_ggg_05.json"
CSD_MAIN    = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/stat_descriptions.csd"
CSD_PASSIVE = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/passive_skill_stat_descriptions.csd"

def parse_csd_both(csd_path: Path) -> list:
    try:
        with open(csd_path, encoding="utf-16", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {csd_path}: {e}")
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

print("Loading CSD templates...")
csd_rules = []
for p in [CSD_MAIN, CSD_PASSIVE]:
    csd_rules.extend(parse_csd_both(p))
print(f"Loaded {len(csd_rules)} translation rules.")

compiled_rules = []
for rule in csd_rules:
    en_tmpl = rule["en"]
    ko_tmpl = rule["ko"]
    
    en_clean = re.sub(r"\[(?:[^\[\]|]*\|)?([^\[\]]*)\]", r"\1", en_tmpl)
    ko_clean = re.sub(r"\[(?:[^\[\]|]*\|)?([^\[\]]*)\]", r"\1", ko_tmpl)
    
    # We want to match numbers, including floats/integers with +/- sign
    # Let's split clean template by braces
    parts = re.split(r'\{(\d+)(?::[^}]*)?\}', en_clean)
    regex_parts = []
    val_indices = []
    
    for idx, part in enumerate(parts):
        if idx % 2 == 0:
            regex_parts.append(re.escape(part))
        else:
            # Match number optionally with + or - prefix
            regex_parts.append(r'([+-]?\d+(?:\.\d+)?)')
            val_indices.append(int(part))
            
    pattern_str = "^" + "".join(regex_parts) + "$"
    try:
        rx = re.compile(pattern_str, re.IGNORECASE)
        compiled_rules.append({
            "rx": rx,
            "val_indices": val_indices,
            "ko_tmpl": ko_clean,
            "en_tmpl": en_clean
        })
    except Exception as e:
        pass

print(f"Successfully compiled {len(compiled_rules)} rules.")

test_stats = [
    "4% increased Movement Speed",
    "15% increased Mana Regeneration Rate",
    "+5 to Dexterity and Intelligence",
    "Regenerate 0.5% of maximum Life per second",
    "Totems die 6 seconds after their Life is reduced to 0",
    "+10 to Spirit",
    "Can Allocate Passive Skills from the Sorceress's starting point"
]

def translate_stat_via_csd(s):
    for rule in compiled_rules:
        m = rule["rx"].match(s)
        if m:
            groups = m.groups()
            values = {}
            for val, placeholder_idx in zip(groups, rule["val_indices"]):
                # Parse as number to strip leading '+' signs
                try:
                    num_val = float(val) if '.' in val else int(val)
                except ValueError:
                    num_val = val
                values[placeholder_idx] = num_val
                
            result = rule["ko_tmpl"]
            
            for placeholder_idx, val in values.items():
                # Formats
                if isinstance(val, (int, float)):
                    val_str = str(val)
                    # For {i:+d}, prepend '+' if >= 0
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

print("\n--- Test Translations ---")
for s in test_stats:
    translated = translate_stat_via_csd(s)
    print(f"ENG: {s}")
    print(f"KO : {translated}")
