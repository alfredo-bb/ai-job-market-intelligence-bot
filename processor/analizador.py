from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analizar_oferta(texto_oferta: str) -> dict:
    prompt = f"""
    Analiza esta oferta de trabajo y extrae la información en formato JSON.
    
    Oferta:
    {texto_oferta}
    
    Devuelve SOLO un JSON con esta estructura, sin texto adicional:
    {{
        "puesto": "nombre del puesto",
        "skills_tecnicos": ["skill1", "skill2"],
        "lenguajes": ["Python", "SQL"],
        "herramientas_datos": ["dbt", "Airflow"],
        "cloud": ["AWS", "Azure"],
        "ia_ml": ["LangChain", "PyTorch"],
        "salario": "rango si aparece, si no null",
        "experiencia_anos": "años requeridos si aparece, si no null",
        "remoto": true/false
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    resultado = response.choices[0].message.content
    # Limpiar posibles backticks que añade el modelo
    resultado = resultado.strip()
    if resultado.startswith("```"):
        resultado = resultado.split("```")[1]
        if resultado.startswith("json"):
            resultado = resultado[4:]
    return json.loads(resultado.strip())


# TEST - oferta de prueba
if __name__ == "__main__":
    oferta_prueba = """
    Buscamos Data Engineer con experiencia en Python y SQL.
    Trabajarás con Airflow, dbt y Snowflake en un entorno cloud AWS.
    Se valora experiencia con LangChain y modelos LLM.
    Salario: 40.000 - 55.000€. Trabajo remoto. 3 años de experiencia.
    """
    
    resultado = analizar_oferta(oferta_prueba)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))