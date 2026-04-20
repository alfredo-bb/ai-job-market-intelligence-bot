from anthropic import Anthropic
from dotenv import load_dotenv
from database.db import buscar_skills_demanda
from database.db import buscar_empresas_top
from database.db import buscar_salarios_por_skill
from rag import rag_tool, inicializar_coleccion
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor 
from dotenv import load_dotenv
import os
import base64
from semantic_cache import buscar_en_cache, guardar_en_cache
from guardrails import es_pregunta_valida, detectar_alucinacion

load_dotenv()
client = Anthropic()

#Inicializa Langfuse

pub = os.getenv("LANGFUSE_PUBLIC_KEY")
sec = os.getenv("LANGFUSE_SECRET_KEY")
token = base64.b64encode(f"{pub}:{sec}".encode()).decode()

os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://cloud.langfuse.com/api/public/otel"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {token}"

AnthropicInstrumentor().instrument()

#Define el prompt

SYSTEM_PROMPT = """Eres un agente especializado en análisis del mercado laboral de datos e IA.
                Tienes acceso a una base de datos real con ofertas de trabajo actuales.

                INSTRUCCIONES CRÍTICAS:
            
                - Responde ÚNICAMENTE a lo que el usuario pregunta. No añadas comparaciones no solicitadas.
                - Elige la tool más específica para cada pregunta:
                    * Preguntas sobre demanda o qué aprender → buscar_skills_demanda
                    * Preguntas sobre salarios o qué paga más → buscar_salarios_por_skill
                    * Preguntas sobre dónde buscar trabajo → buscar_empresas_top
                - Si preguntan por un mercado específico, filtra por ese mercado
                - Si no especifican mercado, usa datos globales sin filtro
                - Sé conciso y directo. Máximo 5 líneas de respuesta."""

#Define la tool
tools = [
    {
        "name":"buscar_skills_demanda",
        "description": "Devuelve los skills más demandados en ofertas de trabajo. Puede filtrar por mercado españa o internacional",
        "input_schema": {
            "type": "object",
            "properties": {
                "mercado": {
                    "type": "string",
                    "enum": ["españa", "internacional"],
                    "description": "Filtrar por mercado. Si no se especifica devuelve datos globales"
                }
            },
            "required": []
        }
    },

    {
        "name":"buscar_empresas_top",
        "description": "Devuelve las plataformas y webs donde hay más ofertas de trabajo. Úsala cuando pregunten dónde buscar empleo, qué plataformas usar, o dónde hay más trabajo disponible",
        "input_schema": {
            "type": "object",
            "properties": {
                "mercado": {
                    "type": "string",
                    "enum": ["españa", "internacional"],
                    "description": "Filtrar por mercado. Si no se especifica devuelve datos globales"
                }
            },
            "required": []
        }
    },

    {
        "name":"buscar_salarios_por_skill",
        "description": "Devuelve las skills que pagan más y los salarios que pagan",
        "input_schema": {
            "type": "object",
            "properties": {
                "mercado": {
                    "type": "string",
                    "description": "Devuelve las skills que pagan más y los salarios que pagan"
                }
            },
            "required": []
        }
    },
    {
    "name": "buscar_en_descripciones",
    "description": "Busca en el texto completo de descripciones de ofertas reales. Úsala cuando pregunten por perfiles específicos, requisitos detallados o tecnologías concretas que buscan las empresas",
    "input_schema": {
        "type": "object",
        "properties": {
            "pregunta": {
                "type": "string",
                "description": "La pregunta o tecnología a buscar en las descripciones"
            }
        },
        "required": ["pregunta"]
    }
}



]

#2. Función real que ejecuta la tool

def buscar_skills_demanda_tool(mercado: str = None) -> str:
    try:
        resultados = buscar_skills_demanda(mercado)
        if not resultados:
            return "No hay datos disponibles"
        
        lineas = [f"{skill}: {total} ofertas" for skill, total in resultados]
        return "\n".join(lineas)
    except Exception as e:
        return f"Error al consultar la base de datos: {e}"

