# docker/python/Dockerfile — Image du service "pipeline" PLF 2026
#
# Base   : python:3.11-slim (~ 130 MB)
# Rôle   : exécuter le pipeline 02 → 05 puis sortir avec code 0.
# Cache  : requirements.txt copié séparément pour bénéficier du cache de couche
#          tant que la liste des dépendances n'évolue pas.

FROM python:3.11-slim

# ── Configuration runtime Python ──────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=UTC

WORKDIR /app

# ── Outils minimum (procps utile pour `ps` côté debug) ────────────────────────
RUN apt-get update \
 && apt-get install -y --no-install-recommends procps \
 && rm -rf /var/lib/apt/lists/*

# ── Dépendances Python ────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Entrypoint : pipeline orchestré ───────────────────────────────────────────
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# ── Code source du pipeline ───────────────────────────────────────────────────
# Les volumes Compose (data/raw, data/clean, data/models) shadow ces COPY
# au runtime — la copie sert uniquement à la portabilité de l'image.
COPY scripts/ ./scripts/
COPY data/    ./data/

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
