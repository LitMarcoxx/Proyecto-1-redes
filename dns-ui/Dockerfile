FROM node:20-alpine AS build

WORKDIR /app

# Allow passing the API URL at build time so the static build points to the API service
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

COPY package*.json ./
RUN npm install
COPY . .
# Ensure the Vite build picks up VITE_API_URL from the environment
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]