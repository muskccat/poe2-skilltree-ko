import re
from pathlib import Path

poe2_dir = Path(r"D:\KS\자료들\_게임\POE2")
CSD_MAIN    = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/stat_descriptions.csd"

with open(CSD_MAIN, encoding="utf-16", errors="replace") as f:
    content = f.read()

blocks = re.split(r"\n\s*description\s*\n", content)

with open(r"C:\Users\Vimus\.gemini\antigravity\brain\64f679ee-eeaf-46f3-a529-0dfae177c7d0\scratch\csd_output.txt", "w", encoding="utf-8") as out:
    out.write(f"Total blocks in main CSD: {len(blocks)}\n")
    block = blocks[100]
    out.write("--- BLOCK 100 RAW ---\n")
    out.write(block + "\n")
    
    parts = re.split(r'\n\s*lang\s+"', block)
    default_section = parts[0]
    out.write("--- DEFAULT SECTION ---\n")
    out.write(default_section + "\n")
    
    en_tmpl_match = re.search(r'#\s+"([^"]*)"', default_section)
    if en_tmpl_match:
        out.write(f"EN: {en_tmpl_match.group(1)}\n")
        
    ko_match = re.search(r'lang\s+"Korean"\s*\n(.*?)(?=\n\s*lang\s+"|$)', block, re.DOTALL)
    if ko_match:
        ko_tmpl_match = re.search(r'#\s+"([^"]*)"', ko_match.group(1))
        if ko_tmpl_match:
            out.write(f"KO: {ko_tmpl_match.group(1)}\n")
