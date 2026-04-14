from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator
from scraper.rss_scraper import obtener_todas_las_ofertas
from scraper.linkedin_scraper import obtener_ofertas_linkedin
from notificador.telegram import TelegramNotificador
from processor.analizador import analizar_oferta
from database.db import guardar_oferta
from database.db import hay_ofertas_nuevas_hoy
import subprocess
from database.db import obtener_skills_por_mercado, obtener_salarios_por_mercado, obtener_total_por_mercado
from langgraph.graph import StateGraph, END



class PipelineState(TypedDict):
    ofertas_scrapeadas: list #ofertas crudas del scraper
    ofertas_procesadas: list #ofertas analizadas por LLM
    hay_ofertas_nuevas: bool #¿hay algo nuevo?
    ofertas_suficientes: bool #¿más de 10 ofertas?
    ofertas_iguales_ayer: bool #¿mismo resumen que ayer?
    errores_llm: int #contador de fallos LLM
    ofertas_guardadas: int #contador de guardadas
    ofertas_descartadas: int #contador de descartadas


def nodo_scraper (state: PipelineState) -> PipelineState:
    """Extrae ofertas de todas las fuentes"""
    print("📡 Scrapeando ofertas...")

    ofertas_rss = obtener_todas_las_ofertas()
    ofertas_google = obtener_ofertas_linkedin()
    todas = ofertas_rss + ofertas_google

    print(f"🎯 {len(todas)} ofertas encontradas")

    return {
        **state,
        "ofertas_scrapeadas": todas,
        "hay_ofertas_nuevas": len(todas) > 0,
        "ofertas_suficientes": len(todas) > 10        
    }

def decidir_si_continuar(state: PipelineState) -> str:
    """Decide si continuar con el pipeline o continuar"""
    if not state ["hay_ofertas_nuevas"]:
        print("⏹️ No hay ofertas nuevas. Terminando.")
        return "end"
    return "continuar"

def nodo_alerta_pocas_ofertas(state: PipelineState) -> PipelineState:
    """Envia alerta si hay pocas ofertas"""
    if not state["ofertas_suficientes"]:
        print("⚠️ Pocas ofertas detectadas, enviando alerta...")
        notificador = TelegramNotificador()
        notificador.enviar_alerta(
            f"⚠️ Solo {len(state['ofertas_scrapeadas'])} ofertas encontradas hoy. Posible fallo en scrapers."
        )
    return state

def nodo_analizar_ofertas(state: PipelineState) -> PipelineState:
    """Analiza cada oferta con LLM y valida calidad"""
    procesadas = []
    descartadas = 0
    errores = 0

    MAX_OFERTAS = 30
    ofertas = state["ofertas_scrapeadas"][:MAX_OFERTAS]

    for oferta in ofertas:
        try:
            datos = analizar_oferta(oferta["descripcion"])

            #validar calidad
            if not datos.get("puesto"):
                descartadas += 1
                continue
            
            skills = (datos.get("lenguajes") or []) + \
                     (datos.get("ia_ml") or []) + \
                     (datos.get("herramientas_datos") or [])
            
            if len(oferta["descripcion"]) < 100 or len(skills) == 0:
                descartadas += 1
                continue
            
            procesadas.append({
                "datos": datos,
                "oferta": oferta
            })
            
        except Exception as e:
            errores += 1
            print(f"⚠️ Error LLM: {e}")
            continue
    
    print(f"✅ Procesadas: {len(procesadas)} | Descartadas: {descartadas} | Errores: {errores}")
    
    return {
        **state,
        "ofertas_procesadas": procesadas,
        "errores_llm": errores,
        "ofertas_descartadas": descartadas
    }

def decidir_si_guardar(state: PipelineState) -> str:
    """Decide si guardar ofertas o terminar por ser iguales a ayer"""
    if len(state["ofertas_procesadas"]) == 0:
        print("⏹️ No hay ofertas de calidad. Terminando.")
        return "end"
    return "continuar"

