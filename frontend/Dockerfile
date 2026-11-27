FROM node:22.22.0-bookworm-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install -g npm@11.21.3 \
    && npm ci

COPY . .

ARG VITE_API_URL=/api
ARG VITE_OIDC_AUTHORIZE_URL
ARG VITE_OIDC_CLIENT_ID
ARG VITE_OIDC_TOKEN_URL

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_OIDC_AUTHORIZE_URL=$VITE_OIDC_AUTHORIZE_URL
ENV VITE_OIDC_CLIENT_ID=$VITE_OIDC_CLIENT_ID
ENV VITE_OIDC_TOKEN_URL=$VITE_OIDC_TOKEN_URL

RUN npm run build

FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
