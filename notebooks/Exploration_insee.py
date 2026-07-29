#!/usr/bin/env python
# coding: utf-8

# # Exploration de l'API INSEE BDM
# 
# Ce notebook sert à valider la structure des réponses de la Banque de Données Macroéconomiques de l'INSEE pour notre PoC.

# In[6]:


import requests
import pandas as pd
import xml.etree.ElementTree as ET

print("Environnement initialisé.")


# ## 1. Requête sur l'IPC (Inflation)
# Identifiant de famille (Dataflow) : `IPC-2015`
# 
# L'INSEE utilise le standard SDMX. Le point d'entrée pour récupérer la structure est :
# `https://bdm.insee.fr/series/sdmx/datastructure/FR1/IPC-2015`

# In[7]:


url = "https://bdm.insee.fr/series/sdmx/datastructure/FR1/IPC-2015"
response = requests.get(url)

if response.status_code == 200:
    print("Requête réussie ! Extraction des dimensions en cours...\n")

    # Parsing du XML avec ElementTree
    root = ET.fromstring(response.content)

    # Le SDMX utilise des namespaces (espaces de noms) stricts qu'il faut déclarer
    ns = {
        'mes': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
        'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
        'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'
    }

    # On cherche la liste des dimensions dans la structure du message
    dimensions = root.findall('.//str:DimensionList/str:Dimension', ns)

    print("=== DIMENSIONS OBLIGATOIRES POUR LA FAMILLE IPC-2015 ===")
    for dim in dimensions:
        dim_id = dim.get('id')
        print(f"- {dim_id}")

else:
    print(f"Erreur {response.status_code}")


# ## 2. Exploration des autres domaines (Chômage et Démographie)
# On répète l'opération pour les autres Dataflows.

# In[8]:


dataflows = ['CHOMAGE-TRIM-NATIONAL', 'NAISSANCES-FECONDITE']
for df in dataflows:
    url = f"https://bdm.insee.fr/series/sdmx/datastructure/FR1/{df}"
    res = requests.get(url)
    if res.status_code == 200:
        root = ET.fromstring(res.content)
        dims = root.findall('.//str:DimensionList/str:Dimension', ns)
        print(f"\n=== DIMENSIONS POUR {df} ===")
        for dim in dims:
            print(f"- {dim.get('id')}")
    else:
        print(f"Erreur sur {df}")


# ## 3. Le Test de Vérité (Les Observations)
# Récupérons la valeur de l'inflation d'Août 2022 (MVP-002) : *"Les prix à la consommation ont augmenté de 5,8 % entre août 2021 et août 2022."*
# 
# La façon la plus simple de récupérer les valeurs dans la BDM est d'utiliser l'identifiant unique de la série (`idbank`) et de télécharger le CSV officiel.
# L'idbank pour *"IPC - Ensemble des ménages - France - Ensemble - Glissement annuel"* est **1763852**.

# In[9]:


# Récupération de la donnée via l'API SDMX (format XML)
idbank = "001763852"
url_data = f"https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/{idbank}"

print(f"Téléchargement des données depuis {url_data}...")
res = requests.get(url_data)

if res.status_code == 200:
    root = ET.fromstring(res.content)

    # Extraction des observations (Période et Valeur)
    observations = []
    # Le tag Obs contient les attributs TIME_PERIOD et OBS_VALUE
    for obs in root.iter():
        if 'Obs' in obs.tag:
            observations.append({
                'Periode': obs.get('TIME_PERIOD'),
                'Valeur': float(obs.get('OBS_VALUE'))
            })

    df_clean = pd.DataFrame(observations)

    # Filtre sur Août 2022
    val_aout_2022 = df_clean[df_clean['Periode'] == '2022-08']
    print("\nRésultat pour Août 2022 :\n")
    print(val_aout_2022.to_string(index=False))
else:
    print("Erreur :", res.status_code)


# ## 4. Validation exhaustive de la Cartographie (Lot 1 complet)
# 
# Grâce au script `fetch_dataflows.py`, nous avons interrogé l'API INSEE pour valider l'existence et la structure de l'ensemble des Dataflows nécessaires à nos 30 affirmations. 
# Vérifions le résultat de cet export :

# In[10]:


import pandas as pd

df_carto = pd.read_csv("../data/selected_dataflows.csv")

# On affiche uniquement les Dataflows du MVP
mvp_dataflows = df_carto[df_carto['tier'] == 'MVP']
display(mvp_dataflows)

print(f"\n{len(mvp_dataflows)} Dataflows MVP ont été validés avec succès dans l'API BDM.")

