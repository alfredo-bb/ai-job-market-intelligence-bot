from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

def es_pregunta_valida(pregunta: str) -> bool:
    """Verifica si la pregunta está relacionada con el mercado laboral"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system="You are a classifier. Answer only YES or NO.",
        messages=[{
            "role": "user",
            "content": f"Is this question related to job market, employment, skills, salaries, or technology careers? Question: '{pregunta}'"
        }]
    )

    resultado = response.content[0].text.strip().upper()
    return resultado == "YES"

def detectar_alucinacion(pregunta: str, respuesta: str, datos_reales: str) -> bool:
    """Detecta si la respuesta contiene información no respaldada por los datos"""
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system="You are a fact checker. Answer only YES or NO.",
        messages=[{
            "role": "user",
            "content": f"""Does this response contain information NOT supported by the data?
            
Data: {datos_reales}
Response: {respuesta}

Answer YES if the response contains invented facts not in the data. Answer NO if the response only uses the provided data."""
        }]
    )
    
    resultado = response.content[0].text.strip().upper()
    return resultado == "YES"