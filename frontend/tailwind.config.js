/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        mono: [
          "var(--font-ibm-plex-mono)",
          "IBM Plex Mono",
          "Noto Sans SC",
          "JetBrains Mono",
          "Courier New",
          "monospace",
        ],
        display: ["var(--font-ibm-plex-mono)", "IBM Plex Mono", "Noto Sans SC", "monospace"],
      },
      colors: {
        "absolute-zero": "#000000",
        "titanium-white": "#FFFFFF",
        "echo-gray": "#808080",
        "echo-mid-dark": "#262626",
        "echo-light-border": "#D9D9D9",
        "echo-success": "#4EDE80",
        "echo-warning": "#EAB308",
      },
    },
  },
  plugins: [],
};
