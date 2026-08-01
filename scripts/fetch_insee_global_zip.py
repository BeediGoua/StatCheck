from __future__ import annotations
import hashlib
import zipfile
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser
import requests
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
LOGGER = logging.getLogger(__name__)

INSEE_BASE_URL = "https://www.insee.fr"
INSEE_INFO_URL = f"{INSEE_BASE_URL}/fr/information/2862759"
EXPECTED_HOSTNAME = "www.insee.fr"

class InseeLinkParser(HTMLParser):
    def __init__(self, pattern_filter: str):
        super().__init__()
        self.pattern_filter = pattern_filter
        self.found_links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    if self.pattern_filter in value and value.endswith(".zip"):
                        self.found_links.append(value)

def discover_zip_url(session: requests.Session, pattern: str) -> str:
    """Trouve dynamiquement la dernière URL du fichier ZIP sur la page de l'INSEE."""
    LOGGER.info(f"Recherche de l'URL pour '{pattern}' sur {INSEE_INFO_URL}...")
    try:
        response = session.get(INSEE_INFO_URL, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        LOGGER.error("Le téléchargement a échoué par timeout. La cause exacte n’est pas établie.")
        raise
    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Impossible d'accéder à la page INSEE: {e}")
        raise
    
    parser = InseeLinkParser(pattern)
    parser.feed(response.text)
    
    if not parser.found_links:
        raise ValueError(f"Aucun lien correspondant à '{pattern}' trouvé sur la page.")

    # Trouver la version avec la date maximale
    # Les fichiers sont typiquement nommés YYYYMM_correspondance_idbank_dimension.zip
    max_date = -1
    best_link = ""
    for link in parser.found_links:
        filename = link.split("/")[-1]
        match = re.search(r'^(\d{6})_', filename)
        if match:
            date_val = int(match.group(1))
            if date_val > max_date:
                max_date = date_val
                best_link = link
                
    if not best_link:
        # Fallback au premier lien trouvé si on ne peut pas extraire de date
        best_link = parser.found_links[0]
        
    full_url = urljoin(INSEE_BASE_URL, best_link)
    
    # Validation du lien découvert
    parsed_url = urlparse(full_url)
    if parsed_url.scheme != "https":
        raise ValueError(f"L'URL découverte n'est pas sécurisée (HTTPS requis): {full_url}")
    if parsed_url.hostname != EXPECTED_HOSTNAME:
        raise ValueError(f"L'URL pointe vers un domaine inattendu ({parsed_url.hostname}): {full_url}")
        
    LOGGER.info(f"URL la plus récente trouvée : {full_url}")
    return full_url

def download_file(session: requests.Session, url: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".part")
    sha256 = hashlib.sha256()

    LOGGER.info(f"Téléchargement de {url} vers {destination}...")
    try:
        with session.get(url, stream=True, timeout=(15, 300)) as response:
            response.raise_for_status()
            with temporary_path.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    output.write(chunk)
                    sha256.update(chunk)
    except requests.exceptions.Timeout:
        LOGGER.error("Le téléchargement du ZIP a échoué par timeout. La cause exacte n’est pas établie.")
        if temporary_path.exists():
            temporary_path.unlink()
        raise
        
    temporary_path.replace(destination)
    return sha256.hexdigest()

def validate_zip(zip_path: Path):
    if not zip_path.exists():
        raise FileNotFoundError(f"Le fichier {zip_path} n'existe pas.")
    
    size_bytes = zip_path.stat().st_size
    if size_bytes == 0:
        raise ValueError(f"Le fichier ZIP est vide: {zip_path}")
    if size_bytes > 5 * 1024 * 1024 * 1024: # 5GB sanity limit
        raise ValueError("Le fichier ZIP dépasse la limite de taille autorisée (5GB).")
        
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Le fichier téléchargé n'est pas un ZIP valide: {zip_path}")
        
    LOGGER.info(f"Validation réussie pour le fichier ZIP ({size_bytes / (1024*1024):.2f} MB).")

def extract_zip(zip_path: Path, output_directory: Path) -> list[Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    extracted_files: list[Path] = []
    
    LOGGER.info(f"Extraction de {zip_path} dans {output_directory}...")
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_name = Path(member.filename)
            if member_name.is_absolute() or ".." in member_name.parts:
                raise RuntimeError(f"Entrée ZIP non sûre détectée : {member.filename}")
            archive.extract(member, output_directory)
            extracted_files.append(output_directory / member.filename)
    return extracted_files

def main():
    target_dir = Path("data/raw/insee/global_zips")
    with requests.Session() as session:
        session.headers.update({"User-Agent": "StatCheck/0.1"})
        
        # 1. Correspondance idbank / dimension
        try:
            zip_url = discover_zip_url(session, "correspondance_idbank_dimension")
            zip_path = target_dir / "correspondance_idbank_dimension.zip"
            download_file(session, zip_url, zip_path)
            validate_zip(zip_path)
            extract_zip(zip_path, target_dir / "correspondance_idbank_dimension")
        except Exception as e:
            LOGGER.error(f"Erreur lors du traitement de la correspondance idbank: {e}")
            # Fallback controlé
            if zip_path.exists() and zipfile.is_zipfile(zip_path):
                LOGGER.info("Utilisation du dernier ZIP valide en cache (Fallback).")
            else:
                LOGGER.error("Aucun fallback possible.")
        
        # 2. Liste des variables / modalités
        try:
            var_url = discover_zip_url(session, "liste_variables_modalites")
            var_path = target_dir / "liste_variables_modalites.zip"
            download_file(session, var_url, var_path)
            validate_zip(var_path)
            extract_zip(var_path, target_dir / "liste_variables_modalites")
        except Exception as e:
            LOGGER.error(f"Erreur lors du traitement des variables/modalités: {e}")
            if var_path.exists() and zipfile.is_zipfile(var_path):
                LOGGER.info("Utilisation du dernier ZIP valide en cache (Fallback).")
            else:
                LOGGER.error("Aucun fallback possible.")

if __name__ == "__main__":
    main()
