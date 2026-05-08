#!/usr/bin/env bash
# entrypoint.sh — Pipeline de modélisation PLF 2026
#
# Exécute, dans l'ordre, les étapes 02 → 05 du pipeline Python :
#   02_clean.py    consolide les CSVs nettoyés
#   03_model.py    produit data/models/sankey_data.json + treemap_data.json
#   04_sankey.py   produit data/models/sankey_figure.json + .html
#   05_treemap.py  produit data/models/treemap_figure.json + .html
#
# En cas d'échec, remonte le code de sortie du script fautif.
# Au succès, écrit le flag data/models/.pipeline_done — signal attendu par
# le service `dashboard` (React) pour démarrer.
#
# Codes de sortie :
#   0 — succès
#   1 — script Python en échec (voir stderr ci-dessus)
#   2 — sortie attendue manquante après exécution

set -euo pipefail

cd /app

ts()  { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf "[%s][pipeline] %s\n" "$(ts)" "$*"; }

PIPELINE=(
  "scripts/02_clean.py"
  "scripts/03_model.py"
  "scripts/04_sankey.py"
  "scripts/05_treemap.py"
)

REQUIRED_OUTPUTS=(
  "data/models/sankey_data.json"
  "data/models/treemap_data.json"
  "data/models/sankey_figure.json"
  "data/models/treemap_figure.json"
)

DONE_FLAG="data/models/.pipeline_done"

# ── Préparation ───────────────────────────────────────────────────────────────
mkdir -p data/models data/clean
# Reset du flag : signale aux dépendants que le pipeline est en cours.
rm -f "$DONE_FLAG"

log "═══════════════════════════════════════════════════════════"
log "  PIPELINE PLF 2026 — démarrage"
log "═══════════════════════════════════════════════════════════"

# ── Exécution séquentielle ────────────────────────────────────────────────────
START_TOTAL=$(date +%s)
for script in "${PIPELINE[@]}"; do
  if [[ ! -f "$script" ]]; then
    log "❌ Script introuvable : $script"
    exit 1
  fi
  log "▸ Exécution : $script"
  start=$(date +%s)
  if ! python -u "$script"; then
    rc=$?
    log "❌ Échec de $script (code $rc)"
    log "   → consultez le stderr ci-dessus et corrigez avant de relancer."
    exit "$rc"
  fi
  elapsed=$(( $(date +%s) - start ))
  log "✓ $script terminé en ${elapsed}s"
  log "─────────────────────────────────────────────────────────"
done

# ── Vérification post-pipeline ────────────────────────────────────────────────
log "Vérification des sorties attendues…"
for f in "${REQUIRED_OUTPUTS[@]}"; do
  if [[ ! -f "$f" ]]; then
    log "❌ Sortie attendue manquante : $f"
    exit 2
  fi
  bytes=$(stat -c '%s' "$f")
  log "  ✓ $f (${bytes} octets)"
done

# ── Flag de complétion ────────────────────────────────────────────────────────
touch "$DONE_FLAG"
total=$(( $(date +%s) - START_TOTAL ))
log "═══════════════════════════════════════════════════════════"
log "✅ Pipeline complet en ${total}s — flag écrit : $DONE_FLAG"
log "   Le service dashboard peut démarrer."
log "═══════════════════════════════════════════════════════════"
