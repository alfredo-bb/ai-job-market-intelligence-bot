from processor.analizador import analizar_oferta
from database.db import guardar_oferta

def procesar_oferta(texto: str, url: str = None, fuente: str = None):
    print("🔍 Analizando oferta...")
    datos = analizar_oferta(texto)
    
    print("💾 Guardando en base de datos...")
    oferta_id = guardar_oferta(datos, texto, url, fuente)
    
    return oferta_id


# TEST
if __name__ == "__main__":
    oferta_prueba = """
    Buscamos Data Engineer con experiencia en Python y SQL.
    Trabajarás con Airflow, dbt y Snowflake en un entorno cloud AWS.
    Se valora experiencia con LangChain y modelos LLM.
    Salario: 40.000 - 55.000€. Trabajo remoto. 3 años de experiencia.
    """

    procesar_oferta(
        texto=oferta_prueba,
        url="https://linkedin.com/jobs/test",
        fuente="linkedin"
    )