import xml.etree.ElementTree as ET
import logging
import json
import hashlib
from pathlib import Path
from src.db.database import SessionLocal
from src.models.structure import DataflowDimension, DataflowModality, AvailableSeriesKey
from src.models.ingestion import CatalogSnapshot
from sqlalchemy.dialects.postgresql import insert
import src.models.catalogue
import src.models.corpus
import src.models.nlp_runs
import src.models.sources
import src.models.series
import src.models.observation
import src.models.evaluation
import src.models.resolution_status
import src.models.retrieval_candidate
import src.models.sdmx_selection
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
LOGGER = logging.getLogger(__name__)

SDMX_NS = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
STR_NS = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
COM_NS = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"
GENERIC_NS = 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic'

NS = {
    'mes': SDMX_NS,
    'str': STR_NS,
    'com': COM_NS,
    'generic': GENERIC_NS
}

class IngestionQualityError(Exception):
    pass

class SnapshotImmutabilityError(Exception):
    pass

def calculate_sha256(directory_path: Path) -> str:
    """Calcule un hash sur l'ensemble des fichiers XML du snapshot pour garantir l'immuabilité."""
    sha256 = hashlib.sha256()
    for xml_file in sorted(directory_path.glob("*.xml")):
        with open(xml_file, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
    return sha256.hexdigest()

def parse_dsd(xml_path: Path, session, snapshot_id: str):
    dataflow_id = xml_path.stem
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    dimensions_inserted = 0
    modalities_inserted = 0
    
    # 1. Extraction des Codelists
    codelists = root.findall('.//str:Codelist', NS)
    for cl in codelists:
        cl_id = cl.attrib.get('id')
        codes = cl.findall('.//str:Code', NS)
        
        modality_rows = []
        for code_elem in codes:
            code_val = code_elem.attrib.get('id')
            label_fr = ""
            for name_elem in code_elem.findall('com:Name', NS):
                if name_elem.attrib.get('{http://www.w3.org/XML/1998/namespace}lang') == 'fr':
                    label_fr = name_elem.text
            if not label_fr:
                first_name = code_elem.find('com:Name', NS)
                label_fr = first_name.text if first_name is not None else code_val
                
            modality_rows.append({
                "id": uuid.uuid4(),
                "snapshot_id": snapshot_id,
                "dataflow_id": dataflow_id,
                "dimension_id": cl_id, 
                "code": code_val,
                "original_label": label_fr
            })
            
        if modality_rows:
            stmt = insert(DataflowModality).values(modality_rows)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["snapshot_id", "dataflow_id", "dimension_id", "code"]
            )
            res = session.execute(stmt)
            modalities_inserted += res.rowcount
            
    # 2. Extraction des Dimensions
    dsds = root.findall('.//str:DataStructure', NS)
    if dsds:
        dsd = dsds[0]
        dimension_list = dsd.find('.//str:DimensionList', NS)
        if dimension_list is not None:
            position = 1
            dimension_rows = []
            for dim_elem in dimension_list:
                role = "SERIES"
                if dim_elem.tag.endswith('TimeDimension'):
                    role = "TIME"
                elif dim_elem.tag.endswith('PrimaryMeasure'):
                    role = "MEASURE"
                    
                dim_id = dim_elem.attrib.get('id')
                enum = dim_elem.find('.//str:LocalRepresentation/str:Enumeration/Ref', NS)
                codelist_ref = enum.attrib.get('id') if enum is not None else None
                
                dimension_rows.append({
                    "id": uuid.uuid4(),
                    "snapshot_id": snapshot_id,
                    "dataflow_id": dataflow_id,
                    "dimension_id": dim_id,
                    "canonical_concept": dim_id,
                    "position": position,
                    "role": role,
                    "codelist": codelist_ref,
                    "is_mandatory": True
                })
                position += 1
                
            if dimension_rows:
                stmt = insert(DataflowDimension).values(dimension_rows)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["snapshot_id", "dataflow_id", "dimension_id"]
                )
                res = session.execute(stmt)
                dimensions_inserted += res.rowcount
                
    return dimensions_inserted, modalities_inserted

