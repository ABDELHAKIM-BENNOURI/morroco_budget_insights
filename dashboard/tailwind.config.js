/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink:     'var(--color-ink)',
        muted:   'var(--color-muted)',
        primary: 'var(--color-primary)',
        recette: 'var(--color-recette)',
        depense: 'var(--color-depense)',
        emprunt: 'var(--color-emprunt)',
        secteur: {
          social:       'var(--color-secteur-social)',
          souverainete: 'var(--color-secteur-souverainete)',
          economique:   'var(--color-secteur-economique)',
          infra:        'var(--color-secteur-infra)',
          autre:        'var(--color-secteur-autre)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Menlo', 'monospace'],
      },
      maxWidth: {
        prose: '70ch',
      },
    },
  },
  plugins: [],
};
