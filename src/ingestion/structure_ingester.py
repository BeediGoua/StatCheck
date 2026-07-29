import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from src.models.sources import Source
from src.models.catalogue import Dataset
from src.models.structure import Dimension, Modality, DatasetDimension, DatasetDimensionModality
from src.models.ingestion import IngestionRun, ResourceVersion, IngestionItem

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
    names = element.findall("common:Name", NAMESPACES)
    for name in names:
        if name.get(XML_LANG) == "fr":
            return (name.text or "").strip()
    return (names[0].text or "").strip() if names else ""

class StructureIngester:
    def __init__(self, db: Session):
        self.db = db
        self.source = self.db.query(Source).filter_by(code="INSEE_BDM").first()

    def run_for_dataset(self, dataset_external_id: str, run_id: str) -> dict:
        dataset = self.db.query(Dataset).filter_by(source_id=self.source.id, external_id=dataset_external_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_external_id} introuvable en base de donnees.")

        item = self.db.query(IngestionItem).filter_by(run_id=run_id, item_type="DATASTRUCTURE", external_id=dataset_external_id).first()
        if not item:
            item = IngestionItem(run_id=run_id, item_type="DATASTRUCTURE", external_id=dataset_external_id, status="RUNNING")
            self.db.add(item)
            self.db.commit()
        else:
            item.status = "RUNNING"
            self.db.commit()

        try:
            url = f"{BASE_URL}/datastructure/{AGENCY}/{dataset_external_id}/{VERSION}?references=children"
            response = requests.get(url, headers={"Accept": "application/vnd.sdmx.structure+xml"}, timeout=60)
            response.raise_for_status()

            raw_content = response.content

            raw_hash = hashlib.sha256(raw_content).hexdigest()
            last_version = self.db.query(ResourceVersion).filter_by(
                source_id=self.source.id,
                resource_type="DATASTRUCTURE",
                external_id=dataset_external_id
            ).order_by(ResourceVersion.retrieved_at.desc()).first()

            if last_version and last_version.raw_hash == raw_hash:
                item.status = "SUCCESS"
                item.error_message = "Idempotence : Structure inchangee."
                self.db.commit()
                return {"dataset": dataset_external_id, "status": "UNCHANGED", "dimensions": 0, "modalities": 0}

            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            raw_filepath = RAW_DIR / f"insee_bdm_structure_{dataset_external_id}_{timestamp_str}.xml"
            raw_filepath.write_bytes(raw_content)

            new_version = ResourceVersion(
                source_id=self.source.id,
                resource_type="DATASTRUCTURE",
                external_id=dataset_external_id,
                raw_hash=raw_hash,
                raw_file_path=str(raw_filepath),
                file_size_bytes=len(raw_content),
                mime_type="application/vnd.sdmx.structure+xml",
                run_id=run_id
            )
            self.db.add(new_version)
            self.db.commit()

            root = ET.fromstring(raw_content)
            
            # Dictionnaire Local: codelist_id -> list of (code, label_fr)
            codelists = {}
            for cl in root.findall(".//structure:Codelists/structure:Codelist", NAMESPACES):
                cl_id = cl.get("id")
                codes = []
                for code_el in cl.findall("structure:Code", NAMESPACES):
                    code_val = code_el.get("id")
                    label = preferred_name(code_el)
                    codes.append((code_val, label))
                codelists[cl_id] = codes

            dimensions_created = 0
            modalities_created = 0

            # Chercher DimensionList
            dim_list = root.find(".//structure:DimensionList", NAMESPACES)
            if dim_list is not None:
                for dim_el in dim_list:
                    dim_id = dim_el.get("id")
                    position = int(dim_el.get("position", "999"))
                    
                    cl_id = None
                    enum = dim_el.find(".//structure:Enumeration/*", NAMESPACES)
                    if enum is not None:
                        cl_id = enum.get("id")

                    dimension_obj = self.db.query(Dimension).filter_by(external_id=dim_id).first()
                    if not dimension_obj:
                        concept_ref = dim_el.find(".//structure:ConceptIdentity/*", NAMESPACES)
                        label_fr = dim_id
                        if concept_ref is not None:
                            label_fr = concept_ref.get("id", dim_id)
                        dimension_obj = Dimension(external_id=dim_id, label_fr=label_fr)
                        self.db.add(dimension_obj)
                        self.db.flush()
                        dimensions_created += 1

                    ds_dim = self.db.query(DatasetDimension).filter_by(dataset_id=dataset.id, dimension_id=dimension_obj.id).first()
                    if not ds_dim:
                        ds_dim = DatasetDimension(dataset_id=dataset.id, dimension_id=dimension_obj.id, position=position, external_codelist=cl_id)
                        self.db.add(ds_dim)
                        self.db.flush()
                    else:
                        ds_dim.position = position
                        ds_dim.external_codelist = cl_id

                    if cl_id and cl_id in codelists:
                        codes = codelists[cl_id]
                        for code_val, code_label in codes:
                            mod = self.db.query(Modality).filter_by(dimension_id=dimension_obj.id, code=code_val).first()
                            if not mod:
                                mod = Modality(dimension_id=dimension_obj.id, code=code_val, label_fr=code_label)
                                self.db.add(mod)
                                self.db.flush()
                                modalities_created += 1
                            else:
                                if mod.label_fr != code_label:
                                    mod.label_fr = code_label
                                if not mod.is_active:
                                    mod.is_active = True

                            ds_dim_mod = self.db.query(DatasetDimensionModality).filter_by(dataset_dimension_id=ds_dim.id, modality_id=mod.id).first()
                            if not ds_dim_mod:
                                ds_dim_mod = DatasetDimensionModality(dataset_dimension_id=ds_dim.id, modality_id=mod.id)
                                self.db.add(ds_dim_mod)

            self.db.commit()

            item.status = "SUCCESS"
            item.error_message = f"{dimensions_created} dims, {modalities_created} mods"
            self.db.commit()

            return {"dataset": dataset_external_id, "status": "SUCCESS", "dimensions": dimensions_created, "modalities": modalities_created}

        except Exception as e:
            item.status = "FAILED"
            item.error_message = str(e)
            self.db.commit()
            raise
