import sqlite3
import os
import uuid
import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'secret_key_maroc_commerce'

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "commerce_maroc.db")
CSV_PATH = os.path.join(BASE_DIR, "piont de vente maroc.csv")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_from_csv():
    """Fonction intégrée pour réinitialiser la base à partir du CSV."""
    if not os.path.exists(CSV_PATH):
        return False, "Fichier CSV introuvable."
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Recréation des tables
    cursor.execute("DROP TABLE IF EXISTS points_commerce")
    cursor.execute("DROP TABLE IF EXISTS changelog")
    
    cursor.execute("""
        CREATE TABLE points_commerce (
            id TEXT PRIMARY KEY,
            zone TEXT,
            nom TEXT,
            categorie TEXT,
            type TEXT,
            latitude REAL,
            longitude REAL,
            statut TEXT DEFAULT 'actif',
            date_creation TEXT,
            date_modification TEXT,
            source TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            point_id TEXT, 
            type_evenement TEXT, 
            date_evenement TEXT,
            nom TEXT,
            zone TEXT,
            categorie TEXT
        )
    """)
    
    # Import CSV
    now = datetime.now().isoformat()
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            point_id = f"PDV-{uuid.uuid4().hex[:12].upper()}"
            batch.append((
                point_id, 
                (row.get("Zone") or "").strip(),
                (row.get("Nom") or "Sans nom").strip(),
                (row.get("Catégorie") or "Autre").strip(),
                (row.get("Type") or "Formel").strip(),
                float(row.get("Latitude") or 0),
                float(row.get("Longitude") or 0),
                'actif', now, now, 'import_csv'
            ))
            if len(batch) >= 5000:
                cursor.executemany("INSERT INTO points_commerce VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch)
                batch = []
        if batch:
            cursor.executemany("INSERT INTO points_commerce VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch)
    
    conn.commit()
    conn.close()
    return True, "Base de données réinitialisée avec succès."

@app.route('/')
def index():
    conn = get_db_connection()
    # On garde les 50 derniers pour les "Dernières Activités" (sidebar)
    recent_points = conn.execute('SELECT * FROM points_commerce ORDER BY date_modification DESC LIMIT 50').fetchall()
    # On récupère TOUS les points pour le tableau du bas
    all_points = conn.execute('SELECT * FROM points_commerce ORDER BY nom ASC').fetchall()
    stats = conn.execute('SELECT COUNT(*) as total, SUM(statut="actif") as actifs FROM points_commerce').fetchone()
    conn.close()
    return render_template('index.html', recent_points=recent_points, all_points=all_points, stats=stats)

@app.route('/api/points', methods=['GET', 'POST'])
def api_points():
    if request.method == 'POST':
        # Vérification de la clé de sécurité envoyée par l'autre ordinateur
        api_key = request.headers.get('X-API-KEY')
        if api_key != "geocommercial_2026_access_secure_key":
            return jsonify({"error": "Clé API invalide"}), 401
            
        data = request.json
        if not data:
            return jsonify({"error": "Données JSON manquantes"}), 400
            
        try:
            nom = data.get('nom')
            zone = data.get('zone')
            cat = data.get('categorie', 'Autre')
            ctype = data.get('type', 'Formel')
            lat = float(data.get('latitude', 0))
            lon = float(data.get('longitude', 0))
            source = data.get('source', 'api_externe')
            
            point_id = f"REM-{uuid.uuid4().hex[:8].upper()}"
            now = datetime.now().isoformat()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO points_commerce (id, zone, nom, categorie, type, latitude, longitude, statut, date_creation, date_modification, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'actif', ?, ?, ?)
            ''', (point_id, zone, nom, cat, ctype, lat, lon, now, now, source))
            
            # Important : Enregistrer dans le changelog pour la synchronisation
            cursor.execute("""
                INSERT INTO changelog (point_id, type_evenement, date_evenement, nom, zone, categorie) 
                VALUES (?, 'creation', ?, ?, ?, ?)
            """, (point_id, now, nom, zone, cat))
            
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "id": point_id}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Version GET existante
    conn = get_db_connection()
    points = conn.execute('SELECT * FROM points_commerce').fetchall()
    conn.close()
    return jsonify([dict(p) for p in points])

@app.route('/api/changes', methods=['GET'])
def api_changes():
    since = request.args.get('since', '1970-01-01T00:00:00')
    conn = get_db_connection()
    changes = conn.execute('SELECT * FROM changelog WHERE date_evenement > ? ORDER BY date_evenement', (since,)).fetchall()
    conn.close()
    return jsonify([dict(c) for c in changes])

@app.route('/add', methods=['POST'])
def add_point():
    try:
        zone = request.form['zone']
        nom = request.form['nom']
        categorie = request.form['categorie']
        type_commerce = request.form['type']
        lat = float(request.form['latitude'])
        lon = float(request.form['longitude'])
        
        point_id = f"MAN-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO points_commerce (id, zone, nom, categorie, type, latitude, longitude, statut, date_creation, date_modification, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'actif', ?, ?, 'manuel')
        ''', (point_id, zone, nom, categorie, type_commerce, lat, lon, now, now))
        
        cursor.execute("""
            INSERT INTO changelog (point_id, type_evenement, date_evenement, nom, zone, categorie) 
            VALUES (?, 'creation', ?, ?, ?, ?)
        """, (point_id, now, nom, zone, categorie))
        conn.commit()
        conn.close()
        flash(f'✅ Point "{nom}" ajouté avec succès !')
    except Exception as e:
        flash(f'❌ Erreur : {str(e)}')
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_point():
    try:
        method = request.form.get('method')
        target = request.form.get('target')
        now = datetime.now().isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Identifier le(s) point(s) pour le changelog avant suppression
        if method == 'id':
            query = "SELECT * FROM points_commerce WHERE id=?"
        else:
            query = "SELECT * FROM points_commerce WHERE nom=?"
            
        points_to_delete = cursor.execute(query, (target,)).fetchall()
        
        if not points_to_delete:
            flash("⚠️ Aucun point trouvé avec ces critères.")
            conn.close()
            return redirect(url_for('index'))

        # 2. Enregistrer la suppression dans le changelog
        for p in points_to_delete:
            cursor.execute("""
                INSERT INTO changelog (point_id, type_evenement, date_evenement, nom, zone, categorie)
                VALUES (?, 'suppression', ?, ?, ?, ?)
            """, (p['id'], now, p['nom'], p['zone'], p['categorie']))
            
        # 3. Suppression réelle (Hard Delete)
        if method == 'id':
            cursor.execute("DELETE FROM points_commerce WHERE id=?", (target,))
        elif method == 'nom':
            cursor.execute("DELETE FROM points_commerce WHERE nom=?", (target,))
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        flash(f"✅ Suppression réelle réussie ({count} point(s)).")
    except Exception as e:
        flash(f"❌ Erreur : {str(e)}")
    return redirect(url_for('index'))

@app.route('/api/ping', methods=['GET'])
def api_ping():
    """Endpoint léger pour tester la connectivité réseau."""
    return jsonify({
        "status": "ok", 
        "message": "Connexion établie !",
        "server_time": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 1. Initialisation si la base n'existe pas
    if not os.path.exists(DB_PATH):
        print("📦 Initialisation de la base de données...")
        init_db_from_csv()
    
    # 2. Migration automatique si nécessaire (ajout colonnes changelog)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # On vérifie si la table existe avant
        table_exists = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='changelog'").fetchone()
        if table_exists:
            cols = [row['name'] for row in cursor.execute("PRAGMA table_info(changelog)").fetchall()]
            if 'nom' not in cols:
                cursor.execute("ALTER TABLE changelog ADD COLUMN nom TEXT")
            if 'zone' not in cols:
                cursor.execute("ALTER TABLE changelog ADD COLUMN zone TEXT")
            if 'categorie' not in cols:
                cursor.execute("ALTER TABLE changelog ADD COLUMN categorie TEXT")
            conn.commit()
    except Exception as e:
        print(f"⚠️ Erreur migration : {e}")
    finally:
        conn.close()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
