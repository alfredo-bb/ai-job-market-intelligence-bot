import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    # Usa DATABASE_URL si está disponible (Neon/producción), sino usa variables locales
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url, connect_timeout=10)
    else:
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
    
def limpiar_experiencia(valor) -> int:
    """Convierte valores como '3-8' o '3+' a un entero, si no puede devuelve None"""
    if valor is None:
        return None
    try:
        return int(valor)
    except (ValueError, TypeError):
        # Si es un rango como "3-8", coge el primer número
        try:
            return int(str(valor).split("-")[0].strip().replace("+", ""))
        except:
            return None
        
def guardar_oferta(datos: dict, descripcion: str, url: str = None, fuente: str = None,  mercado: str = None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ofertas (puesto, descripcion, salario, experiencia_anos, remoto, url, fuente, ciudad, pais, mercado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING  -- Si la URL ya existe, ignora
            RETURNING id
        """, (
            datos.get("puesto"),
            descripcion,
            datos.get("salario"),
            limpiar_experiencia(datos.get("experiencia_anos")),
            datos.get("remoto"),
            url,
            fuente,
            datos.get("ciudad"),
            datos.get("pais"),
            mercado
        ))

        resultado = cur.fetchone()
        if resultado is None:
            print(f"⚠️ Oferta duplicada, ignorada: {url}")
            return None
        
        oferta_id = resultado[0]

        # Insertar skills por categoría
        categorias = {
            "lenguajes": datos.get("lenguajes") or [],
            "herramientas_datos": datos.get("herramientas_datos") or [],
            "cloud": datos.get("cloud") or [],
            "ia_ml": datos.get("ia_ml") or []
        }

        for categoria, skills in categorias.items():
            for skill in skills:
                cur.execute("""
                    INSERT INTO skills_oferta (oferta_id, skill, categoria)
                    VALUES (%s, %s, %s)
                """, (oferta_id, skill, categoria))

        conn.commit()
        print(f"✅ Oferta guardada con ID: {oferta_id}")
        return oferta_id

    except Exception as e:
        conn.rollback()  # Si algo falla, deshace los cambios
        print(f"❌ Error guardando oferta: {e}")
        raise
    finally:
        cur.close()
        conn.close()  # Siempre se cierra, pase lo que pase

def cargar_ofertas_de_bbdd(mercado: str = None) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if mercado:
            cur.execute("""
                SELECT descripcion, url
                FROM ofertas
                WHERE mercado = %s
            """, (mercado,))
        else:
            cur.execute("""
                SELECT descripcion, url
                FROM ofertas
            """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def buscar_skills_demanda(mercado: str = None) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if mercado:
            cur.execute("""
                SELECT s.skill, COUNT(*) as total
                FROM skills_oferta s 
                JOIN ofertas o ON s.oferta_id = o.id
                WHERE o.mercado = %s
                GROUP BY s.skill
                ORDER BY total DESC
                LIMIT 5
            """, (mercado,))
        else:
            cur.execute("""
                SELECT s.skill, COUNT(*) as total
                FROM skills_oferta s
                GROUP BY s.skill
                ORDER BY total DESC
                LIMIT 5
            """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def buscar_salarios_por_skill(mercado: str = None) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if mercado:
            cur.execute("""
                SELECT skill, salario, COUNT(*) as total
                FROM skills_oferta s JOIN ofertas o
                ON s.oferta_id = o.id        
                WHERE o.salario IS NOT NULL AND o.mercado = %s
                GROUP BY skill, salario
                ORDER BY total
                LIMIT 5
            """, (mercado,))
        else:
            cur.execute("""
                SELECT skill, salario, COUNT(*) as total
                FROM skills_oferta s JOIN ofertas o
                ON s.oferta_id = o.id        
                WHERE o.salario IS NOT NULL 
                GROUP BY skill, salario
                ORDER BY total
                LIMIT 5
            """)
            
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def buscar_empresas_top(mercado: str = None) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if mercado:
            cur.execute("""
                SELECT fuente, COUNT(*) as total 
                FROM ofertas
                WHERE mercado = %s
                GROUP BY fuente
                ORDER BY total DESC
                LIMIT 5
            """, (mercado,))
        else:
            cur.execute("""
                SELECT fuente, COUNT(*) as total 
                FROM ofertas
                GROUP BY fuente
                ORDER BY total DESC
                LIMIT 5
            """)

        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def hay_ofertas_nuevas_hoy() -> bool:
    """Devuelve True si hay ofertas nuevas respecto a ayer"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) 
            FROM ofertas 
            WHERE DATE(fecha_extraccion) = CURRENT_DATE
            AND url NOT IN (
                SELECT url FROM ofertas 
                WHERE DATE(fecha_extraccion) = CURRENT_DATE - INTERVAL '1 day'
            )
        """)
        nuevas = cur.fetchone()[0]
        print(f"📊 Ofertas nuevas hoy: {nuevas}")
        return nuevas > 0
    finally:
        cur.close()
        conn.close()
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
    print(buscar_skills_demanda())
    print(buscar_salarios_por_skill())
    print(buscar_empresas_top())