import urllib.request
import re

url = "https://www.insee.fr/fr/information/2862759"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
    
    links = re.findall(r'href=[\"\'\']([^\"\'\']*correspondance_idbank_dimension[^\"\'\']*\.zip)[\"\'\']', html)
    print("Links found:", set(links))
except Exception as e:
    print(f"Error: {e}")
