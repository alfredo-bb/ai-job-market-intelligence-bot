from processor.analizador import analizar_oferta
from database.db import guardar_oferta, get_connection
from notificador.telegram import TelegramNotificador
from scraper.rss_scraper import obtener_todas_las_ofertas
from scraper.linkedin_scraper import obtener_ofertas_linkedin

def procesar_oferta(texto: str, url: str = None, fuente: str = None, mercado: str = None):
    print("🔍 Analizando oferta...")
    datos = analizar_oferta(texto)
    
    print("💾 Guardando en base de datos...")
    oferta_id = guardar_oferta(datos, texto, url, fuente, mercado)
    
    return oferta_id

def obtener_skills_por_mercado(mercado: str) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.skill, COUNT(*) as total_ofertas
            FROM skills_oferta s
            JOIN ofertas o ON s.oferta_id = o.id
            WHERE o.mercado = %s
            AND o.fecha_extraccion = CURRENT_DATE
            GROUP BY s.skill
            ORDER BY total_ofertas DESC
            LIMIT 5
        """, (mercado,))
        rows = cur.fetchall()
        return [{"skill": row[0], "total_ofertas": row[1]} for row in rows]
    finally:
        cur.close()
        conn.close()

def obtener_salarios_por_mercado(mercado: str) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.skill, o.salario, COUNT(*) as total
            FROM skills_oferta s
            JOIN ofertas o ON s.oferta_id = o.id
            WHERE o.mercado = %s
            AND o.salario IS NOT NULL
            AND o.fecha_extraccion = CURRENT_DATE
            GROUP BY s.skill, o.salario
            ORDER BY total DESC
            LIMIT 3
        """, (mercado,))
        rows = cur.fetchall()
        return [{"skill": row[0], "salario": row[1]} for row in rows]
    finally:
        cur.close()
        conn.close()

def obtener_total_por_mercado(mercado: str) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM ofertas
            WHERE mercado = %s
            AND fecha_extraccion = CURRENT_DATE
        """, (mercado,))
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    # Obtener ofertas de todas las fuentes
    print("📡 Obteniendo ofertas RSS...")
    ofertas_rss = obtener_todas_las_ofertas()
    
    print("📡 Obteniendo ofertas Google Jobs...")
    ofertas_google = obtener_ofertas_linkedin()
    
    todas = ofertas_rss + ofertas_google
    print(f"🎯 {len(todas)} ofertas encontradas en total")

    # Limitar a 30 ofertas por ejecución para no agotar el límite de Groq
    MAX_OFERTAS = 30
    todas = todas[:MAX_OFERTAS]
    print(f"⚙️ Procesando máximo {MAX_OFERTAS} ofertas por ejecución")

    # Procesar cada oferta
    procesadas = 0
    duplicadas = 0
    for oferta in todas:
        try:
            resultado = procesar_oferta(
                texto=oferta["descripcion"],
                url=oferta["url"],
                fuente=oferta["fuente"],
                mercado=oferta.get("mercado", "internacional")
            )
            if resultado:
                procesadas += 1
            else:
                duplicadas += 1
        except Exception as e:
            print(f"⚠️ Error procesando oferta, continuando: {e}")
            continue

    print(f"\n✅ Procesadas: {procesadas}")
    print(f"⚠️ Duplicadas ignoradas: {duplicadas}")

    # Obtener datos por mercado
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

    # Enviar resumen por Telegram
    notificador = TelegramNotificador()
    notificador.enviar_resumen(
        datos_españa=datos_españa,
        datos_internacional=datos_internacional
    )