def nodo_guardar_ofertas(state: PipelineState) -> PipelineState:
    """Guarda ofertas procesadas en PostgreSQL"""
    guardadas = 0
    
    for item in state["ofertas_procesadas"]:
        try:
            resultado = guardar_oferta(
                datos=item["datos"],
                descripcion=item["oferta"]["descripcion"],
                url=item["oferta"]["url"],
                fuente=item["oferta"]["fuente"],
                mercado=item["oferta"].get("mercado", "internacional")
            )
            if resultado:
                guardadas += 1
        except Exception as e:
            print(f"⚠️ Error guardando: {e}")
            continue
    
    print(f"💾 Guardadas en BD: {guardadas}")
    
    return {
        **state,
        "ofertas_guardadas": guardadas
    }

def decidir_si_enviar_resumen(state: PipelineState) -> str:
    """Decide si enviar resumen o terminar por no haber cambios"""
    if not hay_ofertas_nuevas_hoy():
        print("⏹️ No hay ofertas nuevas respecto a ayer. No se envía resumen.")
        return "end"
    return "continuar"



def nodo_transformar_dbt(state: PipelineState) -> PipelineState:
    """Ejecuta dbt para transformar los datos"""
    print("🔄 Ejecutando dbt...")
    try:
        subprocess.run(["dbt", "run", "--project-dir", "transform"], 
                      check=True, capture_output=True)
        print("✅ dbt ejecutado correctamente")
    except Exception as e:
        print(f"⚠️ Error en dbt: {e}")
    return state

def nodo_enviar_telegram(state: PipelineState) -> PipelineState:
    """Envía resumen diario por Telegram"""
    print("📱 Enviando resumen por Telegram...")
    
    datos_españa = {
        "total_ofertas": obtener_total_por_mercado("españa"),
        "skills": obtener_skills_por_mercado("españa"),
        "salarios": obtener_salarios_por_mercado("españa")
    }
    datos_internacional = {
        "total_ofertas": obtener_total_por_mercado("internacional"),
        "skills": obtener_skills_por_mercado("internacional"),
        "salarios": obtener_salarios_por_mercado("internacional")
    }
    
    notificador = TelegramNotificador()
    notificador.enviar_resumen(
        datos_españa=datos_españa,
        datos_internacional=datos_internacional
    )
    
    return state

def construir_grafo():
    grafo = StateGraph(PipelineState)

    # Añadir nodos
    grafo.add_node("scraper", nodo_scraper)
    grafo.add_node("alerta_pocas_ofertas", nodo_alerta_pocas_ofertas)
    grafo.add_node("analizar_ofertas", nodo_analizar_ofertas)
    grafo.add_node("guardar_ofertas", nodo_guardar_ofertas)
    grafo.add_node("transformar_dbt", nodo_transformar_dbt)
    grafo.add_node("enviar_telegram", nodo_enviar_telegram)

    # Punto de entrada
    grafo.set_entry_point("scraper")

    # Edge condicional 1 -¿hay ofertas nuevas?
    grafo.add_conditional_edges(
        "scraper",
        decidir_si_continuar,
        {
            "end": END,
            "continuar": "alerta_pocas_ofertas"
        }
    )

    # Edge normal -siempre analiza despues de la alerta
    grafo.add_edge("alerta_pocas_ofertas", "analizar_ofertas")

    # Edge condicional 2- ¿hay ofertas de calidad?
    grafo.add_conditional_edges(
        "analizar_ofertas",
        decidir_si_guardar,
        {
            "end": END,
            "continuar": "guardar_ofertas"
        }
    )

    # Edge condicional 3 — ¿hay ofertas nuevas respecto a ayer?
    grafo.add_conditional_edges(
        "guardar_ofertas",
        decidir_si_enviar_resumen,
        {
            "end": END,
            "continuar": "transformar_dbt"
        }
    )

    # Edges normales finales
    grafo.add_edge("transformar_dbt", "enviar_telegram")
    grafo.add_edge("enviar_telegram", END)
    
    return grafo.compile()

if __name__ == "__main__":
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
    print(f"\n✅ Pipeline completado")
    print(f"Guardadas: {resultado['ofertas_guardadas']}")
    print(f"Descartadas: {resultado['ofertas_descartadas']}")
    print(f"Errores LLM: {resultado['errores_llm']}")


