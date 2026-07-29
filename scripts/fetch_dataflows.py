import time
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

# Constantes de l'API BDM
BASE_URL = "https://bdm.insee.fr/series/sdmx"
AGENCY = "FR1"
VERSION = "1.0"
NAMESPACES = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
OUTPUT_DIRECTORY = Path("data")

# Dataflows issus de la cartographie
MVP_DATAFLOWS = [
    "IPC-2025", "IPCH-2025", "CHOMAGE-TRIM-NATIONAL", "EMPLOI-BIT-TRIM",
    "EMPLOI-SALARIE-TRIM-NATIONAL", "DEMANDES-EMPLOIS-NATIONALES",
    "NAISSANCES-FECONDITE", "POPULATION-STRUCTURE", "DECES-MORTALITE",
    "CREATIONS-ENTREPRISES-METHODE-2022"
]

CORE_EXTENSION_DATAFLOWS = [
    # Ajoute ici d'autres dataflows si tu en as dans la cartographie
]

SPECIALIZED_DATAFLOWS = [
    "ODD-ERADICATION-PAUVRETE",
    "TCRED-SALAIRES-REVENUS-TAUX-PAUVRETE-AGE",
    "TCRED-ESTIMATIONS-POPULATION",
    "TCRED-ECONOMIE-PIB-REG",
    "TCRED-EMPLOI-SALARIE-TRIM",
    "TCRED-SALAIRES-REVENUS-MEN",
    "TCRED-SALAIRES-REVENUS-REV-SAL-SEXE-CS",
    "TCRED-ENTREPRISES-EMP-SAL-AN-TAILLE",
    "IPGD-2015",
    "IPC-PM-2015",
    "IPPI-2021",
    "IPAGRI-BASE-2020",
    "ENQ-CONJ-MENAGES",
]


def get_xml(session: requests.Session, url: str) -> ET.Element:
    """Télécharge et parse une réponse SDMX Structure XML."""
    response = session.get(
        url,
        headers={"Accept": "application/vnd.sdmx.structure+xml"},
        timeout=60,
    )
    response.raise_for_status()
    return ET.fromstring(response.content)


def preferred_name(element: ET.Element) -> str:
    """Retourne le nom français, ou le premier nom disponible."""
    names = element.findall("common:Name", NAMESPACES)
    for name in names:
        if name.get(XML_LANG) == "fr":
            return (name.text or "").strip()
    return (names[0].text or "").strip() if names else ""


def list_dataflows(session: requests.Session) -> dict[str, str]:
    """Récupère le catalogue complet au lieu de maintenir des IDs supposés."""
    root = get_xml(
        session,
        f"{BASE_URL}/dataflow/{AGENCY}/all/{VERSION}?references=none",
    )
    result = {}
    for flow in root.findall(".//structure:Dataflow", NAMESPACES):
        result[flow.get("id", "")] = preferred_name(flow)
    return result


def get_dimensions(session: requests.Session, dataflow_id: str) -> list[dict]:
    """Récupère les dimensions dans l'ordre requis pour une clé SDMX."""
    root = get_xml(
        session,
        f"{BASE_URL}/datastructure/{AGENCY}/{dataflow_id}/{VERSION}"
        "?references=none",
    )
    dimensions = []
    path = (
        ".//structure:DataStructureComponents/"
        "structure:DimensionList/structure:Dimension"
    )
    for dimension in root.findall(path, NAMESPACES):
        dimensions.append(
            {
                "id": dimension.get("id"),
                "position": int(dimension.get("position", "0")),
                "type": "dimension",
            }
        )

    time_dimension = root.find(
        ".//structure:DataStructureComponents/"
        "structure:DimensionList/structure:TimeDimension",
        NAMESPACES,
    )
    if time_dimension is not None:
        dimensions.append(
            {
                "id": time_dimension.get("id"),
                "position": int(time_dimension.get("position", "999")),
                "type": "time",
            }
        )
    return sorted(dimensions, key=lambda item: item["position"])


def tier_for(dataflow_id: str) -> str:
    if dataflow_id in MVP_DATAFLOWS:
        return "MVP"
    if dataflow_id in CORE_EXTENSION_DATAFLOWS:
        return "CORE_EXTENSION"
    return "SPECIALIZED"


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    selected_ids = (
        MVP_DATAFLOWS
        + CORE_EXTENSION_DATAFLOWS
        + SPECIALIZED_DATAFLOWS
    )

    with requests.Session() as session:
        catalog = list_dataflows(session)
        rows = []

        for index, dataflow_id in enumerate(selected_ids, start=1):
            if dataflow_id not in catalog:
                rows.append(
                    {
                        "dataflow_id": dataflow_id,
                        "title": "",
                        "tier": tier_for(dataflow_id),
                        "exists": False,
                        "dimension_count": 0,
                        "dimensions": "",
                        "error": "Absent du catalogue courant",
                    }
                )
                continue

            try:
                dimensions = get_dimensions(session, dataflow_id)
                rows.append(
                    {
                        "dataflow_id": dataflow_id,
                        "title": catalog[dataflow_id],
                        "tier": tier_for(dataflow_id),
                        "exists": True,
                        "dimension_count": len(dimensions),
                        "dimensions": " | ".join(
                            item["id"] for item in dimensions
                        ),
                        "error": "",
                    }
                )
            except requests.RequestException as error:
                rows.append(
                    {
                        "dataflow_id": dataflow_id,
                        "title": catalog[dataflow_id],
                        "tier": tier_for(dataflow_id),
                        "exists": True,
                        "dimension_count": 0,
                        "dimensions": "",
                        "error": str(error),
                    }
                )

            print(f"[{index:02d}/{len(selected_ids)}] {dataflow_id} traité.")
            time.sleep(0.10)

    dataframe = pd.DataFrame(rows)
    dataframe.to_csv(
        OUTPUT_DIRECTORY / "selected_dataflows.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print("Fichier CSV généré avec succès dans data/selected_dataflows.csv")

if __name__ == "__main__":
    main()
