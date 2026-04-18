import { cn } from "../../lib/utils";
import { useEffect, useRef, useState, type CSSProperties, type ReactNode, type MouseEvent } from "react";

interface BackgroundGradientAnimationProps {
  gradientBackgroundStart?: string;
  gradientBackgroundEnd?: string;
  firstColor?: string;
  secondColor?: string;
  thirdColor?: string;
  fourthColor?: string;
  fifthColor?: string;
  pointerColor?: string;
  size?: string;
  blendingValue?: string;
  children?: ReactNode;
  className?: string;
  interactive?: boolean;
  containerClassName?: string;
}

export const BackgroundGradientAnimation = ({
  gradientBackgroundStart = "rgb(8, 10, 20)",
  gradientBackgroundEnd = "rgb(6, 8, 18)",
  firstColor = "18, 113, 255",
  secondColor = "221, 74, 255",
  thirdColor = "100, 220, 255",
  fourthColor = "200, 50, 50",
  fifthColor = "180, 180, 50",
  pointerColor = "140, 100, 255",
  size = "80%",
  blendingValue = "hard-light",
  children,
  className,
  interactive = true,
  containerClassName,
}: BackgroundGradientAnimationProps) => {
  const interactiveRef = useRef<HTMLDivElement>(null);
  const [curX, setCurX] = useState(0);
  const [curY, setCurY] = useState(0);
  const [tgX, setTgX] = useState(0);
  const [tgY, setTgY] = useState(0);

  useEffect(() => {
    document.body.style.setProperty("--gradient-background-start", gradientBackgroundStart);
    document.body.style.setProperty("--gradient-background-end", gradientBackgroundEnd);
    document.body.style.setProperty("--first-color", firstColor);
    document.body.style.setProperty("--second-color", secondColor);
    document.body.style.setProperty("--third-color", thirdColor);
    document.body.style.setProperty("--fourth-color", fourthColor);
    document.body.style.setProperty("--fifth-color", fifthColor);
    document.body.style.setProperty("--pointer-color", pointerColor);
    document.body.style.setProperty("--size", size);
    document.body.style.setProperty("--blending-value", blendingValue);
  }, []);

  useEffect(() => {
    function move() {
      if (!interactiveRef.current) return;
      setCurX(curX + (tgX - curX) / 20);
      setCurY(curY + (tgY - curY) / 20);
      interactiveRef.current.style.transform = `translate(${Math.round(curX)}px, ${Math.round(curY)}px)`;
    }
    move();
  }, [tgX, tgY]);

  const handleMouseMove = (event: MouseEvent<HTMLDivElement>) => {
    if (interactiveRef.current) {
      const rect = interactiveRef.current.getBoundingClientRect();
      setTgX(event.clientX - rect.width / 2);
      setTgY(event.clientY - rect.height / 2);
    }
  };

  const [isSafari, setIsSafari] = useState(false);
  useEffect(() => {
    setIsSafari(/^((?!chrome|android).)*safari/i.test(navigator.userAgent));
  }, []);

  return (
    <div
      className={cn("relative h-screen w-screen overflow-hidden", containerClassName)}
      style={{
        background: `linear-gradient(40deg, ${gradientBackgroundStart}, ${gradientBackgroundEnd})`,
      }}
    >
      <svg className="hidden">
        <defs>
          <filter id="blurMe">
            <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
            <feColorMatrix
              in="blur"
              mode="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -8"
              result="goo"
            />
            <feBlend in="SourceGraphic" in2="goo" />
          </filter>
        </defs>
      </svg>
      <div
        className={cn("", className)}
        style={{ filter: `url(#blurMe) ${isSafari ? "blur(0px)" : ""}` }}
      >
        {children}
      </div>
      <div
        className="gradients-container"
        style={{
          filter: `blur(40px)`,
          position: "absolute",
          inset: 0,
          overflow: "hidden",
        }}
        onMouseMove={interactive ? handleMouseMove : undefined}
      >
        {/* Blob 1 */}
        <div
          className="absolute top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]"
          style={{
            width: "var(--size)",
            height: "var(--size)",
            background: `radial-gradient(circle at center, rgba(var(--first-color), 0.8) 0, rgba(var(--first-color), 0) 50%) no-repeat`,
            mixBlendMode: blendingValue as CSSProperties["mixBlendMode"],
            animation: "moveVertical 30s ease infinite",
            opacity: 1,
          }}
        />
        {/* Blob 2 */}
        <div
          className="absolute top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]"
          style={{
            width: "var(--size)",
            height: "var(--size)",
            background: `radial-gradient(circle at center, rgba(var(--second-color), 0.8) 0, rgba(var(--second-color), 0) 50%) no-repeat`,
            mixBlendMode: blendingValue as CSSProperties["mixBlendMode"],
            animation: "moveInCircle 20s reverse infinite",
            opacity: 1,
            transformOrigin: "calc(50% - 400px)",
          }}
        />
        {/* Blob 3 */}
        <div
          className="absolute top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2-200px)]"
          style={{
            width: "var(--size)",
            height: "var(--size)",
            background: `radial-gradient(circle at center, rgba(var(--third-color), 0.8) 0, rgba(var(--third-color), 0) 50%) no-repeat`,
            mixBlendMode: blendingValue as CSSProperties["mixBlendMode"],
            animation: "moveInCircle 40s linear infinite",
            opacity: 1,
            transformOrigin: "calc(50% + 400px)",
          }}
        />
        {/* Blob 4 */}
        <div
          className="absolute top-[calc(50%-var(--size)/2)] left-[calc(50%-var(--size)/2)]"
          style={{
            width: "var(--size)",
            height: "var(--size)",
            background: `radial-gradient(circle at center, rgba(var(--fourth-color), 0.8) 0, rgba(var(--fourth-color), 0) 50%) no-repeat`,
            mixBlendMode: blendingValue as CSSProperties["mixBlendMode"],
            animation: "moveHorizontal 40s ease infinite",
            opacity: 0.7,
            transformOrigin: "calc(50% - 200px) calc(50% + 100px)",
          }}
        />
        {/* Blob 5 */}
        <div
          className="absolute top-[calc(50%-var(--size)/2+200px)] left-[calc(50%-var(--size)/2-500px)]"
          style={{
            width: "var(--size)",
            height: "var(--size)",
            background: `radial-gradient(circle at center, rgba(var(--fifth-color), 0.8) 0, rgba(var(--fifth-color), 0) 50%) no-repeat`,
            mixBlendMode: blendingValue as CSSProperties["mixBlendMode"],
            animation: "moveInCircle 20s ease infinite",
            opacity: 1,
            transformOrigin: "calc(50% - 800px) calc(50% + 200px)",
          }}
        />
        {/* Interactive pointer blob */}
        {interactive && (
          <div
            ref={interactiveRef}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{
              width: "100%",
              height: "100%",
              background: `radial-gradient(circle at center, rgba(var(--pointer-color), 0.8) 0, rgba(var(--pointer-color), 0) 50%) no-repeat`,
              mixBlendMode: blendingValue as CSSProperties["mixBlendMode"],
              opacity: 0.7,
            }}
          />
        )}
      </div>
    </div>
  );
};
