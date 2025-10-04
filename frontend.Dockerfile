# Frontend Dockerfile
FROM node:18-alpine

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers package
COPY frontend/package*.json ./

# Installer les dépendances
RUN npm install

# Copier le code source du frontend
COPY frontend/ .

# Exposer le port
EXPOSE 3000

# Commande pour démarrer l'application
CMD ["npm", "start"]
