import requests
import time
import json
from datetime import datetime

# --- CONFIGURATION ---
# URL ngrok publique du serveur distant (valable tant que ngrok tourne)
API_URL = "https://cesar-nonapportionable-seelily.ngrok-free.dev/api/changes"

# Fichier pour mémoriser la date de dernière interrogation
LAST_SYNC_FILE = "last_sync.txt"

def get_last_sync():
    try:
        with open(LAST_SYNC_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Si première fois, on prend les changements des 5 dernières minutes
        return datetime.now().isoformat()

def save_last_sync(timestamp):
    with open(LAST_SYNC_FILE, "w") as f:
        f.write(timestamp)

def check_for_updates():
    since = get_last_sync()
    print(f"🔍 Interrogation de l'API (depuis {since})...")
    
    try:
        response = requests.get(API_URL, params={"since": since}, timeout=10)
        response.raise_for_status()
        changes = response.json()
        
        if not changes:
            print("  ✅ Aucun nouveau changement.")
            return

        print(f"  🔔 {len(changes)} changement(s) détecté(s) !")
        
        for change in changes:
            etype = change['type_evenement']
            nom = change.get('nom') or "Inconnu"
            zone = change.get('zone') or "Inconnu"
            
            if etype == 'creation':
                print(f"    ✨ NOUVEAU : [{nom}] à {zone} (Cat: {change.get('categorie')})")
            elif etype == 'modification':
                print(f"    ✏️  MODIF : [{nom}] - Champ {change.get('champ_modifie')} changé")
            elif etype == 'desactivation' or etype == 'suppression':
                print(f"    ❌ SUPPRIMÉ/INACTIF : [{nom}] à {zone} (ID: {change['point_id']})")
            elif etype == 'reactivation':
                print(f"    ♻️  RÉOUVERT : [{nom}] à {zone}")

        # Mettre à jour le timestamp avec la date du dernier événement reçu
        last_event_time = changes[-1]['date_evenement']
        save_last_sync(last_event_time)
        
    except requests.exceptions.ConnectionError:
        print("  ❌ Erreur: Impossible de contacter le serveur. Vérifiez l'IP et que app.py tourne.")
    except Exception as e:
        print(f"  ❌ Une erreur est survenue : {e}")

if __name__ == "__main__":
    print(f"🚀 Client API démarré - Connexion à {API_URL}")
    print("Ce script simule votre deuxième application qui reçoit les mises à jour.\n")
    
    try:
        while True:
            check_for_updates()
            print(f"\n⏳ Attente de 10 secondes avant la prochaine vérification...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du client.")
