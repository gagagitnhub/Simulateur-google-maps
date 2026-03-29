"""
poller.py - Script de consultation régulière de la base de données
Permet de détecter les changements (créations, modifications, désactivations,
réactivations) entre deux interrogations successives.  

Le script lit les événements stockés dans la table `changelog` et se rappelle
dernière date de consultation dans un fichier adjacent `.last_poll`.
Il peut être lancé en mode unique ou en boucle avec intervalle.

Usage :
    python poller.py            # vérifie une fois et sort
    python poller.py --continu  # boucle avec intervalle par défaut (10s)
    python poller.py --intervalle 60   # boucle toutes les 60s

Le fichier `.last_poll` crée à côté de la base de données contient un
ISO-timestamp correspondant à la dernière interrogation.  Cela permet à
un autre script (ou une application) de surveiller en continu la "source"
(simulée) et de réagir aux changements comme s'il s'agissait d'une API
externe.
"""

import sqlite3
import os
import sys
import time
import argparse
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commerce_maroc.db")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_poll")


def ensure_db_exists():
    if not os.path.exists(DB_FILE):
        print("❌ Base de données non trouvée. Exécutez d'abord db_init.py / simulateur.py")
        sys.exit(1)


def get_last_poll():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    # débuter très ancien pour tout récupérer lors de la première exécution
    return "1970-01-01T00:00:00"


def save_last_poll(timestamp: str):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(timestamp)


def fetch_changes(since: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM changelog WHERE date_evenement > ? ORDER BY date_evenement",
        (since,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def display_changes(rows):
    if not rows:
        return
    for r in rows:
        when = r["date_evenement"]
        typ = r["type_evenement"]
        pid = r["point_id"]
        champ = r["champ_modifie"] or ""
        old = r["ancienne_valeur"] or ""
        new = r["nouvelle_valeur"] or ""
        print(f"[{when}] {typ.upper():12s} point={pid} {champ} {old} -> {new}")


def run_once():
    last = get_last_poll()
    now = datetime.now().isoformat()
    changes = fetch_changes(last)
    if changes:
        print(f"\n🔔 Changements détectés depuis {last} :")
        display_changes(changes)
    else:
        print(f"\n⏳ Aucun changement depuis {last}.")
    save_last_poll(now)


def run_continu(interval: int):
    print(f"🔁 Mode continu activé (intervalle = {interval}s). CTRL+C pour arrêter")
    try:
        while True:
            run_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Surveillance interrompue par l'utilisateur")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poller de la base de données commerce_maroc")
    parser.add_argument("--continu", action="store_true",
                        help="boucle indéfiniment avec un intervalle donné")
    parser.add_argument("--intervalle", type=int, default=10,
                        help="intervalle en secondes (mode continu)")
    args = parser.parse_args()

    ensure_db_exists()
    if args.continu:
        run_continu(args.intervalle)
    else:
        run_once()
