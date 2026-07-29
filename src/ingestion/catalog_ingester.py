import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from src.models.sources import Source
from src.models.catalogue import Dataset
from src.models.ingestion import IngestionRun, ResourceVersion

# Constantes SDMX
BASE_URL = "https://bdm.insee.fr/series/sdmx"
AGENCY = "FR1"
VERSION = "1.0"
NAMESPACES = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
RAW_DIR = Path("data/raw")

def preferred_name(element: ET.Element) -> str:
    """Retourne le nom français, ou le premier nom disponible."""
    names = element.findall("common:Name", NAMESPACES)
    for name in names:
        if name.get(XML_LANG) == "fr":
            return (name.text or "").strip()
    return (names[0].text or "").strip() if names else ""

class CatalogIngester:
    def __init__(self, db: Session):
        self.db = db
        # Assurer que la source existe
        self.source = self.db.query(Source).filter_by(code="INSEE_BDM").first()
        if not self.source:
            self.source = Source(code="INSEE_BDM", name="INSEE BDM (Séries Chronologiques)", source_type="API_SDMX", base_url=BASE_URL)
            self.db.add(self.source)
            self.db.commit()

    def run(self):
        # 1. Création du Run
        run = IngestionRun(
            source_id=self.source.id,
            ingestion_type="CATALOG",
            trigger_type="MANUAL",
            status="RUNNING"
        )
        self.db.add(run)
        self.db.commit()

        try:
            # 2. Téléchargement
            url = f"{BASE_URL}/dataflow/{AGENCY}/all/{VERSION}?references=none"
            response = requests.get(url, headers={"Accept": "application/vnd.sdmx.structure+xml"}, timeout=60)
            response.raise_for_status()

            raw_content = response.content
            run.download_size_bytes = len(raw_content)

            # 3. Preuve et Hachage
            raw_hash = hashlib.sha256(raw_content).hexdigest()
            
            # Vérifier si on a déjà ingéré cette version exacte
            last_version = self.db.query(ResourceVersion).filter_by(
                source_id=self.source.id,
                resource_type="CATALOG",
                external_id="ALL_DATAFLOWS"
            ).order_by(ResourceVersion.retrieved_at.desc()).first()

            if last_version and last_version.raw_hash == raw_hash:
                run.status = "SUCCESS"
                run.summary_message = "Idempotence : Le catalogue n'a pas changé."
                run.ended_at = datetime.utcnow()
                self.db.commit()
                return run

            # Sauvegarder le fichier brut
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            raw_filepath = RAW_DIR / f"insee_bdm_catalog_{timestamp_str}.xml"
            raw_filepath.write_bytes(raw_content)

            # Enregistrer la nouvelle version
            new_version = ResourceVersion(
                source_id=self.source.id,
                resource_type="CATALOG",
                external_id="ALL_DATAFLOWS",
                raw_hash=raw_hash,
                raw_file_path=str(raw_filepath),
                file_size_bytes=len(raw_content),
                mime_type="application/vnd.sdmx.structure+xml",
                run_id=run.id
            )
            self.db.add(new_version)
            self.db.commit()

            # 4. Analyse (Parsing)
            root = ET.fromstring(raw_content)
            dataflows = root.findall(".//structure:Dataflow", NAMESPACES)
            run.items_discovered = len(dataflows)

            # 5. Synchronisation Base de Données
            created = 0
            updated = 0
            unchanged = 0

            # Optimisation: Récupérer tous les datasets existants en mémoire
            existing_datasets = {
                d.external_id: d for d in self.db.query(Dataset).filter_by(source_id=self.source.id, external_type="dataflow").all()
            }

            for flow in dataflows:
                external_id = flow.get("id", "")
                title = preferred_name(flow)

                if external_id in existing_datasets:
                    ds = existing_datasets[external_id]
                    if ds.title_fr != title:
                        ds.title_fr = title
                        ds.last_remote_update = datetime.utcnow()
                        updated += 1
                    else:
                        unchanged += 1
                    ds.last_seen_at = datetime.utcnow()
                else:
                    new_ds = Dataset(
                        source_id=self.source.id,
                        external_id=external_id,
                        external_type="dataflow",
                        title_fr=title
                    )
                    self.db.add(new_ds)
                    created += 1

            self.db.commit()

            # 6. Clôture
            run.items_created = created
            run.items_updated = updated
            run.items_unchanged = unchanged
            run.status = "SUCCESS"
            run.summary_message = "Ingestion terminée avec succès."
            run.ended_at = datetime.utcnow()
            self.db.commit()
            
            return run

        except Exception as e:
            run.status = "FAILED"
            run.summary_message = str(e)
            run.ended_at = datetime.utcnow()
            self.db.commit()
            raise
