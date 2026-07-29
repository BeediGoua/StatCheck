import json
import urllib.request
import csv
import os
import hashlib
from datetime import datetime

# Root dirs
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESOURCES_DIR = os.path.join(ROOT_DIR, "src", "parser", "baseline", "resources")
os.makedirs(RESOURCES_DIR, exist_ok=True)

def write_manifest(output_path, dataset_name, source, vintage, row_count, schema_version="1.0"):
    with open(output_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    manifest_path = output_path.replace(".csv", ".manifest.json")
    manifest = {
        "dataset": dataset_name,
        "publisher": "INSEE" if "insee" in source.lower() else "API Geo",
        "source_url": source,
        "vintage": vintage,
        "retrieved_at": datetime.utcnow().isoformat() + "Z",
        "sha256": file_hash,
        "row_count": row_count,
        "schema_version": schema_version,
        "generator_version": "2.0"
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifest écrit: {manifest_path}")

def generate_geo_api_current():
    print("Génération de geo_api_current.csv...")
    output_path = os.path.join(RESOURCES_DIR, "geo_api_current.csv")
    temp_path = output_path + ".tmp"
    
    rows = []
    # Régions
    req = urllib.request.urlopen("https://geo.api.gouv.fr/regions")
    for r in json.loads(req.read().decode('utf-8')):
        rows.append(["geo_api", "CURRENT", "REGION", str(r["code"]), r["nom"], ""])
        
    # Départements
    req = urllib.request.urlopen("https://geo.api.gouv.fr/departements")
    for d in json.loads(req.read().decode('utf-8')):
        rows.append(["geo_api", "CURRENT", "DEPARTEMENT", str(d["code"]), d["nom"], str(d.get("codeRegion", ""))])
        
    # Communes
    req = urllib.request.urlopen("https://geo.api.gouv.fr/communes")
    communes = json.loads(req.read().decode('utf-8'))
    for c in communes:
        rows.append(["geo_api", "CURRENT", "COMMUNE", str(c["code"]), c["nom"], str(c.get("codeDepartement", ""))])
        
    if len(communes) < 30000:
        raise ValueError(f"Erreur de validation: seulement {len(communes)} communes trouvées.")

    with open(temp_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code_system", "vintage", "territory_type", "code", "label", "parent_code"])
        writer.writerows(rows)
        
    os.replace(temp_path, output_path)
    write_manifest(output_path, "Géographie Courante", "https://geo.api.gouv.fr", "CURRENT", len(rows))


def generate_cog_2024():
    print("Génération de cog_2024.csv depuis l'archive Insee...")
    output_path = os.path.join(RESOURCES_DIR, "cog_2024.csv")
    temp_path = output_path + ".tmp"
    
    rows = []
    
    # Agrégats métier
    rows.append(["STATCHECK_INTERNAL", "2024", "TERRITORY_AGGREGATE", "FRANCE", "France", ""])
    rows.append(["STATCHECK_INTERNAL", "2024", "TERRITORY_AGGREGATE", "FRANCE_METRO", "France métropolitaine", "FRANCE"])
    
    # Régions
    url_reg = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_region_2024.csv"
    req_reg = urllib.request.urlopen(url_reg)
    reader = csv.DictReader(req_reg.read().decode('utf-8').splitlines())
    reg_count = 0
    for r in reader:
        rows.append(["INSEE_COG", "2024", "REGION", str(r["REG"]), r["LIBELLE"], ""])
        reg_count += 1
        
    # Départements
    url_dep = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_departement_2024.csv"
    req_dep = urllib.request.urlopen(url_dep)
    reader = csv.DictReader(req_dep.read().decode('utf-8').splitlines())
    dep_count = 0
    for d in reader:
        rows.append(["INSEE_COG", "2024", "DEPARTEMENT", str(d["DEP"]), d["LIBELLE"], str(d["REG"])])
        dep_count += 1
        
    # Communes
    url_com = "https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv"
    req_com = urllib.request.urlopen(url_com)
    reader = csv.DictReader(req_com.read().decode('utf-8').splitlines())
    com_count = 0
    for c in reader:
        ttype = c["TYPECOM"] if "TYPECOM" in c else "COMMUNE"
        rows.append(["INSEE_COG", "2024", ttype, str(c["COM"]), c["LIBELLE"], str(c.get("DEP", ""))])
        com_count += 1
        
    # Validation
    if reg_count == 0 or dep_count == 0 or com_count < 30000:
        raise ValueError(f"Erreur validation Insee: reg={reg_count}, dep={dep_count}, com={com_count}")

    with open(temp_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code_system", "vintage", "territory_type", "code", "label", "parent_code"])
        writer.writerows(rows)
        
    os.replace(temp_path, output_path)
    write_manifest(output_path, "Code Officiel Géographique", url_com, "2024", len(rows))

if __name__ == "__main__":
    generate_geo_api_current()
    generate_cog_2024()
    print("Mise à jour des référentiels terminée.")
