# Stage 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:1.25-alpine
# Copy built assets from the build stage
COPY --from=build /app/dist /usr/share/nginx/html
# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf
# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
