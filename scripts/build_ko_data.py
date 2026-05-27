#!/usr/bin/env python3
"""
POE2 한국어 트리 데이터 생성기
GGG 공식 JSON + 한국어 게임 데이터 → app/public/data/data-0.5.json

사용법:
    python scripts/build_ko_data.py
    python scripts/build_ko_data.py --poe2-data "D:/다른경로/_게임/POE2"
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POE2_DATA = Path(r"D:\KS\자료들\_게임\POE2")


def load_json(path: Path) -> object:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_csd_korean(csd_path: Path) -> dict:
    """
    CSD 파일(UTF-16)에서 stat_id -> 한국어 첫 번째 템플릿 딕셔너리 반환.
    예: {"shock_chance_+%": "{0}% 감전 확률 증가", ...}
    """
    try:
        with open(csd_path, encoding="utf-16", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"  경고: CSD 파일 읽기 실패 {csd_path}: {e}")
        return {}

    templates: dict = {}
    blocks = re.split(r"\n\s*description\s*\n", content)

    for block in blocks[1:]:
        lines = block.split("\n")
        if not lines:
            continue
        # 첫 줄: "    N   stat_name_1 [stat_name_2 ...]"
        m = re.match(r"\s+\d+\s+(.+)", lines[0])
        if not m:
            continue
        stat_names = m.group(1).strip().split()

        # Korean 섹션 추출 (다음 lang 또는 블록 끝까지)
        ko_match = re.search(
            r'lang\s+"Korean"\s*\n(.*?)(?=\n\s*lang\s+"|$)',
            block,
            re.DOTALL,
        )
        if not ko_match:
            continue

        ko_section = ko_match.group(1)
        # 첫 번째 # "..." 패턴 (양수 기준 기본 템플릿)
        tmpl_match = re.search(r'#\s+"([^"]*)"', ko_section)
        if not tmpl_match:
            continue

        template = tmpl_match.group(1).strip()
        for stat_name in stat_names:
            if stat_name and stat_name not in templates:
                templates[stat_name] = template

    return templates


def parse_csd_both(csd_path: Path) -> list:
    """
    CSD 파일에서 영어 기본 템플릿과 한국어 템플릿 쌍을 추출합니다.
    """
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
    """
    POE 인라인 마크업 제거:
      [EnergyShield|에너지 보호막] -> 에너지 보호막
      [Attack]                     -> Attack
    """
    text = re.sub(r"\[(?:[^\[\]|]*\|)?([^\[\]]*)\]", r"\1", text)
    return text


def apply_template(template: str, values: list) -> str:
    """CSD 템플릿 {0:+d}, {0:.1f}, {0} 등에 값 대입 후 마크업 정리."""
    result = template
    for i, v in enumerate(values):
        v_str = str(v)
        result = result.replace(f"{{{i}:+d}}", f"+{v_str}" if not v_str.startswith("-") else v_str)
        result = result.replace(f"{{{i}}}", v_str)
    # 나머지 포맷 지정자({i:...}) 처리 — 예: {0:.1f}
    result = re.sub(
        r"\{(\d+):[^}]*\}",
        lambda m: str(values[int(m.group(1))]) if int(m.group(1)) < len(values) else "",
        result,
    )
    return clean_markup(result)


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


def build_ko_stats(node: dict, ko_node: dict, stat_by_rid: dict, ko_templates: dict, compiled_rules: list):
    """
    한국어 스탯 문자열 목록 반환.
    영어 원문에서 수치를 매칭해 우선 대입하며, 매칭이 불가능한 경우 DB 백업 값으로 포맷합니다.
    """
    stat_rids = ko_node.get("Stats", [])
    if not stat_rids:
        return None

    eng_stats = node.get("stats", [])
    values_all = [
        ko_node.get("Stat1Value", 0),
        ko_node.get("Stat2Value", 0),
        ko_node.get("Stat3Value", 0),
        ko_node.get("Stat4Value", 0),
        ko_node.get("Stat5Value", 0),
    ]

    result = []
    for i, rid in enumerate(stat_rids):
        translated = None
        if i < len(eng_stats):
            clean_eng = clean_markup(eng_stats[i])
            translated = translate_stat_via_csd(clean_eng, compiled_rules)
            
        if translated is not None:
            result.append(translated)
        else:
            # 매칭 실패 시 DB 값을 correctly sliced 하여 백업 포맷팅 적용
            stat_id = stat_by_rid.get(str(rid), "")
            template = ko_templates.get(stat_id, "")
            if not template:
                return None  # 영어 fallback
            result.append(apply_template(template, values_all[i:]))

    return result if result else None


def main():
    parser = argparse.ArgumentParser(description="POE2 한국어 트리 데이터 생성기")
    parser.add_argument(
        "--poe2-data",
        default=str(DEFAULT_POE2_DATA),
        help=f"POE2 데이터 디렉토리 (기본값: {DEFAULT_POE2_DATA})",
    )
    args = parser.parse_args()

    poe2_dir = Path(args.poe2_data)
    if not poe2_dir.exists():
        print(f"오류: POE2 데이터 디렉토리를 찾을 수 없습니다: {poe2_dir}")
        sys.exit(1)

    GGG_JSON    = poe2_dir / "data_ggg_05.json"
    KO_SKILLS   = poe2_dir / "ggpk_workspace/parsed/passiveskills_ko.json"
    STATS_JSON  = poe2_dir / "ggpk_workspace/parsed/stats.json"
    CSD_MAIN    = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/stat_descriptions.csd"
    CSD_PASSIVE = poe2_dir / "ggpk_workspace/extracted/data/statdescriptions/passive_skill_stat_descriptions.csd"
    OUT_PATH    = REPO_ROOT / "app/public/data/data-0.5.json"

    for p in [GGG_JSON, KO_SKILLS, STATS_JSON]:
        if not p.exists():
            print(f"오류: 필수 파일 없음: {p}")
            sys.exit(1)

    print("GGG 공식 JSON 로드 중...")
    ggg = load_json(GGG_JSON)

    print("한국어 패시브 스킬 데이터 로드 중...")
    ko_list = load_json(KO_SKILLS)

    print("스탯 ID 테이블 로드 중...")
    stats_list = load_json(STATS_JSON)

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

    # 기존 templates 매핑용 딕셔너리도 준비 (fallback용)
    ko_templates = {}
    for rule in csd_rules:
        for stat_name in rule["stats"]:
            if stat_name and stat_name not in ko_templates:
                ko_templates[stat_name] = rule["ko"]

    ko_by_graphid: dict = {
        str(item["PassiveSkillGraphId"]): item
        for item in ko_list
        if item.get("PassiveSkillGraphId")
    }
    stat_by_rid: dict = {
        str(item["_rid"]): item.get("Id", "")
        for item in stats_list
    }

    nodes = ggg["nodes"]
    cnt_full = cnt_name = cnt_none = 0

    for key, node in nodes.items():
        if key == "root":
            continue
        
        # Save original English name and stats before translation
        if "name" in node:
            node["nameEn"] = node["name"]
        if "stats" in node:
            node["statsEn"] = node["stats"]

        ko_node = ko_by_graphid.get(key)
        if not ko_node:
            cnt_none += 1
            continue

        ko_name = (ko_node.get("Name") or "").strip()
        if ko_name:
            node["name"] = ko_name

        ko_stats = build_ko_stats(node, ko_node, stat_by_rid, ko_templates, compiled_rules)
        if ko_stats:
            node["stats"] = ko_stats
            cnt_full += 1
        else:
            cnt_name += 1

    total = len(nodes) - 1
    print(f"\n번역 결과:")
    print(f"  완전 번역 (이름+스탯): {cnt_full:4d}  ({cnt_full/total*100:.1f}%)")
    print(f"  이름만 번역:           {cnt_name:4d}  ({cnt_name/total*100:.1f}%)")
    print(f"  미번역:                {cnt_none:4d}  ({cnt_none/total*100:.1f}%)")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(ggg, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = OUT_PATH.stat().st_size / 1_048_576
    print(f"\n저장 완료: {OUT_PATH}  ({size_mb:.1f} MB)")
    print("다음 단계: git add app/public/data/data-0.5.json && git commit")


if __name__ == "__main__":
    main()
