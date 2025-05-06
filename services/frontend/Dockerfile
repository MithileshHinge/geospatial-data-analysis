FROM node:20-slim AS build
# Set environment variables to ensure non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive \
    NODE_ENV=production \
    CI=true

WORKDIR /app
COPY . .
RUN npm i -g pnpm --no-progress && pnpm i --frozen-lockfile && pnpm run build

FROM nginx:1.25-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5174
CMD ["nginx", "-g", "daemon off;"]