# Frontend Dockerfile
FROM node:18-alpine

# Directorio de trabajo
WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install

# Copiar el resto del código
COPY . .



# Exponer puerto Vite
EXPOSE 5173

# Comando para desarrollo
CMD ["yarn", "run", "dev", "--host"]
