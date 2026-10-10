import logging
from unittest.mock import MagicMock
from src.parser.resolvers.orchestrator import orchestrate_resolution

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def run_test():
    logging.info("--- DÉMARRAGE DU TEST D'INTÉGRATION R1 (ÉTAPE 4) AVEC MOCK ---")
    
    session_mock = MagicMock()
    
    # Mock des comportements de requêtes DB
    def mock_query(model):
        query_mock = MagicMock()
        # Mock pour get_available_frequencies
        if model.__name__ == 'DataflowDimension':
            dim_mock = MagicMock()
            dim_mock.dimension_id = "FREQ"
            query_mock.filter_by.return_value.first.return_value = dim_mock
            
        # Mock pour DataflowModality (fréquences dispo)
        if model.__name__ == 'DataflowModality':
            mod_q = MagicMock(code="Q")
            query_mock.filter_by.return_value.all.return_value = [mod_q]
            
        # Mock pour l'index de disponibilité
        if model.__name__ == 'Series':
            # On simule que Q.Y15T24.FM et Q.Y15T29.FM existent
            def filter_by_mock(**kwargs):
                series_mock = MagicMock()
                if kwargs.get('series_key') in ["Q.Y15T24.FM", "Q.Y15T29.FM"]:
                    return MagicMock(first=lambda: True)
                return MagicMock(first=lambda: None)
            query_mock.filter_by.side_effect = filter_by_mock
            
        return query_mock
        
    session_mock.query = mock_query

    structured_dimensions = [
        {"dimension": "FREQ", "candidates": [{"code": "Q"}]},
        {"dimension": "AGE", "candidates": [{"code": "Y15T24"}, {"code": "Y15T29"}]},
        {"dimension": "GEO", "candidates": [{"code": "FM"}]}
    ]

    top_k = [{"dataflow_id": "CHOMAGE_01", "snapshot_id": "test_snap_001", "rank": 1}]

    logging.info("Appel de l'Orchestrateur R1...")
    result = orchestrate_resolution(session_mock, top_k, structured_dimensions)
    
    logging.info(f"RÉSULTAT DE L'ORCHESTRATION : {result}")
    
    assert result["status"] == "SUCCESS"
    assert len(result["resolved_keys"]) == 2
    keys = [k["sdmx_key"] for k in result["resolved_keys"]]
    assert "Q.Y15T24.FM" in keys
    assert "Q.Y15T29.FM" in keys
    
    logging.info("✅ TOUS LES TESTS SONT AU VERT ! L'Architecture R1 fonctionne parfaitement sur l'environnement simulé.")

if __name__ == "__main__":
    run_test()
