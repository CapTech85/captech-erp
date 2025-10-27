/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./**/*.py", // si tu génères des classes côté Python
  ],
  theme: {
    extend: {
      colors: {
        // alias "primary" calé sur le bleu Tailwind
        primary: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
  safelist: [
    // classes conditionnelles fréquentes pour éviter la purge
    "nav-active",
    { pattern: /^bg-(slate|blue|red|green|amber|emerald)-(50|100|600|700)$/ },
    { pattern: /^text-(slate|blue|red|green|amber|emerald)-(500|600|700)$/ },
    { pattern: /^border-(slate|blue|red)-(200|300)$/ },
    { pattern: /^grid-cols-(1|2|3|4|5|6)$/ },
    { pattern: /^bg-(slate|blue)-(50|100|700)$/, variants: ["hover"] },   // au lieu de /^hover:bg-...$/
    { pattern: /^grid-cols-(2|3|4)$/, variants: ["md"] },                 // au lieu de /^md:grid-cols-...$/
    { pattern: /^(from|to|via)-(primary|blue|indigo)-(50|100|200|300|400|500|600|700|800|900|950)$/ },
  ],
};
