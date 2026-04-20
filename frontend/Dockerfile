# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder
WORKDIR /build
COPY package*.json ./
RUN npm ci && npm prune --omit=dev

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /build/node_modules ./node_modules
COPY app.js config.js ./
COPY views ./views

RUN adduser -D -u 1001 appuser
USER appuser

EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "app.js"]
