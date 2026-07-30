import os
import sys
import unittest
import psycopg2
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/statcheck")

class TestPostgresE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg2.connect(DATABASE_URL)
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.cur.close()
        cls.conn.close()

    def test_extensions_installed(self):
        self.cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'unaccent');")
        extensions = [row[0] for row in self.cur.fetchall()]
        self.assertIn('vector', extensions)
        self.assertIn('unaccent', extensions)

    def test_unaccent_french_config(self):
        self.cur.execute("SELECT ts_lexize('french_stem', unaccent('chômage'));")
        res1 = self.cur.fetchone()[0]
        self.cur.execute("SELECT ts_lexize('french_stem', unaccent('chomage'));")
        res2 = self.cur.fetchone()[0]
        self.assertEqual(res1, ['chomag'])
        self.assertEqual(res2, ['chomag'])
        self.assertEqual(res1, res2)
        
    def test_fts_weights_and_unaccent(self):
        # We assume dataset CHOMAGE-TRIM-NATIONAL is in the DB
        self.cur.execute("""
            SELECT dataset_id, ts_rank_cd(lexical_vector, to_tsquery('french_unaccent', 'chômage')) AS score
            FROM search_documents
            WHERE dataset_id = 'CHOMAGE-TRIM-NATIONAL'
        """)
        row = self.cur.fetchone()
        if row:
            self.assertTrue(row[1] > 0)
            
    def test_vector_dimension(self):
        self.cur.execute("SELECT embedding FROM entity_embeddings LIMIT 1;")
        row = self.cur.fetchone()
        if row and row[0]:
            # pgvector returns a string formatted like '[0.1, 0.2, ...]'
            vec_str = row[0]
            vec_list = vec_str.strip('[]').split(',')
            self.assertEqual(len(vec_list), 384) # We chose MiniLM

if __name__ == '__main__':
    unittest.main()
