#!/usr/bin/env node
/**
 * copy-data.mjs — Hook prebuild/predev.
 *
 * Copie les figures Plotly produites par le pipeline Python
 *   data/models/*.json   →   dashboard/public/data/*.json
 *
 * La cible (public/data/) est servie par Vite à l'URL /data/...
 *
 * Le script tente plusieurs chemins-source :
 *   1. ../../data/models      → contexte hôte (cwd = dashboard/)
 *   2. /data/models           → contexte conteneur (volume monté)
 *
 * En cas d'absence des sources, le script journalise un avertissement
 * et termine en code 0 — il ne casse pas un build CI où les JSON ne
 * sont pas présents (ils sont .gitignore).
 */

import {
  copyFileSync, existsSync, mkdirSync, readdirSync, statSync,
} from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const CANDIDATES = [
  resolve(__dirname, '../../data/models'),
  '/data/models',
];

const DST = resolve(__dirname, '../public/data');

function findSource() {
  for (const c of CANDIDATES) {
    if (existsSync(c) && statSync(c).isDirectory()) {
      return c;
    }
  }
  return null;
}

function main() {
  const src = findSource();
  if (!src) {
    console.warn('⚠️  copy-data : aucune source data/models trouvée');
    console.warn('    chemins testés :');
    for (const c of CANDIDATES) console.warn(`      - ${c}`);
    console.warn('    → exécutez le pipeline Python (03_model + 04_sankey + 05_treemap)');
    console.warn('    → puis relancez `npm run dev` ou `npm run build`');
    return;
  }

  const files = readdirSync(src).filter((f) => f.endsWith('.json'));
  if (files.length === 0) {
    console.warn(`⚠️  copy-data : aucun *.json dans ${src}`);
    return;
  }

  mkdirSync(DST, { recursive: true });
  for (const f of files) {
    copyFileSync(join(src, f), join(DST, f));
    console.log(`  ✓ ${f}`);
  }
  console.log(`✅ ${files.length} fichier(s) copié(s) : ${src} → ${DST}`);
}

main();