def buscar_empresas_top_tool(mercado: str = None) -> str:
    try:
        resultados = buscar_empresas_top(mercado)
        if not resultados:
            return "No hay datos disponibles"
        
        lineas = [f"{empresa}: {total} ofertas" for empresa, total in resultados]
        return "\n".join(lineas)
    except Exception as e:
        return f"Error al consultar la base de datos: {e}"

def buscar_salarios_por_skill_tool(mercado: str = None) -> str:
    try:

        resultados = buscar_salarios_por_skill(mercado)
        if not resultados:
            return "No hay datos disponibles"
        
        lineas = [f"{skill}: {salario}" for skill, salario, total in resultados]
        return "\n".join(lineas)
    except Exception as e:
        return f"Error al consultar la base de datos: {e}"
    

#Se ejecuta cuando se necesita
coleccion_chroma = None
bm25 = None
documentos = None

def obtener_coleccion():
    global coleccion_chroma, bm25, documentos
    if coleccion_chroma is None:
        print("🔄 Iniciando colección ChromaDB...")
        coleccion_chroma, bm25, documentos = inicializar_coleccion()
        print("✅ Colección lista")
    return coleccion_chroma, bm25, documentos


tools_functions = {
    "buscar_skills_demanda": buscar_skills_demanda_tool,
    "buscar_empresas_top": buscar_empresas_top_tool,
    "buscar_salarios_por_skill": buscar_salarios_por_skill_tool,
    "buscar_en_descripciones": lambda pregunta: rag_tool(*obtener_coleccion(), pregunta)
}

def responder(pregunta: str, historial: list) -> tuple[str, list]:
    
    # Salida especial
    if pregunta.lower() == "salir":
        return "👋 ¡Hasta luego!", historial

    # 0 Guardrail -verificar si la pregunta es válida
    if not es_pregunta_valida(pregunta):
        respuesta= "Lo siento, sólo puedo responder preguntas sobre el mercado laboral, empleos, skills y tecnologías."
        historial.append({"role": "user", "content": pregunta})
        historial.append({"role": "assistant", "content": pregunta})
        return respuesta, historial
    
    # 1. Comprobar cache primero
    respuesta_cacheada = buscar_en_cache(pregunta)
    if respuesta_cacheada:
        # 1.1. Añadir pregunta al historial
        historial.append({"role": "user", "content": pregunta})
        historial.append({"role": "assistant", "content": respuesta_cacheada})
        return respuesta_cacheada, historial
    
    # 2. Si no hay cache - lógica normal
    historial.append({"role": "user", "content": pregunta})
    
    # 3. Primera llamada
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        tools=tools,
        messages=historial,
        system=SYSTEM_PROMPT
    )
    
    # 4. Procesar tools si las hay
    historial.append({"role": "assistant", "content": response.content})
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            # obtener la función correspondiente
            tool_function = tools_functions.get(block.name)

            # ejecutar la tool 
            resultado = tool_function(**block.input)

            #acumular el resultado
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": resultado
            })
    
    # 5. Si hubo tools, segunda llamada
    if tool_results:
        historial.append({"role": "user", "content": tool_results})
        response_final = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            tools=tools,
            messages=historial,
            system=SYSTEM_PROMPT)
    else:
        response_final = response
    
    respuesta= response_final.content[0].text

    
    
    # 6. Guardar respuesta y devolver
    respuesta = response_final.content[0].text

    # 7. Detectar alucinación
    tool_data = "\n".join([r["content"] for r in tool_results])
    if detectar_alucinacion(pregunta, respuesta, tool_data):
        respuesta = "No tengo datos suficientes para responder con seguridad."

    historial.append({"role": "assistant", "content": respuesta})

    # Limitar historial a los últimos 10 mensajes
    if len(historial) > 10:
        historial = historial[-10:]

    # 8. Guardar respuesta en cache antes de devolver
    guardar_en_cache(pregunta, respuesta)
    return respuesta, historial

if __name__ == "__main__":
    historial = []
  
    print("🤖 Agente local. Escribe 'salir' para terminar.\n")

    try:
        while True:
            user_input = input("Tú: ")
            if user_input.lower() == "salir":
                break
            respuesta, historial = responder(user_input, historial)
            print(f"\nAgente: {respuesta}\n")
    
    except KeyboardInterrupt:
        print("\n👋 Hasta luego.")
