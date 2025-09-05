FROM node:18-alpine

WORKDIR /app


# Instalar dependencias
RUN yarn install

# Copiar el resto del código
COPY . .

# Exponer el puerto usado por yarn dev (por defecto 5173 en Vite)
EXPOSE 5173

# Comando para desarrollo
CMD ["yarn", "run", "dev", "--host"]
