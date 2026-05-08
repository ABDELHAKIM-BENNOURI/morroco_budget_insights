import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev server :
//   - host:true   → écoute sur 0.0.0.0 (nécessaire en conteneur Docker)
//   - usePolling  → fiabilise la détection de changements sur volumes montés
//                   (WSL2 / Docker Desktop)
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    watch: { usePolling: true, interval: 300 },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
  },
});
