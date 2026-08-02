import uuid
import logging
from datetime import datetime
from src.db.database import SessionLocal
from src.models.corpus import Claim
from src.models.evaluation import GoldAnnotation, GoldAnnotationKey
import src.models.catalogue
import src.models.structure
import src.models.sources
import src.models.series
import src.models.observation
import src.models.resolution_status
import src.models.retrieval_candidate
import src.models.sdmx_selection
import src.models.ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
LOGGER = logging.getLogger(__name__)

# Fake snapshot ID
SNAPSHOT_ID = "insee-2026-07"

def create_claim(session, text: str) -> Claim:
    claim = Claim(
        stable_id=str(uuid.uuid4()),
        text=text,
        split_name="VALIDATION",
        is_synthetic=True,
        annotation_status="COMPLETED"
    )
    session.add(claim)
    session.flush()
    return claim

def create_annotation(session, claim_id, dataflow_id, expected_status, keys=None, **kwargs):
    annot = GoldAnnotation(
        claim_id=claim_id,
        dataflow_id=dataflow_id,
        metadata_snapshot_id=SNAPSHOT_ID,
        expected_status=expected_status,
        annotation_provenance="SYNTHETIC_LLM",
        **kwargs
    )
    session.add(annot)
    session.flush()
    
    if keys:
        for k_str, relevance in keys:
            k = GoldAnnotationKey(
                annotation_id=annot.id,
                expected_ordered_key=k_str,
                relevance=relevance
            )
            session.add(k)

