import redis
import numpy as np
import json
from sentence_transformers import SentenceTransformer


modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
THRESHOLD = 0.75 #similitud mínima para considerar hit
TTL = 86400  # 24 horas en segundos

# Conexión a Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def buscar_en_cache(pregunta: str):
    """Busca si hay una respuesta cacheada para esta pregunta"""
    embedding_pregunta = modelo.encode(pregunta)
    
    # Obtener todas las keys del cache
    keys = r.keys("cache:*")
    
    for key in keys:
        entrada = json.loads(r.get(key))
        embedding_guardado = np.array(entrada["embedding"])
        
        similitud = np.dot(embedding_pregunta, embedding_guardado) / (
            np.linalg.norm(embedding_pregunta) * np.linalg.norm(embedding_guardado)
        )
        
        if similitud >= THRESHOLD:
            print(f"✅ Cache hit! Similitud: {similitud:.3f}")
            return entrada["respuesta"]
    
    return None

def guardar_en_cache(pregunta: str, respuesta: str):
    """Guarda una nueva entrada en Redis con TTL"""
    embedding = modelo.encode(pregunta).tolist()
    
    entrada = {
        "pregunta": pregunta,
        "embedding": embedding,
        "respuesta": respuesta
    }
    
    key = f"cache:{pregunta[:50]}"
    r.setex(key, TTL, json.dumps(entrada))
    print(f"💾 Guardado en Redis: '{pregunta[:50]}...'")

