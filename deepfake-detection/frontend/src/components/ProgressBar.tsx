import type React from "react";
import { useEffect, useRef, useState } from "react";

interface Props {
  loading: boolean;
  error: string | null;
}

const STAGES = [
  { label: "Extracting frames…",   target: 25,  duration: 800  },
  { label: "Detecting faces…",     target: 55,  duration: 1200 },
  { label: "Running model…",       target: 85,  duration: 1500 },
  { label: "Finalizing…",          target: 99,  duration: 99999 }, // holds until API responds
];

export const ProgressBar: React.FC<Props> = ({ loading, error }) => {
  const [progress, setProgress] = useState(0);
  const [stageIdx, setStageIdx] = useState(0);
  const [done, setDone] = useState(false);
  const [visible, setVisible] = useState(false);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  };

  useEffect(() => {
    if (loading) {
      // Reset and start
      setProgress(0);
      setStageIdx(0);
      setDone(false);
      setVisible(true);

      let cumDelay = 0;
      STAGES.forEach((stage, idx) => {
        const t = setTimeout(() => {
          setStageIdx(idx);
          // Animate progress to stage target over the stage duration
          const steps = 20;
          const stepInterval = Math.min(stage.duration / steps, 50);
          const startPct = idx === 0 ? 0 : STAGES[idx - 1].target;
          const delta = stage.target - startPct;
          for (let s = 1; s <= steps; s++) {
            const st = setTimeout(() => {
              setProgress(startPct + Math.round((delta * s) / steps));
            }, s * stepInterval);
            timersRef.current.push(st);
          }
        }, cumDelay);
        timersRef.current.push(t);
        if (idx < STAGES.length - 1) cumDelay += stage.duration;
      });
    } else {
      // API responded — finish or show error
      clearTimers();
      if (visible) {
        if (error) {
          setDone(true);
        } else {
          setProgress(100);
          setDone(true);
          const t = setTimeout(() => setVisible(false), 600);
          timersRef.current.push(t);
        }
      }
    }
    return clearTimers;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  if (!visible) return null;

  return (
    <div className={`progress-wrap ${done && error ? "progress-error" : ""}`}>
      <div className="progress-track">
        <div
          className={`progress-fill ${done && !error ? "progress-complete" : ""}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="progress-label">
        {error && done
          ? error
          : STAGES[stageIdx]?.label}
      </p>
    </div>
  );
};
