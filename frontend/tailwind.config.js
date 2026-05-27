/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bull: '#dc2626',  // 漲 (台股紅)
        bear: '#16a34a',  // 跌 (台股綠)
      },
      fontFamily: {
        sans: ['"Noto Sans TC"', '"Microsoft JhengHei"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
