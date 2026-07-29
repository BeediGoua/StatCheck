import os
import hashlib
import requests
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from src.models.sources import Source
from src.models.catalogue import Dataset
from src.models.structure import Dimension, Modality, DatasetDimension
from src.models.series import Series, SeriesDimensionValue
from src.models.ingestion import IngestionItem

BASE_URL = "https://bdm.insee.fr/series/sdmx/data"
NORMALIZED_DIR = Path("data/normalized/INSEE_BDM")

class ObservationIngester:
    def __init__(self, db: Session):
        self.db = db
        self.source = self.db.query(Source).filter_by(code="INSEE_BDM").first()

    def run_for_dataset(self, dataset_external_id: str, run_id: str) -> dict:
        dataset = self.db.query(Dataset).filter_by(source_id=self.source.id, external_id=dataset_external_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_external_id} introuvable en base de donnees.")

        item = self.db.query(IngestionItem).filter_by(run_id=run_id, item_type="DATA", external_id=dataset_external_id).first()
        if not item:
            item = IngestionItem(run_id=run_id, item_type="DATA", external_id=dataset_external_id, status="RUNNING")
            self.db.add(item)
            self.db.commit()
        else:
            item.status = "RUNNING"
            self.db.commit()

        try:
            url = f"{BASE_URL}/{dataset_external_id}"
            # Stream the response to avoid loading huge XMLs into memory
            response = requests.get(url, stream=True, timeout=120)
            if response.status_code == 404:
                raise ValueError("Aucune donnee pour ce dataset.")
            if response.status_code == 413:
                raise ValueError("Payload Too Large (413). Il faut specifier des filtres SDMX (non supporte en batch global pour ce dataset massif).")
            response.raise_for_status()
            response.raw.decode_content = True

            # Pre-load dimensions and modalities for fast mapping
            dimensions = self.db.query(Dimension).join(DatasetDimension).filter(DatasetDimension.dataset_id == dataset.id).all()
            dim_map = {d.external_id: d.id for d in dimensions}
            
            # Map for modalities: (dimension_id, code) -> modality_id
            mods = self.db.query(Modality).filter(Modality.dimension_id.in_(list(dim_map.values()))).all()
            mod_map = {(m.dimension_id, m.code): m.id for m in mods}

            observations = []
            series_count = 0
            obs_count = 0

            # Parse XML efficiently
            context = ET.iterparse(response.raw, events=("end",))
            for event, elem in context:
                # Retirer le namespace du tag pour la comparaison (ex: {http://...}Series -> Series)
                tag_name = elem.tag.split('}')[-1]
                
                if tag_name == "Series":
                    attribs = elem.attrib
                    idbank = attribs.get("IDBANK")
                    title_fr = attribs.get("TITLE_FR")
                    last_update_str = attribs.get("LAST_UPDATE")
                    
                    if not idbank:
                        elem.clear()
                        continue

                    # Gestion de la date de derniere mise a jour (ex: "2026-05-13")
                    last_update = None
                    if last_update_str:
                        try:
                            # Parfois on a T00:00:00, donc on prend que les 10 premiers car.
                            last_update = datetime.strptime(last_update_str[:10], "%Y-%m-%d").date()
                        except ValueError:
                            pass

                    # Upsert Series
                    series_obj = self.db.query(Series).filter_by(dataset_id=dataset.id, external_id=idbank).first()
                    if not series_obj:
                        series_obj = Series(dataset_id=dataset.id, external_id=idbank, title=title_fr, last_updated_at=last_update)
                        self.db.add(series_obj)
                        self.db.flush()
                    else:
                        series_obj.title = title_fr
                        series_obj.last_updated_at = last_update

                    # Insertion DimensionValues (uniquement si non existant)
                    # On cherche d'abord s'il y a deja des valeurs (pour aller plus vite)
                    existing_sdv = self.db.query(SeriesDimensionValue).filter_by(series_id=series_obj.id).count()
                    if existing_sdv == 0:
                        for attr_k, attr_v in attribs.items():
                            if attr_k in dim_map:
                                dim_id = dim_map[attr_k]
                                mod_id = mod_map.get((dim_id, attr_v))
                                if mod_id:
                                    sdv = SeriesDimensionValue(series_id=series_obj.id, dimension_id=dim_id, modality_id=mod_id)
                                    self.db.add(sdv)
                    
                    # Parse observations within this series
                    for obs_elem in elem:
                        obs_tag = obs_elem.tag.split('}')[-1]
                        if obs_tag == "Obs":
                            time_period = obs_elem.attrib.get("TIME_PERIOD")
                            obs_value = obs_elem.attrib.get("OBS_VALUE")
                            obs_status = obs_elem.attrib.get("OBS_STATUS")
                            
                            if time_period and obs_value is not None:
                                try:
                                    val_float = float(obs_value)
                                    observations.append({
                                        "idbank": idbank,
                                        "time_period": time_period,
                                        "obs_value": val_float,
                                        "obs_status": obs_status,
                                        "year": time_period[:4]
                                    })
                                    obs_count += 1
                                except ValueError:
                                    pass
                    
                    self.db.flush() # flush pour garder la memoire legere
                    series_count += 1
                    elem.clear() # Liberer la memoire XML

            # Sauvegarde en Parquet partitionne
            if observations:
                df = pd.DataFrame(observations)
                table = pa.Table.from_pandas(df)
                
                out_path = NORMALIZED_DIR / dataset_external_id
                out_path.mkdir(parents=True, exist_ok=True)
                
                pq.write_to_dataset(
                    table,
                    root_path=str(out_path),
                    partition_cols=['year'],
                    use_dictionary=True,
                    compression='snappy'
                )

            self.db.commit()

            item.status = "SUCCESS"
            item.error_message = f"{series_count} series, {obs_count} obs"
            self.db.commit()

            return {"dataset": dataset_external_id, "status": "SUCCESS", "series": series_count, "observations": obs_count}

        except Exception as e:
            item.status = "FAILED"
            item.error_message = str(e)
            self.db.commit()
            raise
