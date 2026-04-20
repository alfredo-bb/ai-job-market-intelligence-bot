import sys
sys.stdout.flush()

from sentence_transformers import SentenceTransformer

modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("✅ modelo_embeddings.py cargado")