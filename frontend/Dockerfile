# Multi-stage build producing a small standalone Next.js server.
#   docker build -t web .
#   docker build --build-arg NEXT_PUBLIC_APP_ENV=staging --build-arg NEXT_PUBLIC_API_URL=... --build-arg NEXT_PUBLIC_SITE_URL=... --build-arg NEXT_PUBLIC_APP_URL=... -t web:staging .
#   docker run -p 3000:3000 -e SESSION_SECRET=... web

FROM node:22-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* are inlined at build time. Args override .env.production only when non-empty.
ARG NEXT_PUBLIC_APP_ENV
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SITE_URL
ARG NEXT_PUBLIC_APP_URL
ENV BUILD_STANDALONE=true
RUN env ${NEXT_PUBLIC_APP_ENV:+NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV} \
        ${NEXT_PUBLIC_API_URL:+NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL} \
        ${NEXT_PUBLIC_SITE_URL:+NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL} \
        ${NEXT_PUBLIC_APP_URL:+NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL} \
        npm run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S app && adduser -S app -G app
COPY --from=build --chown=app:app /app/.next/standalone ./
COPY --from=build --chown=app:app /app/.next/static ./.next/static
COPY --from=build --chown=app:app /app/public ./public
USER app
EXPOSE 3000
# Secrets (SESSION_SECRET, ...) are injected at runtime, never baked into the image
CMD ["node", "server.js"]