def parse_generic_series(xml_path: Path, session, snapshot_id: str, ordered_dimension_ids: list):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    dataflow_id = xml_path.stem.split('-nodata')[0]
    series_inserted = 0
    
    series_nodes = root.findall('.//generic:Series', NS)
    ask_rows = []
    
    for series_node in series_nodes:
        dimensions = {}
        attributes = {}
        
        series_key = series_node.find('generic:SeriesKey', NS)
        if series_key is not None:
            for value_node in series_key.findall('generic:Value', NS):
                dim_id = value_node.get('id')
                dim_val = value_node.get('value')
                if dim_id and dim_val:
                    dimensions[dim_id] = dim_val
                    
        attributes_node = series_node.find('generic:Attributes', NS)
        if attributes_node is not None:
            for value_node in attributes_node.findall('generic:Value', NS):
                attr_id = value_node.get('id')
                attr_val = value_node.get('value')
                if attr_id and attr_val:
                    attributes[attr_id] = attr_val
                    
        idbank = attributes.get('IDBANK') or attributes.get('ID_BANK') or attributes.get('SERIES_ID')
        
        ordered_key = '.'.join(dimensions[d_id] for d_id in ordered_dimension_ids if d_id in dimensions)
        canonical_dimensions = json.dumps(dimensions, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        
        series_key_hash = hashlib.sha256(f"{snapshot_id}|{dataflow_id}|{ordered_key}|{canonical_dimensions}".encode('utf-8')).hexdigest()
        
        ask_rows.append({
            "id": uuid.uuid4(),
            "snapshot_id": snapshot_id,
            "dataflow_id": dataflow_id,
            "ordered_key": ordered_key,
            "key_hash": series_key_hash,
            "dimensions_json": dimensions,
            "idbank": idbank,
            "availability_source": 'SDMX_NODATA'
        })
        
    if ask_rows:
        stmt = insert(AvailableSeriesKey).values(ask_rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["snapshot_id", "dataflow_id", "ordered_key"]
        )
        res = session.execute(stmt)
        series_inserted += res.rowcount
        
    return series_inserted

def run_ingestion():
    snapshot_dir = sorted(Path("data/raw/insee").glob("snapshot_*"))
    if not snapshot_dir:
        LOGGER.error("Aucun snapshot trouvé.")
        return
    latest_snapshot = snapshot_dir[-1]
    snapshot_id = latest_snapshot.name
    
    # 1. Calcul du Hash de source (Validation Immuabilité)
    source_sha256 = calculate_sha256(latest_snapshot)
    
    LOGGER.info(f"Début de l'ingestion pour le snapshot: {snapshot_id} (SHA: {source_sha256[:8]})")
    
    with SessionLocal() as db_session:
        # Vérification de l'état du snapshot
        snapshot = db_session.query(CatalogSnapshot).filter_by(id=snapshot_id).first()
        if snapshot and snapshot.status == "READY":
            if snapshot.source_sha256 == source_sha256:
                LOGGER.info("SKIPPED_ALREADY_INGESTED: Snapshot identique déjà présent.")
                return
            else:
                raise SnapshotImmutabilityError("Le snapshot existe avec une source différente. Créez un nouvel identifiant de snapshot.")
                
        if not snapshot:
            snapshot = CatalogSnapshot(id=snapshot_id, status="BUILDING", source_sha256=source_sha256)
            db_session.add(snapshot)
            db_session.commit()
            
        try:
            # Ouverture d'une transaction atomique pour l'ingestion
            with db_session.begin():
                total_dims, total_mods, total_series = 0, 0, 0
                
                # Ingestion des DSD
                for xml_file in latest_snapshot.glob("*.xml"):
                    if "-nodata" not in xml_file.name:
                        d, m = parse_dsd(xml_file, db_session, snapshot_id)
                        total_dims += d
                        total_mods += m
                        
                # Ingestion des séries disponibles (Mock)
                ordered_dimension_ids = ['FREQ', 'NATURE']
                for xml_file in latest_snapshot.glob("*-nodata.xml"):
                    s = parse_generic_series(xml_file, db_session, snapshot_id, ordered_dimension_ids)
                    total_series += s
                    
                # Contrôles de Qualité
                if total_dims == 0 and total_series == 0:
                    raise IngestionQualityError("Le snapshot est vide (0 dimensions, 0 séries).")
                    
                LOGGER.info(f"Ingestion terminée: {total_dims} dimensions, {total_mods} modalités, {total_series} séries.")
                
                # Si succès, on passe à READY
                snapshot.status = "READY"
                db_session.add(snapshot)
                
                # Génération du Rapport d'Audit
                report = {
                    "snapshot_id": snapshot_id,
                    "source_sha256": source_sha256,
                    "status": "READY",
                    "metrics": {
                        "dimensions_inserted": total_dims,
                        "modalities_inserted": total_mods,
                        "series_keys_inserted": total_series
                    }
                }
                report_path = latest_snapshot / "audit_report.json"
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=4, ensure_ascii=False)
                LOGGER.info(f"Rapport d'audit généré dans {report_path}")
                
        except Exception as e:
            LOGGER.error(f"Échec de l'ingestion: {e}")
            snapshot.status = "FAILED"
            db_session.add(snapshot)
            db_session.commit()
            raise

if __name__ == "__main__":
    run_ingestion()
