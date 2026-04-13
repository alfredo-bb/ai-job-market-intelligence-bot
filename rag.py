from sentence_transformers import SentenceTransformer
import chromadb
from anthropic import Anthropic
from dotenv import load_dotenv
from database.db import cargar_ofertas_de_bbdd
import os

load_dotenv()

modelo = SentenceTransformer("all-MiniLM-L6-v2")
cliente_chroma = chromadb.Client()
THRESHOLD = 1.2

def inicializar_coleccion():
    """Carga ofertas de PostgreSQL e indexa en Chroma"""
    coleccion = cliente_chroma.create_collection("ofertas_trabajo")
    
    ofertas = cargar_ofertas_de_bbdd()
    
    documentos = [o[0] for o in ofertas if o[0]]
    ids = [f"doc_{i}" for i in range(len(documentos))]
    embeddings = modelo.encode(documentos).tolist()
    
    coleccion.add(
        documents=documentos,
        embeddings=embeddings,
        ids=ids
    )
    print(f"✅ {len(documentos)} ofertas indexadas en Chroma")
    return coleccion

def buscar_ofertas_relevantes(coleccion, pregunta: str) -> list:
    """Busca ofertas semánticamente similares a la pregunta"""
    embedding_pregunta = modelo.encode(pregunta).tolist()
    
    resultados = coleccion.query(
        query_embeddings=[embedding_pregunta],
        n_results=3
    )
    
    documentos_relevantes = [
        doc for doc, distancia in zip(resultados["documents"][0], resultados["distances"][0])
        if distancia < THRESHOLD
    ]
    
    return documentos_relevantes

def rag_tool(coleccion, pregunta: str) -> str:
    """Tool para el agente — busca en descripciones reales de ofertas"""
    try:
        # coleccion ya viene como parámetro, no la inicialices aquí
        documentos = buscar_ofertas_relevantes(coleccion, pregunta)
        
        if not documentos:
            return "No encontré ofertas relevantes para esa pregunta"
        
        return "\n---\n".join(documentos)
    except Exception as e:
        return f"Error al buscar en ofertas: {e}"


