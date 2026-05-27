import type { ParsedTree, VersionDiff, DiffEntry, MovedEntry } from "../types";
import { cleanStat } from "./text";

const isReal = (name: string) => !!name && !name.startsWith("[DNT");
// Compare the *displayed* stat text, so markup-only retags (e.g.
// "[ItemDefences|Item Energy Shield]" → "[ItemEnergyShield|Item Energy Shield]",
// or "Equipment" → "[Equipment]") don't get flagged as reworks.
const sameStats = (a: string[], b: string[]) =>
  a.length === b.length && a.every((s, i) => cleanStat(s) === cleanStat(b[i]));
// Minimum world-space shift to count a node as "moved" (skips micro-adjustments).
const MOVE_MIN = 100;

/**
 * Diff two parsed trees keyed by numeric skill id (the stable dict key).
 * Produces per-node status used to highlight what changed in `next` vs `prev`.
 */
export function computeDiff(prev: ParsedTree, next: ParsedTree): VersionDiff {
  const byKey = new Map<string, DiffEntry>();
  const removed: DiffEntry[] = [];
  const moved: MovedEntry[] = [];
  const counts = { added: 0, removed: 0, stats: 0, renamed: 0, moved: 0 };

  // added + modified (iterate the newer tree)
  for (const [key, n] of next.nodes) {
    const o = prev.nodes.get(key);
    if (!o) {
      if (isReal(n.name) || n.stats.length) {
        byKey.set(key, { status: "added", newName: n.name, newStats: n.stats });
        counts.added++;
      }
      continue;
    }
    // relocation is independent of content changes (a node can move *and* be
    // reworked), so it's tracked separately rather than via byKey.
    const dx = n.x - o.x;
    const dy = n.y - o.y;
    if (dx * dx + dy * dy > MOVE_MIN * MOVE_MIN) {
      moved.push({ key, name: n.name || o.name, fromX: o.x, fromY: o.y, toX: n.x, toY: n.y });
    }
    const statsChanged = !sameStats(o.stats, n.stats);
    const nameChanged = o.name !== n.name && isReal(o.name) && isReal(n.name);

    if (statsChanged && (isReal(o.name) || isReal(n.name)) && (o.stats.length || n.stats.length)) {
      byKey.set(key, {
        status: "stats",
        oldName: o.name,
        newName: n.name,
        oldStats: o.stats,
        newStats: n.stats,
      });
      counts.stats++;
    } else if (nameChanged) {
      byKey.set(key, { status: "renamed", oldName: o.name, newName: n.name });
      counts.renamed++;
    }
  }

  // removed (in prev, gone from next) — keep meaningful ones for ghosting
  for (const [key, o] of prev.nodes) {
    if (next.nodes.has(key)) continue;
    if (!isReal(o.name)) continue;
    const entry: DiffEntry = {
      status: "removed",
      oldName: o.name,
      oldStats: o.stats,
      ghost: { x: o.x, y: o.y, name: o.name, kind: o.kind },
    };
    byKey.set(key, entry);
    removed.push(entry);
    counts.removed++;
  }

  // Per-class overrides: a shared node's displayed name/stats for a class come
  // from skillOverrides, which the base comparison above can't see. Flag a node
  // when its override changed between versions but the base node did not (e.g.
  // the Witch "Spell and Minion Damage" start nodes went 8% → 10%).
  const classIdx = new Set<number>([...prev.classOverrides.keys(), ...next.classOverrides.keys()]);
  for (const ci of classIdx) {
    const pm = prev.classOverrides.get(ci);
    const nm = next.classOverrides.get(ci);
    const keys = new Set<string>([...(pm ? pm.keys() : []), ...(nm ? nm.keys() : [])]);
    for (const key of keys) {
      if (byKey.has(key)) continue; // base change (or another class) already flagged it
      const po = pm?.get(key);
      const no = nm?.get(key);
      const oName = po?.name ?? "";
      const nName = no?.name ?? "";
      const oStats = po?.stats ?? [];
      const nStats = no?.stats ?? [];
      const statsChanged = !sameStats(oStats, nStats);
      if (!statsChanged && oName === nName) continue;
      if (statsChanged) {
        byKey.set(key, { status: "stats", oldName: oName, newName: nName, oldStats: oStats, newStats: nStats });
        counts.stats++;
      } else {
        byKey.set(key, { status: "renamed", oldName: oName, newName: nName });
        counts.renamed++;
      }
    }
  }

  counts.moved = moved.length;
  return { byKey, removed, moved, counts };
}

export const DIFF_COLORS: Record<string, string> = {
  added: "#4ad6a0",
  removed: "#ef5d5d",
  stats: "#f5b740",
  renamed: "#5fd6cd",
  moved: "#6f93ff",
};
