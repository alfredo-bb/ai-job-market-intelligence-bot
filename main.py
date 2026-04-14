from pipeline_graph import construir_grafo
from processor.analizador import analizar_oferta
from database.db import guardar_oferta, get_connection
from notificador.telegram import TelegramNotificador
from scraper.rss_scraper import obtener_todas_las_ofertas
from scraper.linkedin_scraper import obtener_ofertas_linkedin
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor
from dotenv import load_dotenv
import os
import base64


#Inicializar Langfuse

load_dotenv()

pub = os.getenv("LANGFUSE_PUBLIC_KEY")
sec = os.getenv("LANGFUSE_SECRET_KEY")
token = base64.b64encode(f"{pub}:{sec}".encode()).decode()

os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://cloud.langfuse.com/api/public/otel"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {token}"

AnthropicInstrumentor().instrument()



def procesar_oferta(texto: str, url: str = None, fuente: str = None, mercado: str = None):
    print("🔍 Analizando oferta...")
    datos = analizar_oferta(texto)
    
    print("💾 Guardando en base de datos...")
    oferta_id = guardar_oferta(datos, texto, url, fuente, mercado)
    
    return oferta_id




if __name__ == "__main__":
    #Iniciamos el grafo
    pipeline = construir_grafo()
    estado_inicial = {
        "ofertas_scrapeadas": [],
        "ofertas_procesadas": [],
        "hay_ofertas_nuevas": False,
        "ofertas_suficientes": False,
        "ofertas_iguales_ayer": False,
        "errores_llm": 0,
        "ofertas_guardadas": 0,
        "ofertas_descartadas": 0
    }
    resultado = pipeline.invoke(estado_inicial)

