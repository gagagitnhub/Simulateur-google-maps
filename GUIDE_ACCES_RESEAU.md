# Guide d'utilisation et d'automatisation (V2 - Laragon & Réseau)

Ce système est configuré pour fonctionner de manière autonome et partagée sur votre réseau local.

## 📁 Installation sur Laragon
Puisque vous utilisez Laragon, le plus simple pour partager la base de données est de :
1. Copier ce dossier (`Base de données`) dans le dossier `C:\laragon\www\`.
2. Laragon créera automatiquement un hotlink (si configuré) ou vous pourrez y accéder via votre IP locale.

## 🚀 Comment lancer les composants ?

Vous avez besoin de 3 éléments pour que l'automatisation soit complète :

### 1. L'Interface Web (Ajout Manuel)
Dans un terminal, lancez le serveur Flask :
```bash
python app.py
```
*   **Accès local** : [http://localhost:5000](http://localhost:5000)
*   **Accès depuis un autre ordi** : `http://VOTRE_IP_LOCALE:5000` (Remplacez par l'IP de votre PC, ex: `192.168.1.15`)

### 2. Le Simulateur (Ajout Automatique)
Dans un autre terminal, lancez pour simuler le comportement d'OSM :
```bash
python simulateur.py --mode continu --intervalle 30
```

### 3. Le Détecteur (Surveillance)
Sur l'ordinateur où vous voulez vérifier que l'automatisation marche (celui-ci ou un autre ayant accès au dossier partagé) :
```bash
python detecteur_changements.py --mode surveillance --intervalle 10
```

---

## 💡 Pourquoi ça marche ?
*   **Base partagée** : Tous les scripts lisent et écrivent dans `commerce_maroc.db`.
*   **Changelog** : Quand vous ajoutez un point via l'interface web, le script écrit dans la table `changelog`.
*   **Détection temps réel** : Le script `detecteur_changements.py` surveille cette table. Dès qu'il voit une nouvelle entrée (manuelle ou simulée), il déclenche une alerte/rapport.

## 🖥️ Accès depuis un autre ordinateur
1. Assurez-vous que les deux ordinateurs sont sur le même Wi-Fi/Réseau.
2. Autorisez le port `5000` dans votre pare-feu Windows si nécessaire.
3. Tapez l'adresse IP de votre PC principal sur le second PC.
