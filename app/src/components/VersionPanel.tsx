import { memo } from "react";
import { motion } from "framer-motion";
import type { VersionDiff } from "../types";
import { DIFF_COLORS } from "../lib/diff";

interface Props {
  version: "0.5" | "0.4";
  setVersion: (v: "0.5" | "0.4") => void;
  diffOn: boolean;
  setDiffOn: (b: boolean) => void;
  diff: VersionDiff | null;
}

function VersionPanel({ version, setVersion, diffOn, setDiffOn, diff }: Props) {
  const c = diff?.counts;
  return (
    <motion.div
      className="panel version"
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15 }}
    >
      <div className="panel__title">트리 버전</div>
      <div className="seg">
        <button className={version === "0.4" ? "active" : ""} onClick={() => setVersion("0.4")}>
          0.4.0
        </button>
        <button className={version === "0.5" ? "active" : ""} onClick={() => setVersion("0.5")}>
          0.5.0
        </button>
      </div>

      <div className="toggle" onClick={() => setDiffOn(!diffOn)}>
        <div>
          <div className="toggle__label">0.5 변경사항 하이라이트</div>
          <div className="toggle__hint">0.4 대비 변경된 노드 표시</div>
        </div>
        <div className={"switch" + (diffOn ? " on" : "")} />
      </div>

      {diffOn && c && (
        <motion.div className="legend" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="legend__row">
            <span className="legend__swatch" style={{ background: DIFF_COLORS.added, color: DIFF_COLORS.added }} />
            신규 패시브 / 노터블
            <span className="legend__count">{c.added}</span>
          </div>
          <div className="legend__row">
            <span className="legend__swatch" style={{ background: DIFF_COLORS.stats, color: DIFF_COLORS.stats }} />
            스탯 변경
            <span className="legend__count">{c.stats}</span>
          </div>
          <div className="legend__row">
            <span className="legend__swatch" style={{ background: DIFF_COLORS.renamed, color: DIFF_COLORS.renamed }} />
            이름 변경
            <span className="legend__count">{c.renamed}</span>
          </div>
          <div className="legend__row">
            <span className="legend__swatch" style={{ background: DIFF_COLORS.removed, color: DIFF_COLORS.removed }} />
            삭제 (잔상)
            <span className="legend__count">{c.removed}</span>
          </div>
          <div className="legend__row">
            <span className="legend__swatch" style={{ background: DIFF_COLORS.moved, color: DIFF_COLORS.moved }} />
            위치 이동
            <span className="legend__count">{c.moved}</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default memo(VersionPanel);
