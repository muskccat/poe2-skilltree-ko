import { memo, useEffect, useState } from "react";
import type { Camera } from "../lib/camera";

interface Props {
  camera: Camera;
  onReset: () => void;
}

// Polls the camera for the zoom readout internally so zoom changes never
// re-render the rest of the app.
function Controls({ camera, onReset }: Props) {
  const [pct, setPct] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setPct(Math.round(camera.zoom * 100)), 150);
    return () => clearInterval(t);
  }, [camera]);

  const z = (factor: number) =>
    camera.zoomAt(factor, window.innerWidth / 2, window.innerHeight / 2);

  return (
    <div className="panel controls">
      <button title="확대" onClick={() => z(1.3)}>
        +
      </button>
      <div className="zoom-readout">{pct}%</div>
      <button title="축소" onClick={() => z(1 / 1.3)}>
        −
      </button>
      <button title="트리 맞추기" onClick={onReset} style={{ fontSize: 13 }}>
        ⤢
      </button>
    </div>
  );
}

export default memo(Controls);
