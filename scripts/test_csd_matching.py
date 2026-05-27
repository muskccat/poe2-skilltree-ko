import json
import re
from pathlib import Path

# Path definitions
poe2_dir = Path(r"D:\KS\자료들\_게임\POE2")
CSD_MAIN    = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/stat_descriptions.csd"
CSD_PASSIVE = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/passive_skill_stat_descriptions.csd"

def parse_csd_both(csd_path: Path) -> list:
    """
    Parses CSD file and returns list of dicts:
    [{"stats": [stat_name1, ...], "en": "Eng template", "ko": "Ko template"}, ...]
    """
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

        # Extract English section
        en_match = re.search(r'lang\s+"English"\s*\n(.*?)(?=\n\s*lang\s+"|$)', block, re.DOTALL)
        # Extract Korean section
        ko_match = re.search(r'lang\s+"Korean"\s*\n(.*?)(?=\n\s*lang\s+"|$)', block, re.DOTALL)

        if not en_match or not ko_match:
            continue

        # Get English and Korean templates (first one matching # "...")
        en_tmpl_match = re.search(r'#\s+"([^"]*)"', en_match.group(1))
        ko_tmpl_match = re.search(r'#\s+"([^"]*)"', ko_match.group(1))

        if en_tmpl_match and ko_tmpl_match:
            results.append({
                "stats": stat_names,
                "en": en_tmpl_match.group(1).strip(),
                "ko": ko_tmpl_match.group(1).strip()
            })

    return results

templates = []
for p in [CSD_MAIN, CSD_PASSIVE]:
    templates.extend(parse_csd_both(p))

print(f"Loaded {len(templates)} templates.")

# Let's inspect a few templates
for t in templates[:5]:
    print(t)
