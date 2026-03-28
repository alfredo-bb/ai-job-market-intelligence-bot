from processor.analizador import analizar_oferta
from database.db import guardar_oferta, get_connection
from notificador.telegram import TelegramNotificador
from scraper.rss_scraper import obtener_todas_las_ofertas

def procesar_oferta(texto: str, url: str = None, fuente: str = None):
    print("🔍 Analizando oferta...")
    datos = analizar_oferta(texto)
    
    print("💾 Guardando en base de datos...")
    oferta_id = guardar_oferta(datos, texto, url, fuente)
    
    return oferta_id

def obtener_skills_top():
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


if __name__ == "__main__":
    # Obtener ofertas reales del RSS
    print("📡 Obteniendo ofertas de los feeds RSS...")
    ofertas = obtener_todas_las_ofertas()
    print(f"🎯 {len(ofertas)} ofertas encontradas")

    # Procesar cada oferta
    procesadas = 0
    duplicadas = 0
    for oferta in ofertas:
        resultado = procesar_oferta(
            texto=oferta["descripcion"],
            url=oferta["url"],
            fuente=oferta["fuente"]
        )
        if resultado:
            procesadas += 1
        else:
            duplicadas += 1

    print(f"\n✅ Procesadas: {procesadas}")
    print(f"⚠️ Duplicadas ignoradas: {duplicadas}")

    # Enviar resumen por Telegram
    skills_top = obtener_skills_top()
    total_hoy = obtener_total_ofertas_hoy()
    notificador = TelegramNotificador()
    notificador.enviar_resumen(total_ofertas=total_hoy, skills_top=skills_top)