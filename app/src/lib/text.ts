import type { NodeKind } from "../types";

// PoE stat strings embed markup like "[EnergyShield|Energy Shield]" or
// "[Recently]". Collapse to the human-readable part.
export function cleanStat(s: string): string {
  return s.replace(/\[(?:[^\[\]|]*\|)?([^\[\]]*)\]/g, "$1");
}

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
