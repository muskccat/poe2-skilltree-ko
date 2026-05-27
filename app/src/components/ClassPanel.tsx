import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { ClassInfo } from "../types";
import { CLASS_NAME_KO, ASC_ID_KO } from "../lib/text";

interface Props {
  classes: ClassInfo[];
  selectedClass: number | null;
  selectedAsc: string | null;
  newAscIds: Set<string>;
  onSelectClass: (idx: number | null) => void;
  onSelectAsc: (id: string | null) => void;
  onNewBuild: () => void;
  onImport: () => void;
  onEdit: () => void;
  canEdit: boolean;
}

const isPlayable = (c: ClassInfo) => c.ascendancies.some((a) => a && a.name);

function ClassPanel({
  classes,
  selectedClass,
  selectedAsc,
  newAscIds,
  onSelectClass,
  onSelectAsc,
  onNewBuild,
  onImport,
  onEdit,
  canEdit,
}: Props) {
  const cls = selectedClass != null ? classes[selectedClass] : null;
  const ascendancies = cls ? cls.ascendancies.filter((a) => a && a.name) : [];

  return (
    <motion.div
      className="panel classes"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="class-actions">
        <button className="ca-btn primary" onClick={onNewBuild}>
          ✦ 새 빌드
        </button>
        <button className="ca-btn" onClick={onImport}>
          가져오기
        </button>
        {canEdit && (
          <button className="ca-btn edit" onClick={onEdit}>
            편집 ✎
          </button>
        )}
      </div>
      <div className="panel__title">클래스 · 어센던시</div>
      <div className="class-grid">
        {classes.map((c, i) =>
          isPlayable(c) ? (
            <button
              key={c.name}
              className={"class-chip" + (selectedClass === i ? " active" : "")}
              onClick={() => onSelectClass(selectedClass === i ? null : i)}
            >
              {CLASS_NAME_KO[c.name] ?? c.name}
            </button>
          ) : null
        )}
      </div>

      <AnimatePresence>
        {ascendancies.length > 0 && (
          <motion.div
            className="asc-row"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            {ascendancies.map((a) => {
              const isNew = newAscIds.has(a.id);
              return (
                <div
                  key={a.id}
                  className={
                    "asc-chip" +
                    (selectedAsc === a.id ? " active" : "") +
                    (isNew ? " new" : "")
                  }
                  onClick={() => onSelectAsc(selectedAsc === a.id ? null : a.id)}
                >
                  <span className="asc-chip__name">{ASC_ID_KO[a.id] ?? a.name}</span>
                  <span className="asc-chip__tag">{isNew ? "0.5 신규" : a.id}</span>
                </div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default memo(ClassPanel);
