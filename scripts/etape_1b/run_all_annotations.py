import os
import sys

# Add root project directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from llm_pre_annotator import pre_annotate_with_llm

print("Annotating train...")
pre_annotate_with_llm(
    corpus_path="data/corpus/train.jsonl", 
    catalog_path="data/catalog/insee-catalog-real-2026-07-30.json", 
    output_path="data/corpus/train_pre_annotated.jsonl"
)

print("Annotating validation...")
pre_annotate_with_llm(
    corpus_path="data/corpus/validation.jsonl", 
    catalog_path="data/catalog/insee-catalog-real-2026-07-30.json", 
    output_path="data/corpus/validation_pre_annotated.jsonl"
)
