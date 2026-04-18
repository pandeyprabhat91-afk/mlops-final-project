import type React from "react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";

const STEPS = [
  {
    targetId: "upload-area",
    title: "Upload your video",
    body: "Drop your MP4 here to start. Files up to 100 MB are accepted.",
  },
  {
    targetId: "result-card-anchor",
    title: "Your verdict",
    body: "Your verdict and confidence score appear here after analysis completes.",
  },
  {
    targetId: "gradcam-anchor",
    title: "Grad-CAM heatmap",
    body: "Highlighted regions show which parts of the frame influenced the prediction most.",
  },
  {
    targetId: "help-nav-link",
    title: "Need help?",
    body: "Visit the Help page for FAQs, the chatbot, and support ticket submission.",
  },
];

function getAnchorRect(id: string): DOMRect | null {
  const el = document.getElementById(id);
  return el ? el.getBoundingClientRect() : null;
}

export const OnboardingTour: React.FC = () => {
  const { role } = useAuth();
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (role === "admin") return;
    if (localStorage.getItem("tour_done")) return;
    const t = setTimeout(() => setVisible(true), 800);
    return () => clearTimeout(t);
  }, [role]);

  useEffect(() => {
    if (!visible) return;
    const r = getAnchorRect(STEPS[step].targetId);
    setRect(r);
  }, [visible, step]);

  if (!visible || !rect) return null;

  const dismiss = () => {
    setVisible(false);
    localStorage.setItem("tour_done", "1");
  };

  const next = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      dismiss();
    }
  };

  return (
    <div
      className="tour-tooltip"
      style={{ position: "fixed", top: rect.bottom + 12, left: Math.min(rect.left, window.innerWidth - 300) }}
    >
      <div className="tour-arrow" />
      <p className="tour-step">{step + 1} / {STEPS.length}</p>
      <p className="tour-title">{STEPS[step].title}</p>
      <p className="tour-body">{STEPS[step].body}</p>
      <div className="tour-actions">
        <button type="button" className="tour-skip" onClick={dismiss}>Skip Tour</button>
        <button type="button" className="btn tour-next" onClick={next}>
          {step < STEPS.length - 1 ? "Next" : "Done"}
        </button>
      </div>
    </div>
  );
};
