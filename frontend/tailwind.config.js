/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        tech: ['Share Tech Mono', 'monospace'],
        inter: ['Inter', 'sans-serif'],
      },
      colors: {
        jarvis: {
          bg: '#050d1a',
          cyan: '#00d4ff',
          orange: '#ff6b00',
          green: '#00ff9d',
          purple: '#7b2ff7',
          card: '#0a1628',
          border: 'rgba(0, 212, 255, 0.15)',
        },
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'spin-slow': 'spin 8s linear infinite',
        'spin-reverse': 'spin 6s linear infinite reverse',
        'scanline': 'scanline 8s linear infinite',
        'fade-in': 'fadeIn 0.3s ease',
        'slide-up': 'slideUp 0.3s ease',
      },
    },
  },
  plugins: [],
}
