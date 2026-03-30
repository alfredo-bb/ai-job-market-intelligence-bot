# Scraper de LinkedIn Jobs via SerpApi
# SerpApi gestiona los bloqueos y anti-detección por nosotros
from serpapi.google_search import GoogleSearch
import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Búsquedas que queremos hacer en LinkedIn
BUSQUEDAS = [
    "Data Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
    "Analytics Engineer",
    "Data Analyst"
]

# Países donde buscar
LOCALIZACIONES = [
    "Spain",
    "Remote"
]

def extraer_ofertas_linkedin(query: str, localizacion: str) -> list:
    """Extrae ofertas via Google Jobs (indexa LinkedIn y otras webs)"""
    print(f"🔍 Buscando '{query}' en '{localizacion}'...")
    
    params = {
        "engine": "google_jobs",
        "q": f"{query} {localizacion}",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    
    search = GoogleSearch(params)
    resultados = search.get_dict()
    
    ofertas = []
    for job in resultados.get("jobs_results", []):
        ofertas.append({
            "titulo": job.get("title", ""),
            "empresa": job.get("company_name", ""),
            "descripcion": job.get("description", ""),
            "url": job.get("share_link", ""),
            "ubicacion": job.get("location", ""),
            "fuente": "google_jobs"
        })
        print(f"✅ {job.get('title')} - {job.get('company_name')}")
    
    print(f"📊 '{query}' en '{localizacion}': {len(ofertas)} ofertas")
    return ofertas

def obtener_ofertas_linkedin() -> list:
    """Obtiene ofertas de LinkedIn para todas las búsquedas configuradas"""
    todas = []
    for query in BUSQUEDAS:
        for localizacion in LOCALIZACIONES:
            ofertas = extraer_ofertas_linkedin(query, localizacion)
            todas.extend(ofertas)
    return todas


# TEST
if __name__ == "__main__":
    ofertas = obtener_ofertas_linkedin()
    print(f"\n🎯 Total ofertas LinkedIn: {len(ofertas)}")
    for o in ofertas[:3]:
        print(f"\n--- {o['titulo']} ---")
        print(f"Empresa: {o['empresa']}")
        print(f"Ubicación: {o['ubicacion']}")