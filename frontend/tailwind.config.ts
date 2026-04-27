import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: '#0d2538', deep: '#081827' },
        teal: { DEFAULT: '#5cd9c1' },
        accent: { DEFAULT: '#ffe066' },
        ink: '#e8e6e3',
        chalk: '#f4efe6',
        muted: '#7a8b9c',
      },
      fontFamily: {
        serif: ['"Source Serif Pro"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config;
