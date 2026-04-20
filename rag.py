from sentence_transformers import SentenceTransformer
import chromadb
from anthropic import Anthropic
from dotenv import load_dotenv
from database.db import cargar_ofertas_de_bbdd
import os
from rank_bm25 import BM25Okapi

load_dotenv()

from modelo_embeddings import modelo
cliente_chroma = chromadb.Client()
THRESHOLD = 1.2

def inicializar_coleccion():
    """Carga ofertas de PostgreSQL e indexa en Chroma y BM25"""
    coleccion = cliente_chroma.get_or_create_collection("ofertas_trabajo")
    
    try:
        print(f"📄 Cargando ofertas de BD...")
        ofertas = cargar_ofertas_de_bbdd()
        print(f"📄 {len(ofertas)} ofertas cargadas")
    except Exception as e:
        print(f"⚠️ No se pudo conectar a BD: {e}")
        ofertas=[]

    documentos = [o[0] for o in ofertas if o[0]]
    ids = [f"doc_{i}" for i in range(len(documentos))]
    embeddings = modelo.encode(documentos).tolist()
    
    coleccion.add(
        documents=documentos,
        embeddings=embeddings,
        ids=ids
    )

    # Construir indice BM25

    tokenized_docs = [doc.lower().split() for doc in documentos]
    bm25 = BM25Okapi(tokenized_docs)

    print(f"✅ {len(documentos)} ofertas indexadas en Chroma y BM25")
    return coleccion, bm25, documentos

def buscar_ofertas_relevantes(coleccion, bm25, documentos, pregunta: str) -> list:
    """Búsqueda híbrida: vectores + BM25"""

    # 1. Búsqueda vectorial (Chroma)
    embedding_pregunta = modelo.encode(pregunta).tolist()
    
    resultados_chroma = coleccion.query(
        query_embeddings=[embedding_pregunta],
        n_results=5
    )
    docs_vectoriales = set(resultados_chroma["documents"][0])

    # 2. Búsqueda BM25
    tokens_pregunta = pregunta.lower().split()
    scores_bm25 = bm25.get_scores(tokens_pregunta)
    top_indices = sorted(range(len(scores_bm25)),
                         key=lambda i: scores_bm25[i],
                         reverse=True)[:5]
    docs_bm25 = set ([documentos[i] for i in top_indices if scores_bm25[i] > 0])

    # 3. Fusión -unión de ambos resultados
    docs_combinados = docs_vectoriales | docs_bm25

    # 4. Filtrar por threshold vectorial
    docs_relevantes = [
        doc for doc, distancia in zip(
            resultados_chroma["documents"][0],
            resultados_chroma["distances"][0],
        )
        if distancia < THRESHOLD
    ] + [doc for doc in docs_bm25 if doc not in docs_vectoriales]
    
    return docs_relevantes [:5]

def rag_tool(coleccion, bm25, documentos, pregunta: str) -> str:
    """Tool para el agente — busqueda híbrida en descripciones reales de ofertas"""
    try:
        # coleccion ya viene como parámetro, no la inicialices aquí
        docs = buscar_ofertas_relevantes(coleccion, bm25, documentos, pregunta)
        
        if not docs:
            return "No encontré ofertas relevantes para esa pregunta"
        
        return "\n---\n".join(docs)
    except Exception as e:
        return f"Error al buscar en ofertas: {e}"


