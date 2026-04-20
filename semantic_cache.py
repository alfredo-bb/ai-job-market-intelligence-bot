import redis
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import os


from modelo_embeddings import modelo
THRESHOLD = 0.75 #similitud mínima para considerar hit
TTL = 86400  # 24 horas en segundos

# Conexión a Redis
redis_host = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=redis_host, port=6379, db=0)
print(f"🔴 Conectando a Redis en {redis_host}...")
try:
    r.ping()
    print("✅ Redis conectado")
    REDIS_DISPONIBLE = True
except Exception as e:
    print(f"⚠️ Redis no disponible: {e}. Usando cache en memoria.")
    REDIS_DISPONIBLE = False
    cache_memoria = []

def buscar_en_cache(pregunta: str):
    embedding_pregunta = modelo.encode(pregunta)
    
    if REDIS_DISPONIBLE:
        keys = r.keys("cache:*")
        entradas = [json.loads(r.get(key)) for key in keys]
    else:
        entradas = cache_memoria
    
    for entrada in entradas:
        embedding_guardado = np.array(entrada["embedding"])
        similitud = np.dot(embedding_pregunta, embedding_guardado) / (
            np.linalg.norm(embedding_pregunta) * np.linalg.norm(embedding_guardado)
        )
        if similitud >= THRESHOLD:
            print(f"✅ Cache hit! Similitud: {similitud:.3f}")
            return entrada["respuesta"]
    
    return None

def guardar_en_cache(pregunta: str, respuesta: str):
    embedding = modelo.encode(pregunta).tolist()
    entrada = {
        "pregunta": pregunta,
        "embedding": embedding,
        "respuesta": respuesta
    }
    
    if REDIS_DISPONIBLE:
        key = f"cache:{pregunta[:50]}"
        r.setex(key, TTL, json.dumps(entrada))
        print(f"💾 Guardado en Redis: '{pregunta[:50]}...'")
    else:
        cache_memoria.append(entrada)
        print(f"💾 Guardado en memoria: '{pregunta[:50]}...'")
