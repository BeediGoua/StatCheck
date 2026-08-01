from __future__ import annotations
import hashlib
import logging
import random
import time
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path
from typing import Final
import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
LOGGER = logging.getLogger(__name__)

SDMX_BASE_URL: Final = "https://bdm.insee.fr/series/sdmx"
SDMX_AGENCY: Final = "FR1"
SDMX_VERSION: Final = "1.0"

CONNECT_TIMEOUT_SECONDS: Final = 10
READ_TIMEOUT_SECONDS: Final = 90
MIN_DELAY_SECONDS: Final = 1.5
MAX_DELAY_SECONDS: Final = 4.0

class SdmxDownloadError(RuntimeError):
    pass

def build_sdmx_session() -> Session:
    retry_policy = Retry(
        total=6, connect=6, read=6, status=6, other=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_policy, pool_connections=4, pool_maxsize=4)
    session = requests.Session()
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "StatCheck/0.1 (public-statistics research)",
        "Accept": "application/vnd.sdmx.structure+xml;version=2.1, application/xml;q=0.9, text/xml;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return session

def build_datastructure_url(dsd_id: str) -> str:
    normalized_id = dsd_id.strip()
    return f"{SDMX_BASE_URL}/datastructure/{SDMX_AGENCY}/{normalized_id}/{SDMX_VERSION}"

def validate_sdmx_xml(response: Response) -> bytes:
    content = response.content
    if not content: raise SdmxDownloadError("Réponse vide")
    if "html" in response.headers.get("Content-Type", "").lower():
        raise SdmxDownloadError("HTML reçu au lieu de XML")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise SdmxDownloadError("XML invalide") from exc
    return content

def download_datastructure(session: Session, dsd_id: str) -> bytes:
    url = build_datastructure_url(dsd_id)
    LOGGER.info("Téléchargement DSD %s depuis %s", dsd_id, url)
    try:
        response = session.get(url, timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS))
    except RequestException as exc:
        raise SdmxDownloadError(f"Échec réseau définitif: {exc}") from exc
    if response.status_code != 200:
        raise SdmxDownloadError(f"Échec HTTP status={response.status_code}")
    return validate_sdmx_xml(response)

def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def polite_delay() -> None:
    delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    time.sleep(delay)

def create_snapshot():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/raw/insee/snapshot_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dsd_ids = ["CHOMAGE-TRIM-NATIONAL", "IPC-2015", "NAISSANCES-FECONDITE", "CREATIONS-ENTREPRISES"]
    manifest = {}

    with build_sdmx_session() as session:
        for index, dsd_id in enumerate(dsd_ids):
            destination = output_dir / f"{dsd_id}.xml"
            try:
                content = download_datastructure(session, dsd_id)
                destination.write_bytes(content)
                manifest[dsd_id] = {
                    "status": "DOWNLOADED",
                    "path": str(destination),
                    "sha256": sha256_bytes(content),
                }
            except Exception as exc:
                LOGGER.error("Erreur pour %s : %s", dsd_id, exc)
                manifest[dsd_id] = {"status": "FAILED", "error": str(exc)}
            finally:
                if index < len(dsd_ids) - 1:
                    polite_delay()

    # Sauvegarde du manifest global
    manifest_path = output_dir / "snapshot.json"
    manifest_path.write_text(json.dumps({
        "timestamp": timestamp,
        "results": manifest
    }, indent=2), encoding="utf-8")
    LOGGER.info("Snapshot généré dans %s", manifest_path)

if __name__ == "__main__":
    create_snapshot()
