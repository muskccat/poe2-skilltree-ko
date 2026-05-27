#!/usr/bin/env python3
"""
영문 fallback 노드 이름/스탯을 한국어로 번역하는 패치 스크립트.
build_ko_data.py 실행 후 적용.

사용법:
    python scripts/patch_en_translation.py
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_04_PATH = REPO_ROOT / "app/public/data/data-0.4.json"
DATA_05_PATH = REPO_ROOT / "app/public/data/data-0.5.json"

# ── 노드 이름 번역 사전 ─────────────────────────────────────────────────────
# 게임 내 공식 명칭이 확인된 것은 그대로, 설명형 이름은 맥락 번역
NODE_NAME_KO: dict[str, str] = {
    # ── 일반 패시브 설명형 이름 ──
    "Armour and Energy Shield":                              "방어도와 에너지 보호막",
    "Armour applies to Elemental Damage and Deflection":     "방어도의 원소 피해 방어 및 편향",
    "Armour Applies to Elemental Damage and Energy Shield Delay": "방어도의 원소 피해 방어 및 에너지 보호막 지연",
    "Deflection and Energy Shield Delay":                    "편향 및 에너지 보호막 지연",
    "Evasion and Energy Shield":                             "회피와 에너지 보호막",
    "Life Recoup Speed":                                     "생명력 회복 속도",
    "Left Ventricle":                                        "좌심실",
    "Attack Speed":                                          "공격 속도",
    "Movement Speed":                                        "이동 속도",
    "Area of Effect":                                        "효과 범위",
    "Critical Chance":                                       "치명타 확률",
    "Deflection":                                            "편향",
    "Attributes":                                            "능력치",
    "Spirit":                                                "정신력",
    "Sinister Jewel Socket":                                 "사악한 보석 소켓",
    "Immobilisation Buildup":                                "속박 누적",
    "Additional Power Charge Chance":                        "추가 강인함 충전 확률",
    "Flow of Time":                                          "시간의 흐름",
    "Flow of Life":                                          "생명의 흐름",
    "Damage against Enemies on Low Life":                    "생명력이 낮은 적에게 주는 피해",

    # ── Huntress2 (Spirit Walker) 동반자 계열 ──
    "Companion Mastery":                      "동반자 숙련",
    "Companion Attack Speed":                 "동반자 공격 속도",
    "Companion Life and Area":                "동반자 생명력 및 범위",
    "Shared Companion Damage":                "동반자 피해 공유",
    "Attack Speed and Companion Attack Speed": "공격 속도 및 동반자 공격 속도",
    "Attack Damage and Companion Damage as Cold":  "공격 피해 및 동반자 냉기 피해",
    "Attack Damage and Companion Damage as Chaos": "공격 피해 및 동반자 혼돈 피해",
    "Evasion and Companion Movement Speed":   "회피 및 동반자 이동 속도",
    "Area Damage and Companion Area of Effect": "범위 피해 및 동반자 효과 범위",
    "Bond of the Owl":   "올빼미의 유대",
    "Bond of the Wolf":  "늑대의 유대",
    "Bond of the Cat":   "고양이의 유대",
    "Bond of the Ape":   "유인원의 유대",
    "Bond of the Viper": "독사의 유대",
    "Bond of the Mamba": "맘바의 유대",
    "The Hollowkeeper":  "공허의 수호자",
    "Vivid Stampede":    "생동의 질주",
    "Wild Protector":    "야생의 수호자",
    "Primal Bounty":     "원시의 선물",
    "The Mórrigan's Guidance": "모리건의 인도",
    "The Catha's Balance":     "카타의 균형",
    "The Mhacha's Gift":       "마하의 선물",
    "The Natural Order":       "자연의 질서",
    "Idolatry":    "우상 숭배",
    "Sacred Unity": "신성한 결속",

    # ── Puppet Master (Witch 계열) ──
    "Puppet Master chance":           "꼭두각시 마스터 확률",
    "Minion Damage and Command Speed": "하수인 피해 및 명령 속도",
    "Minion Damage and Command Skill Cooldown": "하수인 피해 및 명령 스킬 재사용 대기시간",
    "Archon Effect":      "집정관 효과",
    "Archon of Undeath":  "불사의 집정관",
    "Embodiment of Death": "죽음의 현신",

    # ── Monk (Invoker) 계열 ──
    "Martial Adept":            "무술 숙련자",
    "Martial Master":           "무술 달인",
    "Hollow Focus Technique":   "공허의 집중 기법",
    "Hollow Resonance Technique": "공허의 공명 기법",
    "Hollow Form Technique":    "공허의 형체 기법",
    "Runic Meridians":          "룬 경락",
    "Way of the Mountain":      "산의 길",
    "Way of the Stonefist":     "돌주먹의 길",

    # ── Warrior 계열 ──
    "Brinerot Ferocity":   "브라인롯의 맹렬함",
    "Redblade Discipline": "레드블레이드의 수련",
    "Path of the Renegade": "배신자의 길",

    # ── 유산/특수 노드 이름 (POE 세계관 인물명 등) ──
    # 이름은 그대로 유지하되, 괄호 안에 설명 추가 불필요 — 원문 유지
    # (이미 게임 내 한국어 번역이 없거나 고유명사)
}

# ── 스탯 문자열 번역 ────────────────────────────────────────────────────────
# (cleanup 이후 영어 스탯 → 한국어)
# 순서 중요: 더 구체적인 패턴을 먼저 배치

# 1) 정확히 매핑되는 문자열 (숫자 포함)
STAT_EXACT_KO: dict[str, str] = {
    # Puppet Master
    "+1 maximum stacks of Puppet Master":
        "꼭두각시 마스터 최대 중첩 +1",
    "15% Surpassing Chance to gain a Puppet Master stack whenever you use a Command Skill":
        "명령 스킬 사용 시 꼭두각시 마스터 중첩을 얻을 우월한 확률 15%",
    "25% increased Duration of each Puppet Master stack":
        "꼭두각시 마스터 각 중첩 지속시간 25% 증가",
    "35% Surpassing Chance to gain a Puppet Master stack whenever you use a Command Skill":
        "명령 스킬 사용 시 꼭두각시 마스터 중첩을 얻을 우월한 확률 35%",
    "15% increased Effect of Puppet Master":
        "꼭두각시 마스터 효과 15% 증가",
    "20% increased Effect of Puppet Master":
        "꼭두각시 마스터 효과 20% 증가",

    # Archon
    "Archon recovery period expires 10% faster":
        "집정관 회복 기간 10% 빠르게 만료",
    "10% increased effect of Archon Buffs on you":
        "내게 적용되는 집정관 버프 효과 10% 증가",
    "15% increased effect of Archon Buffs on you":
        "내게 적용되는 집정관 버프 효과 15% 증가",
    "15% chance of gaining Archon of Undeath when you use a Command skill":
        "명령 스킬 사용 시 불사의 집정관 획득 확률 15%",
    "Immune to Bleeding while affected by an Archon Buff":
        "집정관 버프 적용 중 출혈 면역",

    # Command/Minion
    "Minions deal 6% increased Damage":
        "하수인 피해 6% 증가",
    "Minions have 8% increased Cooldown Recovery Rate for Command Skills":
        "하수인의 명령 스킬 재사용 회복 속도 8% 증가",
    "15% increased Mana Cost Efficiency of Command Skills":
        "명령 스킬 마나 소모 효율 15% 증가",
    "15% increased Glory generation":
        "영광 생성 15% 증가",

    # Block
    "10% increased Block chance":
        "막기 확률 10% 증가",
    "15% increased Block chance":
        "막기 확률 15% 증가",
    "Gain 10 Energy Shield when you Block":
        "막기 시 에너지 보호막 10 회복",
    "Recover 10 Life when you Block":
        "막기 시 생명력 10 회복",
    "25% reduced Armour Break taken":
        "받는 방어도 파괴 25% 감소",

    # Recoup
    "8% increased speed of Recoup Effects":
        "회복 효과 속도 8% 증가",
    "20% increased speed of Recoup Effects":
        "회복 효과 속도 20% 증가",

    # Spirit
    "+10 to Spirit":
        "정신력 +10",

    # Attributes
    "+5 to all Attributes":
        "모든 능력치 +5",

    # Stun
    "20% increased Stun Threshold":
        "기절 임계값 20% 증가",
    "20% increased Immobilisation buildup":
        "속박 누적 20% 증가",
    "15% increased Parried Debuff Magnitude":
        "패링 디버프 강도 15% 증가",

    # Life/Low Life
    "30% increased Damage with Hits against Enemies that are on Low Life":
        "생명력이 낮은 적에게 가하는 타격 피해 30% 증가",

    # Presence
    "30% increased Presence Area of Effect":
        "현존 효과 범위 30% 증가",
    "10% increased Damage while your Companion is in your Presence":
        "동반자가 현존 범위 내에 있을 때 피해 10% 증가",

    # Combo (Monk Invoker)
    "When you gain Combo, gain an additional Combo":
        "연계 획득 시 연계를 하나 더 획득",
    "-0.2 seconds to current Energy Shield Recharge delay per Combo expended when using Skills":
        "스킬 사용 시 소모한 연계당 현재 에너지 보호막 충전 지연 -0.2초",
    "Gain Combo from all Attack Hits":
        "모든 공격 타격에서 연계 획득",
    "Skills can build and retain Combo regardless of Weapon Set":
        "스킬이 무기 세트에 관계없이 연계를 쌓고 유지 가능",

    # Mountain/Stonefist
    "100% Surpassing chance per enemy Power to gain Mountain's Teachings on Immobilising an enemy, up to a maximum of 30":
        "적 속박 시 적의 강인함당 산의 가르침 획득 우월한 확률 100% (최대 30)",
    "Lose a Mountain's Teaching when you are Hit, or when you use or Sustain an Attack that benefits from Mountain's Teachings":
        "피격 시 또는 산의 가르침 혜택을 받는 공격을 사용/지속할 때 산의 가르침 1개 소실",

    # Companion – Spirit Walker
    "Companions deal 10% increased Damage":
        "동반자 피해 10% 증가",
    "Companions deal 10% increased damage per Idol in your Equipment":
        "장착한 아이돌당 동반자 피해 10% 증가",
    "Companions gain 12% Damage as extra Chaos Damage":
        "동반자가 피해의 12%를 추가 혼돈 피해로 획득",
    "Companions gain 12% Damage as extra Cold Damage":
        "동반자가 피해의 12%를 추가 냉기 피해로 획득",
    "Companions gain 4% Damage as extra Chaos Damage":
        "동반자가 피해의 4%를 추가 혼돈 피해로 획득",
    "Companions gain 4% Damage as extra Cold Damage":
        "동반자가 피해의 4%를 추가 냉기 피해로 획득",
    "Companions gain added Attack damage equal to 60% of your main hand Weapon's damage":
        "동반자가 주무기 피해의 60%에 해당하는 추가 공격 피해 획득",
    "Companions have 10% increased Area of Effect":
        "동반자 효과 범위 10% 증가",
    "Companions have 10% increased Attack Speed":
        "동반자 공격 속도 10% 증가",
    "Companions have 15% increased maximum Life":
        "동반자 최대 생명력 15% 증가",
    "Companions have 20% increased Movement Speed":
        "동반자 이동 속도 20% 증가",
    "Companions have 30% increased Area of Effect":
        "동반자 효과 범위 30% 증가",
    "Companions have 50% chance to gain Onslaught on Kill":
        "동반자가 처치 시 광격 획득 확률 50%",
    "Companions have 6% increased Attack Speed":
        "동반자 공격 속도 6% 증가",
    "Companions have 8% increased Movement Speed":
        "동반자 이동 속도 8% 증가",
    "Companions have a 40% chance to Poison on Hit":
        "동반자 타격 시 중독 확률 40%",

    # Cold/Chaos companion gains
    "Gain 6% of Damage as Extra Cold Damage":
        "피해의 6%를 추가 냉기 피해로 획득",
    "Gain 4% of Physical Damage as extra Chaos Damage":
        "물리 피해의 4%를 추가 혼돈 피해로 획득",

    # Evasion
    "15% increased Evasion Rating":
        "회피 수치 15% 증가",
    "12% increased Critical Hit Chance":
        "치명타 확률 12% 증가",

    # Idol
    "-4% to all Elemental Resistances per non-Idol Augment in your Equipment":
        "장착 아이템의 아이돌이 아닌 증폭당 모든 원소 저항 -4%",
    "2% increased Reservation Efficiency of Skills per Idol in your Equipment":
        "장착 아이돌당 스킬 예약 효율 2% 증가",

    # Power Charge
    "10% chance when you gain a Power Charge to gain an additional Power Charge":
        "강인함 충전 획득 시 추가 강인함 충전 획득 확률 10%",

    # Buffs/Debuffs
    "Buffs on you expire 10% slower":
        "내게 적용된 버프 10% 느리게 만료",
    "Debuffs on you expire 10% faster":
        "내게 적용된 디버프 10% 빠르게 만료",
    "50% reduced effect of Curses on you":
        "내게 적용되는 저주 효과 50% 감소",
    "35% reduced Effect of Non-Damaging Ailments on you":
        "내게 적용되는 비피해 상태이상 효과 35% 감소",

    # Banner
    "Banner Skills have 15% increased Aura Magnitudes":
        "깃발 스킬 오라 강도 15% 증가",

    # Druid Spirit Walker – Owl
    "Bear Spirit gains Embrace of the Wild":
        "곰 정령이 야성의 포옹 획득",
    "Central Projectile of Owl Feather-Empowered Skills leaves a trail of Soaring Ground":
        "올빼미 깃털로 강화된 스킬의 중앙 발사체가 비상 지면 흔적 생성",
    "Gain Owl Feathers 50% faster":
        "올빼미 깃털 50% 빠르게 획득",
    "Gain a Primal Owl Feather every 4 seconds, up to a maximum of 3\nExpend an Owl Feather when you Dodge to trigger Primal Bounty":
        "4초마다 원시 올빼미 깃털 획득 (최대 3개)\n회피 시 올빼미 깃털 소모하여 원시의 선물 발동",
    "Dodging can expend up to 3 Owl Feathers, granting Primal Bounty 100% more\nEmpowerment effect per additional Feather expended":
        "회피 시 최대 3개의 올빼미 깃털 소모 가능,\n추가 소모한 깃털당 원시의 선물 강화 효과 100% 증가",

    # Vivid Wisp/Stampede
    "Gain a Vivid Wisp for every 10 metres you move, up to a maximum of 3\nExpend all Vivid Wisps to trigger Vivid Stampede when you Attack\nGain a Vivid Wisp when Vivid Stampede ends":
        "10m 이동할 때마다 생동의 도깨비불 획득 (최대 3개)\n공격 시 모든 생동의 도깨비불을 소모하여 생동의 질주 발동\n생동의 질주 종료 시 생동의 도깨비불 획득",

    # Stag
    "Stags deal 20% more damage per leap":
        "수사슴이 도약당 20% 더 많은 피해",
    "Stags have 20% more Shock Magnitude per leap":
        "수사슴이 도약당 감전 강도 20% 증가",
    "Vivid Stags leap towards enemies":
        "생동의 수사슴이 적을 향해 도약",

    # Beast/Tame
    "Tame Beast can capture Unique Beasts":
        "야수 길들이기로 유니크 야수 포획 가능",
    "Can have up to one Unique Tamed Beast summoned":
        "유니크 길들인 야수를 최대 1마리 소환 가능",
    "Unique Tamed Beasts are Possessed by random Azmeri Spirits, changing every 20 seconds":
        "유니크 길들인 야수에 무작위 아즈메리 정령이 20초마다 빙의",
    "Unique Tamed Beasts have 30% increased movement speed":
        "유니크 길들인 야수 이동 속도 30% 증가",

    # Grants Skill (마크업 제거 후 버전)
    "Grants Skill: Hollow Focus":       "스킬 부여: 공허의 집중",
    "Grants Skill: Hollow Form":        "스킬 부여: 공허의 형체",
    "Grants Skill: Hollow Resonance":   "스킬 부여: 공허의 공명",
    "Grants Skill: Primal Bounty":      "스킬 부여: 원시의 선물",
    "Grants Skill: Vivid Stampede":     "스킬 부여: 생동의 질주",
    "Grants Skill: Wild Protector":     "스킬 부여: 야생의 수호자",
    # Grants Skill (마크업 포함 원문도 처리)
    "Grants Skill: <underline>{Hollow Focus}":     "스킬 부여: 공허의 집중",
    "Grants Skill: <underline>{Hollow Form}":      "스킬 부여: 공허의 형체",
    "Grants Skill: <underline>{Hollow Resonance}": "스킬 부여: 공허의 공명",
    "Grants Skill: <underline>{Primal Bounty}":    "스킬 부여: 원시의 선물",
    "Grants Skill: <underline>{Vivid Stampede}":   "스킬 부여: 생동의 질주",
    "Grants Skill: <underline>{Wild Protector}":   "스킬 부여: 야생의 수호자",

    # Blood Mage (Witch2)
    "Skills gain a Base Life Cost equal to Base Mana Cost":
        "스킬이 기본 마나 소모량과 같은 기본 생명력 소모를 획득",
    "Grants Skill: Life Remnants":      "스킬 부여: 생명의 잔재",
    "Grants Skill: Demon Form":         "스킬 부여: 악마의 형체",

    # Chronomancer (Sorceress2)
    "Grants Skill: Temporal Rift":      "스킬 부여: 시간 균열",
    "Grants Skill: Time Freeze":        "스킬 부여: 시간 동결",
    "Grants Skill: Time Snap":          "스킬 부여: 시간 강타",
    "Grants Skill: Align Fate":         "스킬 부여: 운명 일치",
    "Grants Skill: Apocalypse":         "스킬 부여: 묵시록",

    # Invoker (Monk2)
    "Grants Skill: Meditate":           "스킬 부여: 명상",
    "Grants Skill: Unbound Avatar":     "스킬 부여: 속박 해제된 화신",
    "Grants Skill: Void Illusion":      "스킬 부여: 공허의 환영",
    "Grants Skill: Encase in Jade":     "스킬 부여: 비취에 가두기",
    "Grants Skill: Inevitable Agony":   "스킬 부여: 피할 수 없는 고통",

    # Infernalist (Witch1)
    "Grants Skill: Summon Infernal Hound": "스킬 부여: 지옥 사냥개 소환",

    # Warbringer (Warrior2)
    "Grants Skill: Manifest Weapon":    "스킬 부여: 무기 현현",
    "Grants Skill: Temper Weapon":      "스킬 부여: 무기 단련",

    # Deadeye (Ranger1)
    "Grants Skill: Mirage Deadeye":     "스킬 부여: 신기루 데드아이",
    "Grants Skill: Called Shots":       "스킬 부여: 집중 사격",
    "Grants Skill: Moment of Vulnerability": "스킬 부여: 취약성의 순간",

    # Pathfinder (Ranger3)
    "Grants Skill: Acidic Concoction":      "스킬 부여: 산성 혼합물",
    "Grants Skill: Bleeding Concoction":    "스킬 부여: 출혈 혼합물",
    "Grants Skill: Explosive Concoction":   "스킬 부여: 폭발 혼합물",
    "Grants Skill: Fulminating Concoction": "스킬 부여: 격발 혼합물",
    "Grants Skill: Shattering Concoction":  "스킬 부여: 파쇄 혼합물",

    # Amazon (Huntress1)
    "Grants Skill: Into the Breach":    "스킬 부여: 돌파구로",
    "Grants Skill: Supporting Fire":    "스킬 부여: 지원 사격",
    "Grants Skill: Fire Spell on Hit":  "스킬 부여: 타격 시 화염 주문",

    # Ritualist (Huntress3) named skills
    "Grants Skill: Kelari's Deception":        "스킬 부여: 켈라리의 기만",
    "Grants Skill: Kelari's Judgment":         "스킬 부여: 켈라리의 심판",
    "Grants Skill: Kelari's Malediction":      "스킬 부여: 켈라리의 저주",
    "Grants Skill: Kelari, the Tainted Sands": "스킬 부여: 오염된 모래의 켈라리",
    "Grants Skill: Navira's Fracturing":       "스킬 부여: 나비라의 파쇄",
    "Grants Skill: Navira's Oasis":            "스킬 부여: 나비라의 오아시스",
    "Grants Skill: Navira's Well":             "스킬 부여: 나비라의 우물",
    "Grants Skill: Navira, the Last Mirage":   "스킬 부여: 마지막 신기루 나비라",
    "Grants Skill: Ruzhan's Fury":             "스킬 부여: 루잔의 분노",
    "Grants Skill: Ruzhan's Reckoning":        "스킬 부여: 루잔의 심판",
    "Grants Skill: Ruzhan's Trap":             "스킬 부여: 루잔의 함정",
    "Grants Skill: Ruzhan, the Blazing Sword": "스킬 부여: 불타는 검 루잔",

    # Tactician (Mercenary1)
    "Grenades have 15% chance to activate a second time":
        "수류탄 15% 확률로 2회 발동",

    # Gemling Legionnaire (Mercenary3)
    "100 Passive Skill Points become Weapon Set Skill Points":
        "패시브 스킬 포인트 100개가 무기 세트 스킬 포인트로 전환",

    # Witchhunter (Mercenary2)
    "30% increased damage against Undead Enemies":      "언데드 적에게 주는 피해 30% 증가",
    "50% increased Damage against Demons":              "악마에게 주는 피해 50% 증가",
    "50% increased Critical Hit Chance against Humanoids": "인간형에게 치명타 확률 50% 증가",
    "50% increased Duration of Ailments on Beasts":     "야수에게 부여한 상태이상 지속시간 50% 증가",
    "50% increased Immobilisation buildup against Constructs": "구조물에 대한 속박 누적 50% 증가",
    "50% reduced effect of Shock on you":               "내게 적용되는 감전 효과 50% 감소",

    # Disciple of Varashta (Sorceress3)
    "Adapt to the highest Elemental Damage Type of each Hit you take":
        "받는 타격마다 가장 높은 원소 피해 유형에 적응",
    "10% less Damage taken of each Elemental Damage Type per matching Adaptation":
        "일치하는 적응당 각 원소 피해 유형 피해 10% 감소",
    "10% less Elemental Damage taken":
        "받는 원소 피해 10% 감소",

    # Titan (Warrior1) / Warbringer
    "Body Armour grants 100% increased Thorns damage":
        "몸통 방어구: 가시 피해 100% 증가",
    "Body Armour grants 15% increased maximum Life":
        "몸통 방어구: 최대 생명력 15% 증가",
    "Body Armour grants 20% increased Strength":
        "몸통 방어구: 힘 20% 증가",
    "Body Armour grants 25% of Physical Damage from Hits taken as Fire Damage":
        "몸통 방어구: 받는 타격 물리 피해의 25%를 화염 피해로 전환",
    "Body Armour grants 30% increased Spirit":
        "몸통 방어구: 정신력 30% 증가",
    "Body Armour grants 60% increased Glory generation":
        "몸통 방어구: 영광 생성 60% 증가",
    "Body Armour grants Hits against you have 100% reduced Critical Damage Bonus":
        "몸통 방어구: 내게 가해지는 타격의 치명타 피해 보너스 100% 감소",
    "Body Armour grants Unaffected by Damaging Ailments":
        "몸통 방어구: 피해 주는 상태이상 면역",
    "Body Armour grants regenerate 3% of maximum Life per second":
        "몸통 방어구: 초당 최대 생명력의 3% 재생",

    # Warbringer 특수
    "Consuming Glory grants you 3% increased Attack damage per Glory consumed for 6 seconds, up to 60%":
        "영광 소모 시 소모한 영광당 6초간 공격 피해 3% 증가 (최대 60%)",
    "20% increased Culling Strike Threshold":
        "처형 타격 임계값 20% 증가",
    "20% increased Life Regeneration rate":
        "생명력 재생 속도 20% 증가",

    # Stormweaver
    "Can Allocate Passive Skills from the Sorceress's starting point":
        "소서리스 시작 지점에서 패시브 스킬 배분 가능",
    "Can Allocate Passive Skills from the Warrior's starting point":
        "워리어 시작 지점에서 패시브 스킬 배분 가능",

    # Pathfinder / Poison
    "25% chance for Attacks to Maim on Hit against Poisoned Enemies":
        "중독된 적 공격 타격 시 절름발이 확률 25%",
    "25% increased Magnitude of Poison you inflict":
        "부여하는 중독 강도 25% 증가",

    # Martial Artist (Monk1)
    "Gain a stack of Jade every second":
        "초당 비취 중첩 1 획득",

    # Acolyte of Chayula (Monk3)
    "Break enemy Concentration on Hit equal to 100% of Damage Dealt":
        "타격 시 가한 피해의 100%에 해당하는 적 집중력 파괴",
    "Enemies have Maximum Concentration equal to 30% of their Maximum Life":
        "적의 최대 집중력이 최대 생명력의 30%가 됨",
    "Enemies in your Presence are Slowed by 20%":
        "현존 범위 내 적 이동 속도 20% 둔화",
    "Enemies regain 10% of Concentration every second if they haven't lost Concentration in the past 5 seconds":
        "5초간 집중력을 잃지 않은 적이 초당 집중력 10% 회복",

    # Totem
    "+1 to maximum number of Summoned Totems":
        "소환된 토템 최대 수 +1",
    "Skills used by Totems have 30% more Skill Speed":
        "토템이 사용하는 스킬 스킬 속도 30% 증가",
    "Totems only use Skills when you fire an Attack Projectile":
        "공격 투사체 발사 시에만 토템이 스킬 사용",

    # Projectile
    "Projectile Attacks have a 12% chance to fire two additional Projectiles while moving":
        "이동 중 발사 투사체 공격이 12% 확률로 추가 투사체 2개 발사",
    "Projectiles Pierce enemies with Fully Broken Armour":
        "투사체가 방어도가 완전히 파괴된 적을 관통",

    # Passive Points
    "Grants 1 Passive Skill Point":     "패시브 스킬 포인트 1 부여",
    "Grants 4 Passive Skill Points":    "패시브 스킬 포인트 4 부여",

    # Misc
    "You cannot be Electrocuted":       "감전사 면역",
    "30% reduced effect of Curses on you": "내게 적용되는 저주 효과 30% 감소",
    "Culling Strike against Beasts while your Companion is in your Presence":
        "동반자가 현존 범위 내에 있을 때 야수에게 처형 타격",
    "Tame Beast can capture Unique Beasts\nCan have up to one Unique Tamed Beast summoned":
        "야수 길들이기로 유니크 야수 포획 가능\n유니크 길들인 야수를 최대 1마리 소환 가능",

    # Vivid Wisp 여러 줄 버전
    "Gain a Vivid Wisp for every 10 metres you move, up to a maximum of 3\nExpend all Vivid Wisps to trigger Vivid Stampede when you Attack":
        "10m 이동할 때마다 생동의 도깨비불 획득 (최대 3개)\n공격 시 모든 생동의 도깨비불을 소모하여 생동의 질주 발동",
    "Gain a Vivid Wisp when Vivid Stampede ends":
        "생동의 질주 종료 시 생동의 도깨비불 획득",

    # Gloves transform
    "Gloves you equip have their Base Type transformed to Fists of Stone while equipped, and\ntheir Explicit Modifiers are transformed into more powerful related Modifiers":
        "장착한 장갑의 기본 유형이 장착 중 '돌 주먹'으로 변환되며,\n명시적 수정자가 더 강력한 관련 수정자로 변환됩니다",
    "Ignore Attribute Requirements to equip Gloves":
        "장갑 장착 능력치 요구사항 무시",

    # Rune sockets
    "Can tattoo Runes onto your body, gaining\nadditional Rune-only sockets:\n• 1 Helmet socket\n• 2 Body Armour sockets\n• 1 Gloves socket\n• 1 Boots socket":
        "몸에 룬을 문신할 수 있으며, 다음 룬 전용 소켓 추가:\n• 투구 소켓 1개\n• 몸통 방어구 소켓 2개\n• 장갑 소켓 1개\n• 신발 소켓 1개",
}

# 2) 숫자 포함 정규식 패턴 (더 구체적인 것 먼저)
STAT_REGEX_KO: list[tuple[str, str]] = [
    # Armour applies to X damage
    (r'\+(\d+)% of Armour also applies to Elemental Damage',
     r'방어도의 +\1%가 원소 피해 방어에도 적용됩니다'),
    (r'\+(\d+)% of Armour also applies to Chaos Damage',
     r'방어도의 +\1%가 혼돈 피해 방어에도 적용됩니다'),
    (r'\+(\d+)% of Armour also applies to Fire Damage',
     r'방어도의 +\1%가 화염 피해 방어에도 적용됩니다'),
    (r'\+(\d+)% of Armour also applies to Lightning Damage',
     r'방어도의 +\1%가 번개 피해 방어에도 적용됩니다'),
    (r'\+(\d+)% of Armour also applies to Cold Damage',
     r'방어도의 +\1%가 냉기 피해 방어에도 적용됩니다'),
    (r'\+(\d+)% of Armour also applies to Physical Damage',
     r'방어도의 +\1%가 물리 피해 방어에도 적용됩니다'),

    # Energy Shield recharge
    (r'(\d+)% faster start of Energy Shield Recharge',
     r'에너지 보호막 충전 시작 \1% 빠름'),

    # Deflection
    (r'Gain Deflection Rating equal to (\d+)% of Evasion Rating',
     r'회피 수치의 \1%에 해당하는 편향 수치 획득'),

    # Armour
    (r'(\d+)% increased Armour',
     r'방어도 \1% 증가'),

    # Energy Shield
    (r'(\d+)% increased maximum Energy Shield',
     r'최대 에너지 보호막 \1% 증가'),

    # Evasion
    (r'(\d+)% increased Evasion Rating',
     r'회피 수치 \1% 증가'),

    # Resistances
    (r'\+(\d+)% to Fire Resistance',
     r'화염 저항 +\1%'),
    (r'\+(\d+)% to Chaos Resistance',
     r'혼돈 저항 +\1%'),
    (r'\+(\d+)% to Lightning Resistance',
     r'번개 저항 +\1%'),
    (r'\+(\d+)% to Cold Resistance',
     r'냉기 저항 +\1%'),

    # Attack
    (r'(\d+)% increased Attack Speed',
     r'공격 속도 \1% 증가'),
    (r'(\d+)% increased Attack Damage',
     r'공격 피해 \1% 증가'),
    (r'(\d+)% increased Area Damage',
     r'범위 피해 \1% 증가'),
    (r'(\d+)% increased Area of Effect',
     r'효과 범위 \1% 증가'),
    (r'(\d+)% increased Movement Speed',
     r'이동 속도 \1% 증가'),
    (r'(\d+)% reduced Movement Speed Penalty from using Skills while moving',
     r'이동 중 스킬 사용 이동 속도 패널티 \1% 감소'),

    # Life
    (r'(\d+)% increased Accuracy Rating',
     r'정확도 수치 \1% 증가'),
    (r'(\d+)% increased Light Radius',
     r'빛 반경 \1% 증가'),
    (r'(\d+)% increased Skill Effect Duration',
     r'스킬 효과 지속시간 \1% 증가'),

    # Block
    (r'(\d+)% increased Block chance',
     r'막기 확률 \1% 증가'),
]


def clean_markup(text: str) -> str:
    """[A|B] → B, [A] → A, <underline>{X} → X"""
    text = re.sub(r'\[(?:[^\[\]|]*\|)?([^\[\]]*)\]', r'\1', text)
    text = re.sub(r'<[^>]+>\{([^}]+)\}', r'\1', text)
    text = text.replace("\\n", "\n")
    return text


def translate_stat(stat: str) -> str:
    """영어 스탯 문자열 → 한국어 (순서: 정확일치 → 정규식)"""
    # 1) 정확 일치
    if stat in STAT_EXACT_KO:
        return STAT_EXACT_KO[stat]
    # 2) 정규식 패턴
    for pattern, repl in STAT_REGEX_KO:
        new_stat = re.sub(pattern, repl, stat)
        if new_stat != stat:
            return new_stat
    return stat  # 번역 없으면 원문 유지


def translate_name(name: str) -> str:
    """영어 노드 이름 → 한국어"""
    # 마크업 정리 후 사전 조회
    cleaned = clean_markup(name)
    return NODE_NAME_KO.get(cleaned, NODE_NAME_KO.get(name, name))


def patch_file(file_path: Path):
    if not file_path.exists():
        print(f"오류: {file_path} 없음")
        return

    print(f"로드 중: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    nodes = data["nodes"]
    name_changed = stat_changed = 0

    for key, node in nodes.items():
        if key == "root":
            continue

        name = node.get("name", "")
        # 영어인 경우만 처리 (한국어 이미 있으면 스킵)
        has_ko = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in name)

        if not has_ko and name.strip() and name != "WIP":
            new_name = translate_name(name)
            if new_name != name:
                node["name"] = new_name
                name_changed += 1

        # 스탯 번역 (한국어가 없는 스탯만)
        old_stats = node.get("stats", [])
        new_stats = []
        changed = False
        for s in old_stats:
            has_ko_stat = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in s)
            if not has_ko_stat:
                cleaned = clean_markup(s)
                translated = translate_stat(cleaned)
                if translated != cleaned:
                    new_stats.append(translated)
                    changed = True
                else:
                    new_stats.append(s)  # 번역 없으면 마크업 포함 원문 유지
            else:
                new_stats.append(s)
        if changed:
            node["stats"] = new_stats
            stat_changed += 1

    # ── 특정 노드 맞춤 수동 보정 ──────────────────────────────────────────
    # 1) 공허의 손아귀 기술 -> 공허의 손바닥 기술 교체
    for key, node in nodes.items():
        if key == "root":
            continue
        if "name" in node and node["name"] == "공허의 손아귀 기술":
            node["name"] = "공허의 손바닥 기술"
            name_changed += 1
        if "stats" in node:
            new_node_stats = []
            stat_node_changed = False
            for s in node["stats"]:
                if "공허의 손아귀 기술" in s:
                    new_node_stats.append(s.replace("공허의 손아귀 기술", "공허의 손바닥 기술"))
                    stat_node_changed = True
                else:
                    new_node_stats.append(s)
            if stat_node_changed:
                node["stats"] = new_node_stats
                stat_changed += 1

    # 2) 64601 (공허의 손바닥 기술) 노드의 0.5.0 버전에 버그픽스 문구 추가 (기존 설명 제거)
    if file_path.name == "data-0.5.json" and "64601" in nodes:
        hollow_node = nodes["64601"]
        bugfix_text = '버그픽스: "공허의 손바닥 기술"이 대부분의 무도 무기 사용 가능 스킬에 보너스를 제공하지 않던 문제를 수정했습니다. 이제 "공허의 손바닥 기술"은 영향을 받는 공격에 대해 기본 비무장 피해에 피해를 추가하는 대신, 비무장 기본 피해를 대체합니다.'
        hollow_node["stats"] = [bugfix_text]
        stat_changed += 1

    print(f"  노드 이름 번역: {name_changed}개")
    print(f"  스탯 번역: {stat_changed}개")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = file_path.stat().st_size / 1_048_576
    print(f"  저장 완료: {file_path} ({size_mb:.1f} MB)\n")


def main():
    patch_file(DATA_04_PATH)
    patch_file(DATA_05_PATH)


if __name__ == "__main__":
    main()
