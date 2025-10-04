# Makefile pour MobilityDataFusion

.PHONY: help build up down logs clean dev-backend dev-frontend

# Aide
help:
	@echo "🐳 MobilityDataFusion - Commandes Docker"
	@echo ""
	@echo "Commandes disponibles:"
	@echo "  make build     - Construire les images Docker"
	@echo "  make up        - Démarrer les services"
	@echo "  make down      - Arrêter les services"
	@echo "  make logs      - Voir les logs"
	@echo "  make clean     - Nettoyer les images et volumes"
	@echo "  make dev-backend  - Démarrer le backend en mode dev"
	@echo "  make dev-frontend - Démarrer le frontend en mode dev"
	@echo ""

# Docker commands
build:
	docker-compose build

up:
	docker-compose up

up-detached:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Nettoyage
clean:
	docker-compose down
	docker system prune -f
	docker-compose build --no-cache

# Mode développement (sans Docker)
dev-backend:
	cd src && python3 app.py

dev-frontend:
	cd frontend && npm start

# Installation des dépendances
install-backend:
	pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# Setup complet
setup: install-backend install-frontend
	@echo "✅ Dépendances installées !"
	@echo "Pour démarrer avec Docker: make up"
	@echo "Pour démarrer en mode dev: make dev-backend (terminal 1) et make dev-frontend (terminal 2)"
