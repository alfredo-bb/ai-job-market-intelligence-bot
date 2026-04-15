from sentence_transformers import SentenceTransformer
import numpy as np

modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
THRESHOLD = 0.75 #similitud mínima para considerar hit

cache = [] # lista de pares {embedding, pregunta, respuesta}

def buscar_en_cache(pregunta: str):
    """Busca si hay una respuesta cacheada para esta pregunta"""
    if not cache:
        return None
    
    embedding_pregunta = modelo.encode(pregunta)

    for entrada in cache:
        similitud = np.dot(embedding_pregunta, entrada["embedding"]) / (
            np.linalg.norm(embedding_pregunta) * np.linalg.norm(entrada["embedding"])
            )
        if similitud >= THRESHOLD:
            print(f"✅ Cache hit! Similitud: {similitud:.3f}")
            return entrada["respuesta"]
        
    
        
    return None

def guardar_en_cache(pregunta: str, respuesta: str):
    """Guarda una nueva entrada en el cache"""
    embedding = modelo.encode(pregunta)
    cache.append({
        "embedding": embedding,
        "pregunta": pregunta,
        "respuesta": respuesta
    })
    print(f"💾 Guardado en cache: '{pregunta[:50]}...'")

