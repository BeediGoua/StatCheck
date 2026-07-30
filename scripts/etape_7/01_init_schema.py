import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Setup paths
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/statcheck")
DEFAULT_DB_URL = "postgresql://postgres:postgrespassword@localhost:5432/postgres"

def main():
    print("=== 01_init_schema.py : Initialisation de la Base de Données E2E ===")
    
    # 1. Create database if not exists
    conn = None
    try:
        conn = psycopg2.connect(DEFAULT_DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'statcheck'")
        exists = cur.fetchone()
        if not exists:
            print("Création de la base de données 'statcheck'...")
            cur.execute("CREATE DATABASE statcheck")
        else:
            print("La base de données 'statcheck' existe déjà.")
        cur.close()
    except Exception as e:
        print(f"Erreur lors de la connexion initiale: {e}")
        return
    finally:
        if conn:
            conn.close()

    # 2. Execute the schema SQL
    schema_path = root_dir / "src" / "database" / "schema_retrieval.sql"
    if not schema_path.exists():
        print(f"Erreur: Fichier de schéma introuvable: {schema_path}")
        return
        
    print(f"Exécution du script SQL : {schema_path.name}...")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
            
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        print("Schéma initialisé avec succès !")
        
        # Validation extensions
        cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'unaccent');")
        extensions = [row[0] for row in cur.fetchall()]
        print(f"Extensions actives : {', '.join(extensions)}")
        
        # Validation unaccent config
        cur.execute("SELECT ts_lexize('french_stem', unaccent('chômage'));")
        res = cur.fetchone()[0]
        print(f"Test unaccent (chômage) -> {res}")
        
        cur.close()
    except Exception as e:
        print(f"Erreur lors de l'exécution du schéma: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
