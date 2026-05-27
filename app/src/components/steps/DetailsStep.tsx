import { memo } from "react";
import type { ClassInfo } from "../../types";
import { CLASS_NAME_KO, ASC_ID_KO } from "../../lib/text";

interface Props {
  name: string;
  author: string;
  description: string;
  setField: (field: "name" | "author" | "description", value: string) => void;
  classes: ClassInfo[];
  selectedClass: number | null;
  selectedAsc: string | null;
  newAscIds: Set<string>;
  onSelectClass: (idx: number | null) => void;
  onSelectAsc: (id: string | null) => void;
}

const isPlayable = (c: ClassInfo) => c.ascendancies.some((a) => a && a.name);

function DetailsStep({
  name,
  author,
  description,
  setField,
  classes,
  selectedClass,
  selectedAsc,
  newAscIds,
  onSelectClass,
  onSelectAsc,
}: Props) {
  const cls = selectedClass != null ? classes[selectedClass] : null;
  const ascendancies = cls ? cls.ascendancies.filter((a) => a && a.name) : [];

  return (
    <div className="panel step step--details">
      <div className="step__title">빌드 정보</div>

      <div className="field-row">
        <label className="field">
          <span className="field__label">이름</span>
          <input value={name} onChange={(e) => setField("name", e.target.value)} placeholder="내 빌드" autoFocus />
        </label>
        <label className="field">
          <span className="field__label">작성자</span>
          <input value={author} onChange={(e) => setField("author", e.target.value)} placeholder="선택사항" />
        </label>
      </div>
      <label className="field">
        <span className="field__label">설명</span>
        <textarea
          value={description}
          rows={2}
          onChange={(e) => setField("description", e.target.value)}
          placeholder="선택사항"
        />
      </label>

      <div className="field__label" style={{ marginTop: 4 }}>
        클래스
      </div>
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

      {ascendancies.length > 0 && (
        <div className="asc-row">
          {ascendancies.map((a) => (
            <div
              key={a.id}
              className={
                "asc-chip" + (selectedAsc === a.id ? " active" : "") + (newAscIds.has(a.id) ? " new" : "")
              }
              onClick={() => onSelectAsc(selectedAsc === a.id ? null : a.id)}
            >
              <span className="asc-chip__name">{ASC_ID_KO[a.id] ?? a.name}</span>
              <span className="asc-chip__tag">{newAscIds.has(a.id) ? "0.5 신규" : a.id}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default memo(DetailsStep);
