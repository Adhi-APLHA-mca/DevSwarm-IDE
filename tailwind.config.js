/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./frontend/index.html",
    "./frontend/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vscode-bg': '#1e1e1e',
        'vscode-panel': '#252526',
        'vscode-header': '#2d2d30',
        'vscode-border': '#3e3e42',
      },
      fontFamily: {
        'mono': ['Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
