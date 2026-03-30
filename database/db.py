import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    # Usa DATABASE_URL si está disponible (Neon/producción), sino usa variables locales
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
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

# TEST
if __name__ == "__main__":
    datos_prueba = {
        "puesto": "Data Engineer",
        "lenguajes": ["Python", "SQL"],
        "herramientas_datos": ["dbt", "Airflow", "Snowflake"],
        "cloud": ["AWS"],
        "ia_ml": ["LangChain"],
        "salario": "40.000 - 55.000€",
        "experiencia_anos": 3,
        "remoto": True
    }

    guardar_oferta(
        datos=datos_prueba,
        descripcion="Oferta de prueba",
        url="https://linkedin.com/test",
        fuente="linkedin"
    )