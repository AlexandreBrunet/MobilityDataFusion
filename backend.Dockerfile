# Backend Dockerfile
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires pour les bibliothèques géospatiales
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libspatialindex-dev \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip
RUN pip install --upgrade pip

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python avec gestion des erreurs
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ ./src/

# Exposer le port
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["python", "src/app.py"]
