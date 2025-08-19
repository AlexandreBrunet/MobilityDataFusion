# Mobility DataFusion

## Description
**Mobility DataFusion** est une application web interactive (React) conçue pour faciliter la **fusion, l’analyse et la visualisation de données géospatiales**.  
Elle permet aux utilisateurs de :

- Charger facilement des fichiers GeoJSON.  
- Configurer différents types de voisinages (buffers spatiaux, réseaux, etc.).  
- Appliquer des filtres et calculer des métriques personnalisées.  
- Explorer et comparer les résultats directement sur une carte interactive.  

L’objectif principal est de fournir un outil flexible et intuitif pour l’étude de la mobilité et de l’accessibilité urbaine, mais il peut être adapté à d’autres contextes nécessitant l’analyse spatiale.


Elle propose :  
- L’exploration de fichiers de données spatiales  
- La configuration dynamique de couches tampon (buffers) spatiaux (circular, grid, isochrone, network...)  
- La gestion dynamique de filtres personnalisés sur fichiers  
- La génération et l’affichage interactif de tables, cartes, histogrammes et bar charts  
- La communication avec un backend Flask pour traitement des données et génération des visualisations


## Fonctionnalités principales

- Chargement et visualisation des fichiers de données  
- Formulaire dynamique avec adaptation selon type de voisinage spatial  
- Ajout/suppression dynamique de filtres sur les données  
- Soumission des configurations au backend via API REST  
- Affichage des résultats (tableaux, cartes, graphiques)  
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

### Fichiers en entrées
Pour débuter avec l’outil, il est nécessaire de fournir des données géospatiales au format **GeoJSON**.  
Ces fichiers doivent être placés dans le dossier suivant du projet :
MobilityDataFusion/src/data/input/geojson. Par exemple : `bus_stop_and_lines.geojson`.

### Étapes à suivre

Une fois les fichiers nécessaires à l’analyse ajoutés dans le dossier `MobilityDataFusion/src/data/input/geojson`, ceux-ci apparaîtront dans l’interface sous la section **Data Files**.  
Les étapes suivantes permettent de générer le voisinage désiré et fusionner les ensembles de données sur l’objet et le voisinage de son choix :

#### 1) Buffer Layer Configuration
- **Layer Name** : Choisir sur quelle couche (fichier) générer le voisinage. Exemple : `bus_stop_and_lines`.  
- **Geometry type** : Indiquer le type de géométrie contenu dans le fichier (`Point`, `LineString`, `Polygon`, `MultiPolygon`).  
- **Buffer Type** : Sélectionner le type de voisinage à générer, puis remplir les paramètres associés (ex. distance, type de réseau, etc.).

#### 2) Add Filter
- Permet d’appliquer un filtre initial avant toute opération sur les fichiers en entrée.

#### 3) Calcul de métriques
- Section pour calculer des métriques après la fusion de données et au niveau des voisinages.  
- Possibilité d’effectuer des **sommes, moyennes, minimums, maximums, écarts-types, comptages et comptages distincts**.  
- Chaque métrique peut être nommée (ex. `stop_id` → `count_distinct_arret_bus`).  
- **Groupby_columns** : Définir les colonnes de regroupement (ex. `buffer_id`, `bus_stop_name`).  
- **Global filter** : Appliquer un filtre après agrégation.  
- **Post-Aggregation Metrics** : Calculer des ratios après agrégation (ex. `total_pers / area_km2`).

#### 4) Activate visualisation
- Activer pour visualiser les GeoJSON et les voisinages sur une carte, dans l’onglet **Map**.  
- ⚠️ Peut augmenter le temps de calcul.

#### 5) Join layers
- Définir la logique de jointure au niveau des voisinages :
  - **contains** : l’objet doit être entièrement contenu dans le voisinage pour être fusionné.  
  - **intersects** : tout objet croisant le voisinage est fusionné.  
- Par défaut :
  - **Points** → `contains`  
  - **Lignes et polygones** → `intersects`

#### 6) Colors
- Définir la couleur utilisée pour représenter les objets sur la carte (notation **RGB**).

#### 7) Submit
- Une fois la configuration terminée, cliquer sur **Submit** pour lancer les calculs.


### Fichers de sortie
Fichers GeoJSON permettant de visualiser les buffer:
src/data/output/data/buffers/

exemple de ficher: metro_station_buffer_circular_500m.geojson

Fichers fuisonnées en CSV
Contiennent les données de la couche de base enrichies des attributs des autres couches fusionnées.
src/data/output/data/fusion/
exemple de ficher: joined_data_stations_bixi_montreal_only_circular_300m.csv)
