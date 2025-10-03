# Dockerfile.dev
FROM node:20-alpine

# Crear carpeta de la app
WORKDIR /app

# Copiar package.json y yarn.lock para instalar dependencias
COPY package.json yarn.lock ./

# Instalar dependencias dentro del contenedor
RUN yarn install

# Copiar todo el código
COPY . .

# Exponer el puerto de Vite
EXPOSE 5173

# Comando de desarrollo
CMD ["yarn", "dev", "--host"]
