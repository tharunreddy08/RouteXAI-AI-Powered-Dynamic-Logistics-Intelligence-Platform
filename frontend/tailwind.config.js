/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#0a0e16",
          900: "#0f1520",
          800: "#141b29",
          700: "#1b2434",
        },
        panel: "#111826",
        panelBorder: "#22304a",
        signal: {
          DEFAULT: "#3ee6c4",
          dim: "#1f8f79",
          glow: "#8ffaea",
        },
        route: {
          1: "#3ee6c4",
          2: "#f5a623",
          3: "#c792ea",
          4: "#5ec8f5",
          5: "#ff7a7a",
        },
        status: {
          normal: "#7c8aa3",
          express: "#f5a623",
          emergency: "#ff5d5d",
          success: "#3ee6c4",
          warn: "#f5a623",
          danger: "#ff5d5d",
        },
        ink: {
          DEFAULT: "#e7edf5",
          dim: "#9fb0c9",
          faint: "#5b6b85",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.6)",
        glow: "0 0 24px -4px rgba(62,230,196,0.35)",
      },
      backgroundImage: {
        "grid-fade": "radial-gradient(ellipse at top, rgba(62,230,196,0.08), transparent 60%)",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.5", transform: "scale(0.85)" },
        },
        dash: {
          to: { strokeDashoffset: "-24" },
        },
      },
      animation: {
        pulseDot: "pulseDot 1.6s ease-in-out infinite",
        dash: "dash 1.2s linear infinite",
      },
    },
  },
  plugins: [],
};
