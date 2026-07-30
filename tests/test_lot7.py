import sys
import os
import unittest
import math

# Add root directory to sys path so we can import the scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.etape_5.hybrid_search import get_rrf_score, perform_rrf
from scripts.etape_6.deterministic_reranker import apply_deterministic_reranker
from scripts.etape_7.evaluate_retrieval import compute_ndcg, evaluate_metrics, calculate_hnwr

class TestLot7Pipeline(unittest.TestCase):
    
    # ---------------------------------------------------------
    # TESTS ÉTAPE 5 : RRF (Reciprocal Rank Fusion)
    # ---------------------------------------------------------
    def test_rrf_score(self):
        k = 60
        weight = 1.0
        rank = 1
        expected = 1.0 / (60 + 1)
        self.assertEqual(get_rrf_score(rank, k, weight), expected)
        self.assertEqual(get_rrf_score(None, k, weight), 0.0)
        
    def test_perform_rrf(self):
        lexical = ["A", "B", "C"]
        vector = ["B", "C", "D"]
        
        results = perform_rrf(lexical, vector, k=60, lexical_weight=1.0, vector_weight=1.0, consensus_bonus=0.1)
        
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]['dataset_id'], 'B')
        self.assertEqual(results[1]['dataset_id'], 'C')
        
        self.assertTrue(results[0]['rrf_score'] > 0.1)
        self.assertTrue(results[3]['rrf_score'] < 0.1)

    # ---------------------------------------------------------
    # TESTS ÉTAPE 6 : RERANKER DÉTERMINISTE
    # ---------------------------------------------------------
    def test_deterministic_reranker_rejections(self):
        claim_context = {
            'required_indicator': 'CHOMAGE',
            'required_dimensions': ['AGE'],
            'forbidden_sources': ['BAD_SOURCE']
        }
        
        candidates = [
            {'dataset_id': '1', 'rrf_score': 0.1, 'cosine_distance': 0.1, 'metadata': {'is_active': False, 'source': 'INSEE', 'dimensions': ['AGE']}},
            {'dataset_id': '2', 'rrf_score': 0.1, 'cosine_distance': 0.1, 'metadata': {'is_active': True, 'source': 'BAD_SOURCE', 'dimensions': ['AGE']}},
            {'dataset_id': '3', 'rrf_score': 0.1, 'cosine_distance': 0.1, 'metadata': {'is_active': True, 'source': 'INSEE', 'dimensions': []}},
        ]
        
        res = apply_deterministic_reranker(candidates, claim_context)
        self.assertTrue(res['abstention'])
        self.assertTrue(all(c['is_rejected'] for c in res['ranked_results']))

    def test_deterministic_reranker_bonuses(self):
        claim_context = {
            'required_indicator': 'CHOMAGE',
            'required_dimensions': ['AGE', 'SEXE'],
            'forbidden_sources': []
        }
        
        candidates = [
            {'dataset_id': 'A', 'rrf_score': 0.1, 'cosine_distance': 0.1, 'metadata': {'is_active': True, 'indicator_code': 'CHOMAGE', 'dimensions': ['AGE', 'SEXE']}},
            {'dataset_id': 'B', 'rrf_score': 0.1, 'cosine_distance': 0.1, 'metadata': {'is_active': True, 'indicator_code': 'POPULATION', 'dimensions': ['AGE', 'SEXE']}},
        ]
        
        res = apply_deterministic_reranker(candidates, claim_context)
        self.assertFalse(res['abstention'])
        
        top = res['ranked_results'][0]
        bottom = res['ranked_results'][1]
        
        self.assertEqual(top['dataset_id'], 'A')
        self.assertEqual(top['deterministic_score'], (1, 1, 2, 0.1)) # Valid, exact indicator, 2 dims, 0.1 rrf
        self.assertEqual(bottom['dataset_id'], 'B')
        self.assertEqual(bottom['deterministic_score'], (1, 0, 2, 0.1)) # Valid, wrong indicator, 2 dims, 0.1 rrf

    def test_deterministic_reranker_abstention_aberrant(self):
        claim_context = {'required_indicator': 'X', 'required_dimensions': [], 'forbidden_sources': []}
        candidates = [
            {'dataset_id': 'A', 'rrf_score': 0.1, 'cosine_distance': 0.8, 'metadata': {'is_active': True}}
        ]
        res = apply_deterministic_reranker(candidates, claim_context, cosine_threshold=0.4)
        self.assertTrue(res['abstention'])
        self.assertIn("aberrante", res['abstention_reason'].lower())

    # ---------------------------------------------------------
    # TESTS ÉTAPE 7 : ÉVALUATION
    # ---------------------------------------------------------
    def test_compute_ndcg(self):
        self.assertEqual(compute_ndcg([3, 2, 1], 3), 1.0)
        self.assertEqual(compute_ndcg([0, 0], 2), 0.0)
        ndcg = compute_ndcg([1, 2, 3], 3)
        self.assertTrue(ndcg < 1.0 and ndcg > 0.0)
        
    def test_evaluate_metrics(self):
        ground_truth = {'A': 3, 'B': 2, 'C': 0}
        results = [{'dataset_id': 'A'}, {'dataset_id': 'B'}, {'dataset_id': 'C'}]
        
        metrics = evaluate_metrics(results, ground_truth, k_values=[1, 3])
        self.assertEqual(metrics['Exact_Recall@1'], 1.0)
        self.assertEqual(metrics['Acceptable_Recall@1'], 1.0)
        self.assertEqual(metrics['nDCG@1'], 1.0)
        self.assertEqual(metrics['Exact_Recall@3'], 1.0)

    def test_calculate_hnwr(self):
        results = [{'dataset_id': 'A'}, {'dataset_id': 'B'}]
        self.assertEqual(calculate_hnwr(results, positive_id='A', hard_negative_id='B'), 1.0)
        self.assertEqual(calculate_hnwr(results, positive_id='B', hard_negative_id='A'), 0.0)

if __name__ == '__main__':
    unittest.main()
