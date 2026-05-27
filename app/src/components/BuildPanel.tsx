import { memo } from "react";
import type { Tag } from "../lib/buildState";

interface Props {
  hasClass: boolean;
  mainUsed: number;
  budget: number;
  bonus: number;
  ascUsed: number;
  ascBudget: number;
  mode: Tag;
  set1: number;
  set2: number;
  swapMax: number;
  setMode: (m: Tag) => void;
  setBaseBudget: (n: number) => void;
  onClear: () => void;
}

function BuildPanel({
  hasClass,
  mainUsed,
  budget,
  bonus,
  ascUsed,
  ascBudget,
  mode,
  set1,
  set2,
  swapMax,
  setMode,
  setBaseBudget,
  onClear,
}: Props) {
  return (
    <div className="panel build">
      <div className="build__stat">
        <span className="build__label">패시브</span>
        <span className={"build__val" + (mainUsed > budget ? " over" : "")}>
          {mainUsed}
          <span className="build__slash">/</span>
          <input
            className="build__budget"
            type="number"
            value={budget - bonus}
            min={0}
            onChange={(e) => setBaseBudget(Math.max(0, parseInt(e.target.value || "0", 10)))}
            title="기본 패시브 포인트 (캠페인+레벨). 수정 가능."
          />
          {bonus > 0 && <span className="build__bonus">+{bonus}</span>}
        </span>
      </div>

      <div className="build__sep" />

      <div className="build__stat">
        <span className="build__label">어센던시</span>
        <span className={"build__val" + (ascUsed > ascBudget ? " over" : "")}>
          {ascUsed}
          <span className="build__slash">/</span>
          {ascBudget}
        </span>
      </div>

      <div className="build__sep" />

      <div className="build__stat">
        <span className="build__label">무기 교체</span>
        <div className="build__seg">
          <button className={mode === 0 ? "active" : ""} onClick={() => setMode(0)} title="공유 — 배분/제거">
            공유
          </button>
          <button
            className={"set1" + (mode === 1 ? " active" : "")}
            onClick={() => setMode(1)}
            title="세트 I 배분 (빨강)"
          >
            세트 I
          </button>
          <button
            className={"set2" + (mode === 2 ? " active" : "")}
            onClick={() => setMode(2)}
            title="세트 II 배분 (초록)"
          >
            세트 II
          </button>
        </div>
        <span className="build__sets">
          <span className="s1" title="세트 I 포인트">
            {set1}
            <span className="cap">/{swapMax}</span>
          </span>
          <span className="s2" title="세트 II 포인트">
            {set2}
            <span className="cap">/{swapMax}</span>
          </span>
        </span>
      </div>

      <div className="build__sep" />

      <button className="build__clear" onClick={onClear} title="배분 초기화" aria-label="초기화">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
          <path d="M3 3v5h5" />
        </svg>
      </button>
    </div>
  );
}

export default memo(BuildPanel);
