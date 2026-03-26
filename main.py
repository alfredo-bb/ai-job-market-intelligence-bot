from processor.analizador import analizar_oferta
from database.db import guardar_oferta, get_connection
from notificador.telegram import TelegramNotificador

def procesar_oferta(texto: str, url: str = None, fuente: str = None):
    print("🔍 Analizando oferta...")
    datos = analizar_oferta(texto)
    
    print("💾 Guardando en base de datos...")
    oferta_id = guardar_oferta(datos, texto, url, fuente)
    
    return oferta_id

def obtener_skills_top():
    # Lee los skills más demandados de Neon
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT skill, COUNT(*) as total_ofertas
            FROM skills_oferta
            GROUP BY skill
            ORDER BY total_ofertas DESC
            LIMIT 5
        """)
        rows = cur.fetchall()
        return [{"skill": row[0], "total_ofertas": row[1]} for row in rows]
    finally:
        cur.close()
        conn.close()

def obtener_total_ofertas_hoy():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM ofertas
            WHERE fecha_extraccion = CURRENT_DATE
        """)
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()


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

    # Enviar resumen por Telegram con datos reales de Neon
    skills_top = obtener_skills_top()
    total_hoy = obtener_total_ofertas_hoy()
    notificador = TelegramNotificador()
    notificador.enviar_resumen(total_ofertas=total_hoy, skills_top=skills_top)