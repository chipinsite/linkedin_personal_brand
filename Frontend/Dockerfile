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

# Copy our SPA-aware nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Railway injects $PORT; nginx listens on 80 by default.
# We use envsubst to dynamically set the port at runtime.
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
