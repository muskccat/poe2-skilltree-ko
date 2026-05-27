import { memo } from "react";
import { levelParts, makeLevel, type BuildSkill } from "../../lib/buildFile";
import { usePoeDb } from "../../lib/poedb";
import MarkupEditor from "../MarkupEditor";

interface Props {
  skills: BuildSkill[];
  setSkills: (sk: BuildSkill[]) => void;
  version: string;
}

function SkillsStep({ skills, setSkills }: Props) {
  const db = usePoeDb();

  const patch = (i: number, fn: (s: BuildSkill) => BuildSkill) =>
    setSkills(skills.map((s, idx) => (idx === i ? fn(s) : s)));

  const addSkill = () => setSkills([...skills, { id: "", supports: [] }]);
  const removeSkill = (i: number) => setSkills(skills.filter((_, idx) => idx !== i));
  const addSupport = (i: number) => patch(i, (s) => ({ ...s, supports: [...(s.supports ?? []), { id: "" }] }));
  const setSupport = (i: number, j: number, fn: (x: { id: string; level_interval?: number | number[] }) => typeof x) =>
    patch(i, (s) => ({ ...s, supports: (s.supports ?? []).map((x, k) => (k === j ? fn(x) : x)) }));
  const removeSupport = (i: number, j: number) =>
    patch(i, (s) => ({ ...s, supports: (s.supports ?? []).filter((_, k) => k !== j) }));

  return (
    <div className="panel step step--skills">
      <div className="step__title">스킬</div>
      <datalist id="poedb-skills">
        {db.skillGems.map((g) => (
          <option key={g} value={g} />
        ))}
      </datalist>
      <datalist id="poedb-supports">
        {db.supportGems.map((g) => (
          <option key={g} value={g} />
        ))}
      </datalist>

      <div className="skills-list">
        {skills.map((s, i) => (
          <div className="skill-card" key={i}>
            <div className="skill-card__head">
              <input
                className="skill-card__gem"
                list="poedb-skills"
                placeholder="스킬 젬…"
                value={s.id}
                onChange={(e) => patch(i, (x) => ({ ...x, id: e.target.value }))}
              />
              <input
                className="lvl-field"
                placeholder="레벨"
                title="시작 레벨 (선택사항)"
                value={levelParts(s.level_interval)[0]}
                onChange={(e) =>
                  patch(i, (x) => ({ ...x, level_interval: makeLevel(e.target.value, levelParts(x.level_interval)[1]) }))
                }
              />
              <input
                className="lvl-field"
                placeholder="~"
                title="종료 레벨 (선택사항)"
                value={levelParts(s.level_interval)[1]}
                onChange={(e) =>
                  patch(i, (x) => ({ ...x, level_interval: makeLevel(levelParts(x.level_interval)[0], e.target.value) }))
                }
              />
              <button className="skill-card__rm" onClick={() => removeSkill(i)} title="스킬 제거">
                ✕
              </button>
            </div>
            <div className="skill-supports">
              {(s.supports ?? []).map((sup, j) => (
                <div className="skill-support" key={j}>
                  <input
                    list="poedb-supports"
                    placeholder="서포트 젬…"
                    value={sup.id}
                    onChange={(e) => setSupport(i, j, (x) => ({ ...x, id: e.target.value }))}
                  />
                  <input
                    className="lvl-field"
                    placeholder="레벨"
                    title="시작 레벨 (선택사항)"
                    value={levelParts(sup.level_interval)[0]}
                    onChange={(e) =>
                      setSupport(i, j, (x) => ({ ...x, level_interval: makeLevel(e.target.value, levelParts(x.level_interval)[1]) }))
                    }
                  />
                  <input
                    className="lvl-field"
                    placeholder="~"
                    title="종료 레벨 (선택사항)"
                    value={levelParts(sup.level_interval)[1]}
                    onChange={(e) =>
                      setSupport(i, j, (x) => ({ ...x, level_interval: makeLevel(levelParts(x.level_interval)[0], e.target.value) }))
                    }
                  />
                  <button onClick={() => removeSupport(i, j)} title="서포트 제거">
                    –
                  </button>
                  <MarkupEditor
                    value={sup.additional_text ?? ""}
                    onChange={(v) => setSupport(i, j, (x) => ({ ...x, additional_text: v }))}
                    placeholder="서포트 메모 (선택사항)"
                    rows={1}
                  />
                </div>
              ))}
              <button className="skill-support__add" onClick={() => addSupport(i)}>
                + 서포트
              </button>
            </div>
            <MarkupEditor
              value={s.additional_text ?? ""}
              onChange={(v) => patch(i, (x) => ({ ...x, additional_text: v }))}
              placeholder="스킬 메모 — 우클릭으로 서식 지정"
              rows={1}
            />
          </div>
        ))}
      </div>

      <button className="step__add" onClick={addSkill}>
        + 스킬 추가
      </button>
      {db.skillGems.length === 0 && (
        <p className="step__hint">젬 자동완성을 사용할 수 없습니다 — 직접 입력하세요.</p>
      )}
    </div>
  );
}

export default memo(SkillsStep);
