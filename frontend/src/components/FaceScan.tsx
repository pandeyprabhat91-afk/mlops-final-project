import type React from "react";

const V: [number, number][] = [
  [220,46],[143,73],[297,73],[103,141],[337,141],
  [125,164],[168,148],[220,146],[272,148],[315,164],
  [125,184],[161,176],[193,184],[247,184],[279,176],[315,184],
  [114,229],[326,229],[175,209],[265,209],[220,210],
  [196,243],[244,243],[220,254],[120,275],[320,275],
  [165,280],[275,280],[197,268],[243,268],
  [220,293],[128,322],[312,322],[167,354],[273,354],[220,378],
];

const EDGES: [number,number][] = [
  [0,1],[0,2],[1,2],[1,3],[2,4],[3,5],[4,9],[3,6],[4,8],
  [0,7],[6,7],[7,8],[1,6],[2,8],[5,6],[8,9],
  [5,10],[6,12],[9,15],[8,13],
  [10,11],[11,12],[13,14],[14,15],
  [10,16],[15,17],[12,18],[13,19],[11,18],[14,19],
  [16,18],[17,19],[18,20],[19,20],[16,24],[17,25],
  [20,21],[20,22],[21,22],[21,23],[22,23],
  [23,26],[23,27],[21,26],[22,27],
  [26,28],[28,29],[29,27],[26,30],[27,30],[28,30],[29,30],
  [24,26],[25,27],[24,31],[25,32],
  [30,31],[30,32],[31,33],[32,34],[33,35],[34,35],[33,34],[30,35],
];

const MAJOR = new Set([0,3,4,10,15,16,17,20,23,26,27,30,31,32,35]);
const CX = 220, CY = 210;

export const FaceScan: React.FC = () => (
  <div className="face-wrap" aria-hidden="true">
    <svg viewBox="0 0 440 480" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="fv" cx="50%" cy="42%" r="52%">
          <stop offset="0%"   stopColor="#1a3d1e" />
          <stop offset="50%"  stopColor="#142e17" />
          <stop offset="100%" stopColor="#0e1f10" />
        </radialGradient>
        <radialGradient id="hg" cx="50%" cy="18%" r="52%">
          <stop offset="0%"   stopColor="#122a15" />
          <stop offset="100%" stopColor="#0c1a0e" />
        </radialGradient>
        <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#1a5c35" stopOpacity="0" />
          <stop offset="48%"  stopColor="#1a5c35" stopOpacity="0.08" />
          <stop offset="50%"  stopColor="#34a85a" stopOpacity="0.6" />
          <stop offset="52%"  stopColor="#1a5c35" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#1a5c35" stopOpacity="0" />
        </linearGradient>
        <filter id="dg" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <clipPath id="fc">
          <ellipse cx={CX} cy={CY} rx="108" ry="168" />
        </clipPath>
      </defs>

      <circle cx={CX} cy={CY} r="188"
        stroke="#34a85a" strokeOpacity="0.10" strokeWidth="1"
        strokeDasharray="4 6" />
      <circle cx={CX} cy={CY} r="158"
        stroke="#34a85a" strokeOpacity="0.15" strokeWidth="0.75" />

      <circle r="4" fill="#34a85a" fillOpacity="0.9"
        className="face-orbit-dot"
        style={{ filter: "drop-shadow(0 0 6px rgba(52,168,90,0.9))" }} />

      <ellipse cx={CX} cy={175} rx="112" ry="140" fill="url(#hg)" />
      <ellipse cx={CX} cy={CY} rx="107" ry="166" fill="url(#fv)" />

      {EDGES.map(([a,b],i) => (
        <line key={i}
          x1={V[a][0]} y1={V[a][1]} x2={V[b][0]} y2={V[b][1]}
          stroke="#34a85a" strokeOpacity="0.20" strokeWidth="0.75" />
      ))}

      {V.map(([x,y],i) => {
        const big = MAJOR.has(i);
        return (
          <circle key={i} cx={x} cy={y}
            r={big ? 3.5 : 2}
            fill="#34a85a"
            fillOpacity={big ? 0.70 : 0.35}
            filter={big ? "url(#dg)" : undefined}
            className="face-mesh-dot"
            style={{ animationDelay: `${(i * 0.08) % 2}s` }} />
        );
      })}

      <rect x="112" y="-20" width="216" height="32"
        fill="url(#beam)" clipPath="url(#fc)"
        className="face-scan-beam" />
      <line x1="112" y1="0" x2="328" y2="0"
        stroke="#34a85a" strokeWidth="1" strokeOpacity="0.8"
        clipPath="url(#fc)" className="face-scan-beam" />

      <path d="M 28 64 L 28 40 L 52 40" className="face-corner-line" />
      <path d="M 388 40 L 412 40 L 412 64" className="face-corner-line" />
      <path d="M 28 416 L 28 440 L 52 440" className="face-corner-line" />
      <path d="M 388 440 L 412 440 L 412 416" className="face-corner-line" />

      <circle cx="46" cy="24" r="3.5" fill="#4ade80" opacity="0.9"
        className="face-mesh-dot" />
      <text x="56" y="28" fontFamily="'JetBrains Mono', monospace" fontSize="9"
        letterSpacing="0.12em" fill="rgba(255,255,255,0.45)">BIOMETRIC SCAN · ACTIVE</text>

      <text x="220" y="468" textAnchor="middle"
        fontFamily="'JetBrains Mono', monospace" fontSize="8"
        letterSpacing="0.1em" fill="rgba(255,255,255,0.25)">
        36 LANDMARKS · CNN+LSTM
      </text>
    </svg>
  </div>
);
