# ── Frontend Dockerfile ─────────────────────────────────────────
# Two-stage build:
#   1. Node stage: install deps + build React SPA
#   2. Nginx stage: serve static files with SPA routing
# ────────────────────────────────────────────────────────────────

# ── Build stage ─────────────────────────────────────────────────
FROM node:20-slim AS build

WORKDIR /app

# Copy dependency manifests first for better layer caching
COPY package.json package-lock.json* ./
RUN npm ci --production=false

# Copy source and build
COPY . .

# Build arg so the API URL can be set at build time
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# ── Serve stage ─────────────────────────────────────────────────
FROM nginx:alpine AS serve

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our SPA-aware nginx config template (uses $PORT envsubst)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Also keep static nginx.conf for docker-compose (listens on 80)
COPY nginx.conf /etc/nginx/nginx-static.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Railway injects $PORT at runtime; default to 80 for docker-compose
ENV PORT=80

EXPOSE ${PORT}

# Use envsubst to replace $PORT in the nginx template at startup
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
