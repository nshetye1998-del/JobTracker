FROM node:18-alpine as build

WORKDIR /app

COPY services/dashboard-ui/package*.json ./
RUN npm install

COPY services/dashboard-ui .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY services/dashboard-ui/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
