import { Suspense, lazy } from "react";

const Spline = lazy(() => import("@splinetool/react-spline"));

interface SplineSceneProps {
  scene: string;
  className?: string;
}

function SplineScene({ scene, className }: SplineSceneProps) {
  return (
    <Suspense
      fallback={
        <div className="w-full h-full flex items-center justify-center" style={{ display: "flex", alignItems: "center", justifyContent: "center", width: "100%", height: "100%" }}>
          <span style={{ color: "rgba(0,212,255,0.4)", fontFamily: "var(--font-mono)", fontSize: "12px", letterSpacing: "0.12em" }}>
            LOADING 3D SCENE…
          </span>
        </div>
      }
    >
      <Spline scene={scene} className={className} />
    </Suspense>
  );
}

export { SplineScene };
