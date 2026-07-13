import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: { extend: {
    colors: { ink: "#14232c", paper: "#f4f5f2", navy: "#173c47", accent: "#2f6f67", mist: "#dce4e2", risk: "#9a342d" },
    fontFamily: { sans: ["Arial", "Helvetica", "sans-serif"], mono: ["ui-monospace", "SFMono-Regular", "monospace"] },
  } }, plugins: [],
} satisfies Config;
