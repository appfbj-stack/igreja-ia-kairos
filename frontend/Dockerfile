# syntax=docker/dockerfile:1.7
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Argumento de build: URL pública do backend (inlined no JS pelo Next)
# Default = produção (igreja.fbautomacao.space/api)
# Em dev, sobrescrever: --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000/api
ARG NEXT_PUBLIC_API_URL=https://igreja.fbautomacao.space/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_TELEMETRY_DISABLED=1

# Dependências
COPY package*.json ./
RUN npm ci

# Copia fonte e builda
COPY . .
RUN npm run build

# Runtime stage - imagem leve só com o necessário
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Usuário não-root
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Standalone output do Next.js
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
