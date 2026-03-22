/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        body: ["'DM Sans'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        ink: {
          950: "#060810",
          900: "#0c1021",
          800: "#121829",
          700: "#1a2235",
          600: "#243048",
        },
        gold: {
          400: "#f4c842",
          500: "#e8b830",
          600: "#c99a1a",
        },
        jade: {
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        },
        scarlet: {
          400: "#f87171",
          500: "#ef4444",
        },
        slate: {
          350: "#94a3b8",
        },
      },
      backgroundImage: {
        "mesh-dark": "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(244,200,66,0.08), transparent)",
        "mesh-subtle": "radial-gradient(ellipse 60% 40% at 80% 60%, rgba(52,211,153,0.05), transparent)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
