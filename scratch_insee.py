import urllib.request
import xml.etree.ElementTree as ET

url = 'https://bdm.insee.fr/series/sdmx/dataflow'
req = urllib.request.Request(url, headers={'Accept': 'application/xml'})
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        xml_data = response.read()
    root = ET.fromstring(xml_data)
    
    # namespaces
    ns = {
        'mes': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
        'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
        'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'
    }
    
    dataflows = root.findall('.//str:Dataflow', ns)
    print(f'Found {len(dataflows)} dataflows (datasets) in INSEE BDM.')
    for df in dataflows[:10]:
        df_id = df.get('id')
        name_elem = df.find('.//com:Name[@xml:lang="fr"]', ns)
        name = name_elem.text if name_elem is not None else 'No title'
        print(f'- {df_id}: {name}')
except Exception as e:
    print('Failed to fetch:', e)
