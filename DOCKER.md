# 🐳 Docker Setup pour MobilityDataFusion

## Démarrage rapide

### Commandes manuelles
```bash
# Construire les images
docker-compose build

# Démarrer les services
docker-compose up

# Démarrer en arrière-plan
docker-compose up -d
```

## Services

### Backend (Port 5000)
- **URL** : http://localhost:5000
- **Image** : `mobilitydatafusion_backend`
- **Dockerfile** : `backend.Dockerfile`

### Frontend (Port 3000)
- **URL** : http://localhost:3000
- **Image** : `mobilitydatafusion_frontend`
- **Dockerfile** : `frontend.Dockerfile`

## Commandes utiles

### Gestion des services
```bash
# Voir les logs
docker-compose logs

# Voir les logs d'un service spécifique
docker-compose logs backend
docker-compose logs frontend

# Arrêter les services
docker-compose down

# Redémarrer un service
docker-compose restart backend
docker-compose restart frontend

# Reconstruire et redémarrer
docker-compose up --build
```

### Debugging
```bash
# Accéder au shell du backend
docker-compose exec backend bash

# Accéder au shell du frontend
docker-compose exec frontend sh

# Voir les processus en cours
docker-compose ps
```

## Volumes

Les données sont persistées via des volumes Docker :
- `./src/data` → `/app/src/data` (données d'entrée et de sortie)
- `./cache` → `/app/cache` (cache de l'application)

## Prérequis

- Docker
- Docker Compose
- Ports 3000 et 5000 disponibles

## Dépannage

### Port déjà utilisé
```bash
# Vérifier quels processus utilisent les ports
lsof -i :3000
lsof -i :5000

# Arrêter les services Docker
docker-compose down
```

### Problème de permissions
```bash
# Donner les permissions au script
chmod +x start.sh
```

### Rebuild complet
```bash
# Supprimer les images et reconstruire
docker-compose down
docker system prune -f
docker-compose build --no-cache
docker-compose up
```
