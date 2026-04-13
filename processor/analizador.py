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
        "remoto": true/false,
        "ciudad": "ciudad si aparece, si no null",
        "pais": "país si aparece, si no null"
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


