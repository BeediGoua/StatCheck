import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path

NAMESPACES = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

def preferred_name(element: ET.Element) -> str:
    names = element.findall("common:Name", NAMESPACES)
    for name in names:
        if name.get(XML_LANG) == "fr":
            return (name.text or "").strip()
    return (names[0].text or "").strip() if names else ""

def extract_real_datasets():
    raw_dir = Path("data/raw")
    output_path = Path("data/catalog/search_documents_real.json")
    
    datasets = []
    
    if not raw_dir.exists():
        print(f"Directory {raw_dir} does not exist.")
        return
        
    xml_files = list(raw_dir.glob("insee_bdm_structure_*.xml"))
    print(f"Found {len(xml_files)} XML files.")
    
    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # The dataset ID is usually in the filename
            filename = xml_file.stem
            # filename format: insee_bdm_structure_ID_TIMESTAMP
            parts = filename.split('_')
            dataset_id = parts[3] if len(parts) >= 4 else "UNKNOWN"
            if dataset_id == "UNKNOWN":
                # handle names with multiple underscores
                dataset_id = filename.replace("insee_bdm_structure_", "").rsplit("_", 2)[0]
                
            # Try to get Title and Description from the XML
            title = dataset_id
            description = ""
            
            # In SDMX from INSEE BDM, the structure is usually in DataStructure
            data_structure = root.find(".//structure:DataStructure", NAMESPACES)
            if data_structure is not None:
                title = preferred_name(data_structure) or dataset_id
                desc_element = data_structure.find("common:Description", NAMESPACES)
                if desc_element is not None:
                    description = (desc_element.text or "").strip()
            
            # Extract Dimensions
            dimensions = []
            dim_list = root.find(".//structure:DimensionList", NAMESPACES)
            if dim_list is not None:
                for dim_el in dim_list:
                    dim_id = dim_el.get("id")
                    if dim_id and dim_id not in ['TIME_PERIOD', 'FREQ']: # skip generic dims if needed
                        dimensions.append(dim_id)
            
            # Form embedding text
            embedding_text = f"Dataset: {title} ({dataset_id}). Description: {description}. Dimensions: {', '.join(dimensions)}."
            
            doc = {
                "dataset_id": dataset_id,
                "indicator_code": dataset_id, # Simplified for offline test
                "title": title,
                "description": description,
                "dimensions": dimensions,
                "embedding_text": embedding_text,
                "is_active": True,
                "source": "INSEE"
            }
            
            # Prevent duplicates if multiple timestamps exist
            if not any(d['dataset_id'] == dataset_id for d in datasets):
                datasets.append(doc)
            
        except Exception as e:
            print(f"Error parsing {xml_file.name}: {e}")
            
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(datasets, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully extracted {len(datasets)} datasets to {output_path}")

if __name__ == "__main__":
    extract_real_datasets()
