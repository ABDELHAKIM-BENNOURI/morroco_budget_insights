# docker/react/Dockerfile — Image du service "dashboard" PLF 2026
#
# Base   : node:20-alpine (~ 130 MB)
# Rôle   : servir le dashboard Vite en mode dev sur :5173, après que
#          le pipeline Python ait produit data/models/*.json.
# Cache  : package.json copié seul → npm install caché tant que les
#          dépendances n'ont pas bougé.

FROM node:20-alpine

ENV NODE_ENV=development \
    CI=true

WORKDIR /app

# ── Outils minimum (coreutils → date GNU pour les timestamps) ────────────────
RUN apk add --no-cache coreutils

# ── Wait-and-start : orchestration au démarrage ──────────────────────────────
COPY docker/wait-and-start.sh /usr/local/bin/wait-and-start.sh
RUN chmod +x /usr/local/bin/wait-and-start.sh

# ── Dépendances NPM ──────────────────────────────────────────────────────────
COPY dashboard/package.json ./
RUN npm install

# ── Code source dashboard ────────────────────────────────────────────────────
# Le bind-mount Compose (./dashboard:/app) shadow ces fichiers au runtime,
# mais la copie reste utile pour la portabilité de l'image (CI, prod).
COPY dashboard/ ./

EXPOSE 5173

CMD ["/usr/local/bin/wait-and-start.sh"]
