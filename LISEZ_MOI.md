# Système de Simulation et de Détection des Commerces au Maroc

Ce dossier contient un système complet pour simuler et surveiller l'évolution des points de commerce (formels et informels) au Maroc.

## Composants du Système

1.  **`commerce_maroc.db`** : La base de données SQLite persistante contenant l'état actuel de tous les points de vente, ainsi qu'un journal complet des modifications (`changelog`).

2.  **`db_init.py`** : Script d'initialisation.
    *   Lit le fichier `piont de vente maroc.csv`.
    *   Crée la base de données et importe les données initiales.
    *   Attribue des IDs uniques et des dates de création.

3.  **`simulateur.py`** : Simule le comportement d'une source externe (type OpenStreetMap).
    *   **Apparition** : Crée de nouveaux points dans des zones réalistes.
    *   **Modification** : Change les noms ou catégories de points existants.
    *   **Disparition** : Désactive (passe en `inactif`) des points.
    *   **Utilisation** : `python simulateur.py --mode continu --intervalle 30`

4.  **`detecteur_changements.py`** : Le script "externe" de surveillance.
    *   Interroge la base régulièrement.
    *   Compare l'état actuel avec la dernière interrogation.
    *   Génère des rapports détaillés dans le dossier `rapports/`.
    *   **Utilisation** : `python detecteur_changements.py --mode surveillance --intervalle 30`

## Comment faire une démonstration ?

1.  **Initialisation** : (Déjà fait) `python db_init.py`
2.  **Lancer la simulation** : Dans un terminal, lancez le simulateur en mode continu :
    ```bash
    python simulateur.py --mode continu --intervalle 10
    ```
3.  **Lancer la surveillance** : Dans un second terminal, lancez le détecteur :
    ```bash
    python detecteur_changements.py --mode surveillance --intervalle 10
    ```

Vous verrez alors le détecteur identifier automatiquement chaque modification apportée par le simulateur en temps réel.
