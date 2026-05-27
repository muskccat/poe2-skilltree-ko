import type { NodeKind } from "../types";

// PoE stat strings embed markup like "[EnergyShield|Energy Shield]" or
// "[Recently]" or "<underline>{Skill Name}". Collapse to human-readable text.
export function cleanStat(s: string): string {
  return s
    .replace(/\[(?:[^\[\]|]*\|)?([^\[\]]*)\]/g, "$1")   // [A|B]→B, [A]→A
    .replace(/<[^>]+>\{([^}]+)\}/g, "$1");                // <underline>{X}→X
}

// 클래스 이름 한국어
export const CLASS_NAME_KO: Record<string, string> = {
  Witch:      "위치",
  Ranger:     "레인저",
  Warrior:    "워리어",
  Sorceress:  "소서리스",
  Huntress:   "헌트리스",
  Mercenary:  "머서너리",
  Monk:       "몽크",
  Druid:      "드루이드",
  Marauder:   "머라우더",
  Duelist:    "듀얼리스트",
  Shadow:     "섀도우",
  Templar:    "템플러",
};

// 어센던시 ID → 한국어 표시 이름
export const ASC_ID_KO: Record<string, string> = {
  // Witch
  Witch1:       "지옥술사",
  Witch2:       "블러드 메이지",
  Witch3:       "리치",
  Witch3b:      "심연의 리치",
  // Ranger
  Ranger1:      "데드아이",
  Ranger3:      "패스파인더",
  // Warrior
  Warrior1:     "타이탄",
  Warrior2:     "워브링어",
  Warrior3:     "스미스 오브 키타바",
  // Sorceress
  Sorceress1:   "스톰위버",
  Sorceress2:   "크로노맨서",
  Sorceress3:   "디사이플 오브 바라시타",
  // Huntress (0.5 신규)
  Huntress1:    "아마존",
  Huntress2:    "스피릿 워커",
  Huntress3:    "리추얼리스트",
  // Mercenary
  Mercenary1:   "택티션",
  Mercenary2:   "위치헌터",
  Mercenary3:   "젬링 리저네어",
  // Monk
  Monk1:        "마샬 아티스트",
  Monk2:        "인보커",
  Monk3:        "애컬라이트 오브 차율라",
  // Druid
  Druid1:       "오라클",
  Druid2:       "샤먼",
  // 미출시 자리 (ID만 존재)
  Ranger2:      "레인저2",
  Druid3:       "드루이드3",
  Marauder1:    "마로더1", Marauder2: "마로더2", Marauder3: "마로더3",
  Duelist1:     "듀얼리스트1", Duelist2: "듀얼리스트2", Duelist3: "듀얼리스트3",
  Shadow1:      "그림자1", Shadow2: "그림자2", Shadow3: "그림자3",
  Templar1:     "템플러1", Templar2: "템플러2", Templar3: "템플러3",
};

export const KIND_LABEL: Record<NodeKind, string> = {
  keystone: "키스톤",
  notable: "노터블",
  mastery: "마스터리",
  jewel: "보석 소켓",
  ascNotable: "어센던시 노터블",
  ascNormal: "어센던시 패시브",
  ascStart: "어센던시 시작",
  small: "패시브",
};
