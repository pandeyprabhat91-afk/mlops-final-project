/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  corePlugins: {
    // Disable CSS reset - existing design system handles base styles
    preflight: false,
  },
  theme: {
    extend: {
      animation: {
        first:  "moveVertical 30s ease infinite",
        second: "moveInCircle 20s reverse infinite",
        third:  "moveInCircle 40s linear infinite",
        fourth: "moveHorizontal 40s ease infinite",
        fifth:  "moveInCircle 20s ease infinite",
        spotlight: "spotlight 2s ease 0.75s 1 forwards",
      },
      keyframes: {
        moveHorizontal: {
          "0%":   { transform: "translateX(-50%) translateY(-10%)" },
          "50%":  { transform: "translateX(50%)  translateY(10%)"  },
          "100%": { transform: "translateX(-50%) translateY(-10%)" },
        },
        moveInCircle: {
          "0%":   { transform: "rotateZ(0deg)"   },
          "50%":  { transform: "rotateZ(180deg)" },
          "100%": { transform: "rotateZ(360deg)" },
        },
        moveVertical: {
          "0%":   { transform: "translateY(-50%)" },
          "50%":  { transform: "translateY(50%)"  },
          "100%": { transform: "translateY(-50%)" },
        },
        spotlight: {
          "0%":   { opacity: "0", transform: "translate(-72%, -62%) scale(0.5)" },
          "100%": { opacity: "1", transform: "translate(-50%, -40%) scale(1)"   },
        },
      },
    },
  },
  plugins: [],
};
