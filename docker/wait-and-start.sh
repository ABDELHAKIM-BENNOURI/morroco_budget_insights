#!/bin/sh
# wait-and-start.sh — Démarrage du dashboard React (mode dev) après pipeline.
#
# Étapes :
#   1. Attend l'apparition du flag /data/models/.pipeline_done
#      (signal écrit par docker/entrypoint.sh côté Python).
#   2. Vérifie que les figures attendues existent.
#   3. Copie les JSONs de /data/models/ → /app/public/data/.
#   4. Lance `npm run dev` (Vite, hot reload, host 0.0.0.0:5173).
#
# Codes de sortie :
#   0   — succès (n'arrive jamais : exec npm run dev ne retourne pas)
#   1   — timeout en attente du flag pipeline
#   2   — fichier figure attendu manquant après réception du flag

set -eu

DONE_FLAG="/data/models/.pipeline_done"
SRC="/data/models"
DST="/app/public/data"

TIMEOUT_SEC=600     # 10 min max d'attente
INTERVAL_SEC=2

REQUIRED="sankey_data.json sankey_figure.json treemap_data.json treemap_figure.json"

ts()  { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf "[%s][dashboard] %s\n" "$(ts)" "$*"; }

log "═══════════════════════════════════════════════════════════"
log "  DASHBOARD PLF 2026 — démarrage"
log "═══════════════════════════════════════════════════════════"

# ── 1. Attente du flag pipeline ───────────────────────────────────────────────
if [ -f "$DONE_FLAG" ]; then
  log "✓ Flag pipeline déjà présent : $DONE_FLAG"
else
  log "Attente du pipeline Python (flag $DONE_FLAG)…"
  elapsed=0
  while [ ! -f "$DONE_FLAG" ]; do
    if [ "$elapsed" -ge "$TIMEOUT_SEC" ]; then
      log "❌ Timeout : pipeline non terminé après ${TIMEOUT_SEC}s"
      log "   → docker compose logs pipeline"
      exit 1
    fi
    sleep "$INTERVAL_SEC"
    elapsed=$((elapsed + INTERVAL_SEC))
    if [ $((elapsed % 30)) -eq 0 ]; then
      log "  … toujours en attente (${elapsed}s)"
    fi
  done
  log "✓ Flag détecté après ${elapsed}s"
fi

# ── 2. Vérification des fichiers attendus ─────────────────────────────────────
for f in $REQUIRED; do
  if [ ! -f "$SRC/$f" ]; then
    log "❌ Fichier attendu manquant : $SRC/$f"
    exit 2
  fi
done
log "✓ Toutes les figures sont présentes dans $SRC"

# ── 3. Copie /data/models/*.json → /app/public/data/ ──────────────────────────
mkdir -p "$DST"
log "Copie des JSONs $SRC/*.json → $DST/"
count=0
for f in "$SRC"/*.json; do
  cp "$f" "$DST/"
  log "  ✓ $(basename "$f")"
  count=$((count + 1))
done
log "✓ ${count} fichier(s) copié(s)"

# ── 4. Lancement du serveur Vite (mode dev, hot reload) ───────────────────────
log "Lancement de Vite en mode dev (http://localhost:5173)…"
log "═══════════════════════════════════════════════════════════"
exec npm run dev -- --host
