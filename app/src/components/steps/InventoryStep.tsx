import { memo } from "react";
import { levelParts, makeLevel, type BuildInventorySlot } from "../../lib/buildFile";
import { usePoeDb } from "../../lib/poedb";
import MarkupEditor from "../MarkupEditor";

interface Props {
  inventory: BuildInventorySlot[];
  setInventory: (inv: BuildInventorySlot[]) => void;
  selectedAsc: string | null;
}

// inventory_id values per the .build format (best-effort PoE2 slot ids).
const BASE_SLOTS: { id: string; label: string }[] = [
  { id: "Weapon1", label: "무기 — 세트 I" },
  { id: "Weapon2", label: "보조무기 — 세트 I" },
  { id: "Weapon1Swap", label: "무기 — 세트 II" },
  { id: "Weapon2Swap", label: "보조무기 — 세트 II" },
  { id: "Helmet", label: "투구" },
  { id: "BodyArmour", label: "몸통 방어구" },
  { id: "Gloves", label: "장갑" },
  { id: "Boots", label: "신발" },
  { id: "Amulet", label: "부적" },
  { id: "Ring1", label: "반지 1" },
  { id: "Ring2", label: "반지 2" },
  { id: "Belt", label: "벨트" },
];

function InventoryStep({ inventory, setInventory, selectedAsc }: Props) {
  const db = usePoeDb();
  // Ritualist (Huntress3) can equip a third ring.
  const slots =
    selectedAsc === "Huntress3"
      ? [...BASE_SLOTS.slice(0, 11), { id: "Ring3", label: "반지 3" }, ...BASE_SLOTS.slice(11)]
      : BASE_SLOTS;
  const byId: Record<string, BuildInventorySlot> = {};
  for (const s of inventory) byId[s.inventory_id] = s;

  const update = (id: string, p: Partial<BuildInventorySlot>) => {
    const merged: BuildInventorySlot = { ...(byId[id] ?? { inventory_id: id }), ...p };
    const next = inventory.filter((s) => s.inventory_id !== id);
    if (merged.unique?.trim() || merged.hint?.trim() || merged.level_interval != null) next.push(merged);
    setInventory(next);
  };

  return (
    <div className="panel step step--inv">
      <div className="step__title">인벤토리</div>
      <datalist id="poedb-uniques">
        {db.uniques.map((u) => (
          <option key={u} value={u} />
        ))}
      </datalist>

      <div className="inv-grid">
        {slots.map((slot) => {
          const s = byId[slot.id];
          const hasContent = !!(s?.unique?.trim() || s?.hint?.trim());
          return (
            <div className="inv-slot-block" key={slot.id}>
              <div className="inv-slot">
                <span className="inv-slot__label">{slot.label}</span>
                <input
                  className="inv-slot__field"
                  list="poedb-uniques"
                  placeholder="유니크 아이템…"
                  value={s?.unique ?? ""}
                  onChange={(e) => update(slot.id, { unique: e.target.value })}
                />
                <input
                  className="lvl-field"
                  placeholder="레벨"
                  title="시작 레벨 (선택사항)"
                  value={levelParts(s?.level_interval)[0]}
                  onChange={(e) =>
                    update(slot.id, { level_interval: makeLevel(e.target.value, levelParts(s?.level_interval)[1]) })
                  }
                />
                <input
                  className="lvl-field"
                  placeholder="~"
                  title="종료 레벨 (선택사항)"
                  value={levelParts(s?.level_interval)[1]}
                  onChange={(e) =>
                    update(slot.id, { level_interval: makeLevel(levelParts(s?.level_interval)[0], e.target.value) })
                  }
                />
              </div>
              {hasContent && (
                <MarkupEditor
                  value={s?.hint ?? ""}
                  onChange={(v) => update(slot.id, { hint: v })}
                  placeholder="힌트 (선택사항) — 우클릭으로 서식 지정"
                  rows={1}
                />
              )}
            </div>
          );
        })}
      </div>

      {db.uniques.length === 0 && (
        <p className="step__hint">아이템 자동완성을 사용할 수 없습니다 — 직접 입력하세요.</p>
      )}
    </div>
  );
}

export default memo(InventoryStep);