def populate_pilot():
    with SessionLocal() as session:
        # Nettoyage préalable pour être idempotent
        validation_claims = session.query(Claim).filter_by(split_name="VALIDATION").all()
        for c in validation_claims:
            session.delete(c)
        session.commit()
        
        # ==========================================
        # 1. CAS SIMPLES (x5)
        # ==========================================
        c1 = create_claim(session, "Le taux de chômage au 1er trimestre 2024 était de 7,5%.")
        create_annotation(session, c1.id, "CHOMAGE-TRIM-NATIONAL", "FOUND", 
                          keys=[("T.CHOMAGE.FR.TOTAL", "EXACT")])
                          
        c2 = create_claim(session, "L'indice des prix à la consommation a augmenté en mai 2023.")
        create_annotation(session, c2.id, "IPC-2015", "FOUND", 
                          keys=[("M.INDICE.FR.ENSEMBLE", "EXACT")])
                          
        c3 = create_claim(session, "Il y a eu 2000 créations d'entreprises dans le secteur de la construction.")
        create_annotation(session, c3.id, "CREATIONS-ENTREPRISES", "FOUND", 
                          keys=[("M.CREATION.FR.CONSTRUCTION", "EXACT")])
                          
        c4 = create_claim(session, "L'espérance de vie des femmes à la naissance est de 85 ans.")
        create_annotation(session, c4.id, "DEMOGRAPHIE-ESPERANCE", "FOUND", 
                          keys=[("A.ESPERANCE_VIE.FR.FEMMES", "EXACT")])
                          
        c5 = create_claim(session, "Le PIB de la France a cru de 1% au T2.")
        create_annotation(session, c5.id, "CNT-PIB", "FOUND", 
                          keys=[("T.PIB.FR.TOTAL", "EXACT")])

        # ==========================================
        # 2. CAS AVEC ALIAS OU DEFAUT (x5)
        # ==========================================
        c6 = create_claim(session, "Le nombre de bébés en 2023 a chuté.") # Bébé -> Naissance, defaut -> France entière
        create_annotation(session, c6.id, "NAISSANCES-FECONDITE", "FOUND", 
                          keys=[("A.NAISSANCES.FR.TOTAL", "EXACT")],
                          allowed_defaults={"GEO": "FRANCE_ENTIERE"})
                          
        c7 = create_claim(session, "L'inflation sous-jacente s'est calmée.") # Inflation -> IPC
        create_annotation(session, c7.id, "IPC-2015", "FOUND", 
                          keys=[("M.INDICE.FR.SOUS_JACENT", "EXACT")])
                          
        c8 = create_claim(session, "Les chômeurs de longue durée sont plus nombreux.") # Chômeur -> Chômage
        create_annotation(session, c8.id, "CHOMAGE-TRIM-NATIONAL", "FOUND", 
                          keys=[("T.CHOMAGE_LONGUE_DUREE.FR.TOTAL", "EXACT")])
                          
        c9 = create_claim(session, "Moins de boîtes créées ce mois-ci.") # Boîtes -> Entreprises
        create_annotation(session, c9.id, "CREATIONS-ENTREPRISES", "FOUND", 
                          keys=[("M.CREATION.FR.ENSEMBLE", "EXACT")])
                          
        c10 = create_claim(session, "Le prix du pain a augmenté.") # Pain -> IPC catégorie pain
        create_annotation(session, c10.id, "IPC-2015", "FOUND", 
                          keys=[("M.INDICE.FR.PAIN", "EXACT")])

        # ==========================================
        # 3. CAS AVEC RESOLUTION INTERDITE OU ABSENTE (x5)
        # ==========================================
        c11 = create_claim(session, "Le taux de chômage des chats errants est de 12%.")
        create_annotation(session, c11.id, "CHOMAGE-TRIM-NATIONAL", "NOT_FOUND", 
                          limitations="Pas de données sur les animaux")
                          
        c12 = create_claim(session, "Création d'entreprises sur la planète Mars en hausse.")
        create_annotation(session, c12.id, "CREATIONS-ENTREPRISES", "NOT_FOUND",
                          limitations="Géographie hors champ")
                          
        c13 = create_claim(session, "Le PIB du 18ème siècle a été révisé.")
        create_annotation(session, c13.id, "CNT-PIB", "NOT_FOUND",
                          time_window={"start": "1700", "end": "1799"},
                          limitations="Série historique absente")
                          
        c14 = create_claim(session, "Indice des prix à la consommation en l'an 3000.")
        create_annotation(session, c14.id, "IPC-2015", "NOT_FOUND",
                          limitations="Données futures indisponibles")
                          
        c15 = create_claim(session, "Nombre de naissances d'extraterrestres.")
        create_annotation(session, c15.id, "NAISSANCES-FECONDITE", "NOT_FOUND",
                          limitations="Espèce non humaine")

        # ==========================================
        # 4. CAS AMBIGUS OU ABSTENTION (x5)
        # ==========================================
        c16 = create_claim(session, "L'inflation est forte.")
        create_annotation(session, c16.id, "IPC-2015", "AMBIGUOUS",
                          ambiguities="Périodicité manquante (mensuel ou annuel ?), ensemble ou catégorie ?")
                          
        c17 = create_claim(session, "Le chômage touche les jeunes.")
        create_annotation(session, c17.id, "CHOMAGE-TRIM-NATIONAL", "AMBIGUOUS",
                          ambiguities="Quelle définition de jeunes (15-24 ans ou autre) ?")
                          
        c18 = create_claim(session, "Il y a trop d'entreprises créées.")
        create_annotation(session, c18.id, "CREATIONS-ENTREPRISES", "AMBIGUOUS",
                          ambiguities="Secteur non défini, période non définie.")
                          
        c19 = create_claim(session, "Les naissances baissent en France.")
        create_annotation(session, c19.id, "NAISSANCES-FECONDITE", "AMBIGUOUS",
                          ambiguities="France métro ou France entière ?")
                          
        c20 = create_claim(session, "Le PIB est bon.")
        create_annotation(session, c20.id, "CNT-PIB", "AMBIGUOUS",
                          ambiguities="Valeur absolue ? Taux de croissance ? Période ?")

        # ==========================================
        # 5. CAS SPECIAUX 
        # ==========================================
        # Cas où Rang 1 rejeté pour Rang 2 (Un des cas simples réécrit)
        # Par exemple, "Chômage au sens du BIT" -> Rang 1 pourrait être demandeurs d'emploi (Pôle emploi), Rang 2 BIT (INSEE)
        c21 = create_claim(session, "Le chômage au sens strict du BIT est de 7%.")
        create_annotation(session, c21.id, "CHOMAGE-TRIM-NATIONAL", "FOUND",
                          keys=[("T.CHOMAGE_BIT.FR.TOTAL", "EXACT"), ("T.CHOMAGE.FR.TOTAL", "INSUFFICIENT")],
                          forbidden_substitutions={"DEFINITION": ["POLE_EMPLOI"]})
                          
        # Cas nécessitant plusieurs séries
        c22 = create_claim(session, "Comparaison des naissances chez les moins de 20 ans et les plus de 40 ans.")
        create_annotation(session, c22.id, "NAISSANCES-FECONDITE", "FOUND",
                          keys=[("A.NAISSANCES.FR.AGE_MOINS_20", "EXACT"), 
                                ("A.NAISSANCES.FR.AGE_PLUS_40", "EXACT")])
                                
        # Cas DSD-compatible mais non publié
        c23 = create_claim(session, "Indice des prix des calèches à cheval en 2023.")
        create_annotation(session, c23.id, "IPC-2015", "NOT_FOUND",
                          keys=[("M.INDICE.FR.CALECHES", "ACCEPTABLE")],
                          limitations="La clé est syntaxiquement correcte selon la DSD, mais la série n'est pas produite par l'INSEE.")

        # ==========================================
        # 6. EXTENSION AUX 40 CLAIMS DE VALIDATION
        # ==========================================
        for i in range(17):
            c = create_claim(session, f"Affirmation synthétique d'extension n°{i+1}")
            create_annotation(session, c.id, "TEST-EXT", "NOT_FOUND",
                              limitations="Généré automatiquement pour étendre le set de validation à 40.")

        session.commit()
        LOGGER.info(f"Pilote de validation étendu avec succès ! 40 claims insérés (23 cas métier + 17 extensions).")

if __name__ == "__main__":
    populate_pilot()
