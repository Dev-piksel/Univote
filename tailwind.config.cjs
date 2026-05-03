module.exports = {
  darkMode: 'class', // Enable class-based dark mode
  content: [
    './src/**/*.{html,js,svelte,ts}',
    './src/**/*.svelte',
    './src/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Define primary brand colors, can be customized later
        brand: {
          DEFAULT: '#0b75fe',
          light: '#e5f0ff',
          dark: '#0a5ad4',
        },
      },
    },
  },
  plugins: [],
};
