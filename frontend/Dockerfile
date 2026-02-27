# ---- Build stage ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# VITE_API_URL is the public URL of your deployed backend service on Render
# Pass it at build time: --build-arg VITE_API_URL=https://your-backend.onrender.com
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---- Serve stage ----
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config to handle React Router (client-side routing)
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    # Forward /api calls to the backend (only useful if using a reverse proxy)\n\
    # For Render, set VITE_API_URL at build time instead.\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
