FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/console/package.json apps/console/package-lock.json* ./
RUN npm install

COPY apps/console ./
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder --chown=node:node /app/package.json ./package.json
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./apps/console/.next/static

EXPOSE 3000

USER node

CMD ["node", "apps/console/server.js"]
