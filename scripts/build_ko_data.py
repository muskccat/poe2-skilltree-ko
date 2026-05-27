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
        result = result.replace(f"{{{i}:+d}}", f"+{v}" if v >= 0 else str(v))
        result = result.replace(f"{{{i}}}", str(v))
    # 나머지 포맷 지정자({i:...}) 처리 — 예: {0:.1f}
    result = re.sub(
        r"\{(\d+):[^}]*\}",
        lambda m: str(values[int(m.group(1))]) if int(m.group(1)) < len(values) else "",
        result,
    )
    return clean_markup(result)


def build_ko_stats(ko_node: dict, stat_by_rid: dict, ko_templates: dict):
    """
    한국어 스탯 문자열 목록 반환.
    하나라도 템플릿이 없으면 None 반환 (영어 fallback 신호).
    """
    stat_rids = ko_node.get("Stats", [])
    if not stat_rids:
        return None

    values = [
        ko_node.get("Stat1Value", 0),
        ko_node.get("Stat2Value", 0),
        ko_node.get("Stat3Value", 0),
        ko_node.get("Stat4Value", 0),
        ko_node.get("Stat5Value", 0),
    ]

    result = []
    for i, rid in enumerate(stat_rids):
        stat_id = stat_by_rid.get(str(rid), "")
        template = ko_templates.get(stat_id, "")
        if not template:
            return None  # 이 노드는 영어 fallback
        result.append(apply_template(template, values))

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

    print("CSD 파일 파싱 중...")
    ko_templates: dict = {}
    for csd_path in [CSD_MAIN, CSD_PASSIVE]:
        ko_templates.update(parse_csd_korean(csd_path))
    print(f"  한국어 스탯 템플릿 {len(ko_templates)}개 로드됨")

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

        ko_stats = build_ko_stats(ko_node, stat_by_rid, ko_templates)
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
