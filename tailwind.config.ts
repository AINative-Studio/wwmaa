import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "dojo-light": "var(--dojo-light)",
        "dojo-navy": "var(--dojo-navy)",
        "dojo-green": "var(--dojo-green)",
        "dojo-orange": "var(--dojo-orange)",
        "dojo-red": "var(--dojo-red)",
        bg: "var(--bg)",
        fg: "var(--fg)",
        card: "var(--card)",
        muted: "var(--muted)",
        border: "var(--border)",
        ring: "var(--ring)",
        primary: "var(--primary)",
        "primary-fg": "var(--primary-fg)",
        accent: "var(--accent)",
        success: "var(--success)",
        danger: "var(--danger)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
      },
      boxShadow: {
        card: "0 8px 28px rgba(2, 62, 114, 0.08)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Arial", "sans-serif"],
        display: ["Manrope", "Inter", "system-ui", "Arial", "sans-serif"],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
