# Scraper via RSS - más estable que scraping HTML
# Las webs ofrecen RSS como forma oficial de consumir su contenido
import feedparser
import re
import os

# URLs de los feeds RSS que vamos a consumir
FEEDS = {
    # Mercado Internacional
    "remoteok": "https://remoteok.com/remote-jobs.rss",
    "weworkremotely": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    # Mercado España
    "infojobs_data_engineer": "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=data+engineer&rss=true",
    "infojobs_data_scientist": "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=data+scientist&rss=true",
    "infojobs_data_analyst": "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=data+analyst&rss=true",
}

# Clasificación de fuentes por mercado
MERCADO_ESPAÑA = ["infojobs_data_engineer", "infojobs_data_scientist", "infojobs_data_analyst"]
MERCADO_INTERNACIONAL = ["remoteok", "weworkremotely"]

KEYWORDS_OBLIGATORIAS = [
    # Inglés
    "data engineer", "data scientist", "data analyst", "machine learning",
    "ml engineer", "analytics engineer", "python", "llm", "ai engineer",
    "business intelligence", "data platform", "analytics","ai", "nlp",
    "rag", "gpt",
    
    # Español
    "ingeniero de datos", "científico de datos", "analista de datos",
    "aprendizaje automático", "inteligencia artificial", "análisis de datos",
    "ai", "ia", "nlp", "rag", "gpt"
]

KEYWORDS_EXCLUSION = [
    # Ingeniería no relacionada con datos
    "electrical", "mechanical", "hardware", "embedded", "c++",
    "eléctrico", "mecánico", "hardware",
    
    # Desarrollo web no relacionado
    "php developer", "ruby on rails", "wordpress", "shopify",
    
    # Otros perfiles claramente no relacionados
    "creative strategist", "copywriter", "graphic designer",
    "diseñador gráfico", "redactor", "community manager"
]

def limpiar_html(texto: str) -> str:
    """Elimina etiquetas HTML de la descripción"""
    texto = re.sub(r'<[^>]+>', ' ', texto)       # elimina etiquetas HTML
    texto = re.sub(r'\s+', ' ', texto)            # elimina espacios extra
    return texto.strip()

def es_oferta_relevante(titulo: str, descripcion: str) -> bool:
    """Filtra solo ofertas relacionadas con datos e IA"""
    texto = (titulo + " " + descripcion).lower()

    # Descarta si contiene keywords de exclusión
    if any(keyword in texto for keyword in KEYWORDS_EXCLUSION):
        return False
    
    # Acepta solo si contiene al menos una keyword obligatoria
    return any(keyword in texto for keyword in KEYWORDS_OBLIGATORIAS)

def extraer_ofertas(fuente: str, url: str) -> list:
    """Extrae ofertas de un feed RSS"""
    print(f"📡 Leyendo feed de {fuente}...")

    # Determina el mercado según la fuente
    mercado = "españa" if fuente in MERCADO_ESPAÑA else "internacional"
    
    feed = feedparser.parse(url, request_headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})
    ofertas = []
    
    for entry in feed.entries:
        titulo = entry.get("title", "")
        descripcion = limpiar_html(entry.get("summary", ""))  # limpia HTML
        link = entry.get("link", "")
        
        # Solo procesa ofertas relevantes
        if not es_oferta_relevante(titulo, descripcion):
            print(f"⏭️ Ignorada: {titulo}")
            continue
        
        ofertas.append({
            "titulo": titulo,
            "descripcion": descripcion,
            "url": link,
            "fuente": fuente,
            "mercado": mercado  
        })
        print(f"✅ Encontrada: {titulo}")
    
    print(f"📊 {fuente}: {len(ofertas)} ofertas relevantes encontradas")
    return ofertas

def obtener_todas_las_ofertas() -> list:
    """Obtiene ofertas de todos los feeds configurados"""
    todas = []
    for fuente, url in FEEDS.items():
        ofertas = extraer_ofertas(fuente, url)
        todas.extend(ofertas)
    return todas


