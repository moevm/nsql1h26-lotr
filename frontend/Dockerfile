FROM node:22.18.0-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY openapi.yml ./
COPY orval.config.ts ./
COPY src ./src

RUN npm run generate

COPY . .

RUN npm run build

FROM nginx:1.28.0-alpine3.21 AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]