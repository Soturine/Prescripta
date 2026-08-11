# syntax=docker/dockerfile:1.11
FROM node:24.17.0-trixie-slim@sha256:9022946fb57e6fb6a2503931470deba4b49db02bfc8f587f93007fd33ef54415 AS build

ENV NPM_CONFIG_FETCH_RETRIES=4 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=10000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=60000

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
COPY scripts/check_install_scripts.mjs scripts/install-script-policy.json /tmp/prescripta-scripts/
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    npm install --global npm@11.18.0 \
    && node /tmp/prescripta-scripts/check_install_scripts.mjs /app/package-lock.json \
    && npm ci --prefer-offline --no-audit --no-fund

COPY frontend/index.html frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts ./
COPY frontend/src ./src

ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.30.4-alpine@sha256:97d490c12ba55b4946b01546d1c3ed324e8d41ab1c9fcb2a616aa470620e5b46

COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
  CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]

CMD ["nginx", "-g", "daemon off;"]
