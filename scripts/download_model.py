"""
download_model.py — one-time script to pre-download and cache the
sentence-transformers embedding model.
Run this ONCE before starting the app:
    python scripts/download_model.py
"""
import os
import sys

os.environ["TRANSFORMERS_NO_PACKAGES_SCAN"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Ensure network access is ON for the download
os.environ.pop("HF_HUB_OFFLINE", None)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

print(f"Downloading embedding model: {config.EMBEDDING_MODEL}")
print("This is a one-time download (~30MB via ONNX). Please wait...")

from fastembed import TextEmbedding

model = TextEmbedding(model_name=config.EMBEDDING_MODEL)
result = list(model.embed(["telecom churn analysis"]))
print(f"Model cached. Embedding dim: {len(result[0])}")
print("Done. Subsequent app starts will be fast.")
