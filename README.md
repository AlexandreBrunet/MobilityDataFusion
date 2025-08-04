# Data Fusion

## Description

**Data Fusion** est une application React permettant de configurer, visualiser et analyser des données géospatiales via une interface utilisateur intuitive.

Elle propose :  
- L’exploration de fichiers de données spatiales  
- La configuration dynamique de couches tampon (buffers) spatiaux (circular, grid, isochrone, network...)  
- La gestion dynamique de filtres personnalisés sur fichiers  
- La génération et l’affichage interactif de tables, cartes, histogrammes et bar charts  
- La communication avec un backend Flask pour traitement des données et génération des visualisations


## Fonctionnalités principales

- Chargement et visualisation des fichiers de données  
- Formulaire dynamique avec adaptation selon type de buffer spatial  
- Ajout/suppression dynamique de filtres sur les données  
- Soumission des configurations au backend via API REST  
- Affichage des résultats (tableaux, cartes, graphiques) dans des iframes intégrées  
- Interface multi-onglets pour basculer entre explorateur, formulaire, tables, cartes, histogrammes et bar charts

---


## Installation
```bash
git clone <repo-url>
```

### Prérequis
- Node.js v23.3.0
- Python 3.9

### Installer et lancer le frontend
```bash
cd frontend
npm install
npm start
```
### Installer et lancer le backend
```bash
pip3 install -r requirements.txt
cd src
python3 app.py
```

L’application React sera accessible sur http://localhost:3000