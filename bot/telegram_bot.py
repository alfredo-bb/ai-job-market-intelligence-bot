import telegram
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def enviar_mensaje(texto: str):
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="HTML")

def enviar_resumen(total_ofertas: int, skills_top: list):
    # Construye el mensaje de resumen diario
    skills_texto = "\n".join([f"  {i+1}. <b>{s['skill']}</b> → {s['total_ofertas']} ofertas" 
                               for i, s in enumerate(skills_top[:5])])
    
    mensaje = f"""
🤖 <b>Job Market Intelligence - Resumen Diario</b>

📊 Ofertas analizadas hoy: <b>{total_ofertas}</b>

🔥 <b>Top 5 Skills más demandados:</b>
{skills_texto}
    """
    
    asyncio.run(enviar_mensaje(mensaje))


# TEST
if __name__ == "__main__":
    skills_prueba = [
        {"skill": "python", "total_ofertas": 45},
        {"skill": "sql", "total_ofertas": 38},
        {"skill": "aws", "total_ofertas": 22},
        {"skill": "dbt", "total_ofertas": 18},
        {"skill": "airflow", "total_ofertas": 15},
    ]
    enviar_resumen(total_ofertas=10, skills_top=skills_prueba)