#!/usr/bin/env python3
"""
POE2 0.4.0 한국어 트리 데이터 생성기
app/public/data/data-0.4.json 의 nameEn / statsEn -> name / stats 번역
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POE2_DATA = Path(r"D:\KS\자료들\_게임\POE2")

GGG_JSON    = POE2_DATA / "data_ggg_05.json"
KO_SKILLS   = POE2_DATA / "ggpk_workspace/parsed/passiveskills_ko.json"
STATS_JSON  = POE2_DATA / "ggpk_workspace/parsed/stats.json"
CSD_MAIN    = POE2_DATA / "ggpk_workspace/extracted/data/statdescriptions/stat_descriptions.csd"
CSD_PASSIVE = POE2_DATA / "ggpk_workspace/extracted/data/statdescriptions/passive_skill_stat_descriptions.csd"
DATA_04_PATH = REPO_ROOT / "app/public/data/data-0.4.json"

def load_json(path: Path) -> object:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def parse_csd_both(csd_path: Path) -> list:
    try:
        with open(csd_path, encoding="utf-16", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"  경고: CSD 파일 읽기 실패 {csd_path}: {e}")
        return []

    rules = []
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
                rules.append({
                    "stats": stat_names,
                    "en": en_t.strip(),
                    "ko": ko_t.strip()
                })

    return rules

def clean_markup(text: str) -> str:
    text = re.sub(r"\[(?:[^\[\]|]*\|)?([^\[\]]*)\]", r"\1", text)
    text = text.replace("\\n", "\n")
    return text

def translate_stat_via_csd(s, compiled_rules):
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

def main():
    if not DATA_04_PATH.exists():
        print(f"오류: {DATA_04_PATH} 없음")
        return

    print("0.4.0 트리 데이터 로드 중...")
    data_04 = load_json(DATA_04_PATH)

    print("한국어 패시브 스킬 데이터 로드 중...")
    ko_list = load_json(KO_SKILLS)
    ko_by_graphid = {
        str(item["PassiveSkillGraphId"]): item
        for item in ko_list
        if item.get("PassiveSkillGraphId")
    }

    print("CSD 파일에서 영어/한국어 규칙 추출 중...")
    csd_rules = []
    for csd_path in [CSD_MAIN, CSD_PASSIVE]:
        csd_rules.extend(parse_csd_both(csd_path))
    print(f"  총 {len(csd_rules)}개의 CSD 룰 로드됨")

    compiled_rules = []
    for rule in csd_rules:
        en_clean = clean_markup(rule["en"])
        ko_clean = clean_markup(rule["ko"])
        
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
    print(f"  컴파일 성공한 CSD 룰: {len(compiled_rules)}개")

    nodes = data_04["nodes"]
    cnt_translated = 0

    for key, node in nodes.items():
        if key == "root":
            continue
        
        # 1) 이름 번역
        name_en = node.get("nameEn", node.get("name", ""))
        node["nameEn"] = name_en
        
        ko_node = ko_by_graphid.get(key)
        if ko_node:
            ko_name = (ko_node.get("Name") or "").strip()
            if ko_name:
                node["name"] = ko_name
            else:
                node["name"] = name_en
        else:
            node["name"] = name_en

        # 2) 스탯 번역
        stats_en = node.get("statsEn", node.get("stats", []))
        node["statsEn"] = stats_en

        ko_stats = []
        for s in stats_en:
            clean_eng = clean_markup(s)
            translated = translate_stat_via_csd(clean_eng, compiled_rules)
            if translated is not None:
                ko_stats.append(translated)
            else:
                ko_stats.append(clean_eng)
        
        node["stats"] = ko_stats
        cnt_translated += 1

    print(f"번역 완료: {cnt_translated}개 노드")

    with open(DATA_04_PATH, "w", encoding="utf-8") as f:
        json.dump(data_04, f, ensure_ascii=False, separators=(",", ":"))
    print(f"저장 완료: {DATA_04_PATH}")

if __name__ == "__main__":
    main()
