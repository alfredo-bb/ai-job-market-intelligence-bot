import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.ext import CommandHandler
from agente_chat import responder
from dotenv import load_dotenv


load_dotenv()

# Historial por usuario
historiales = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """👋 *Bienvenido al AI Job Market Intelligence Bot*

Puedo ayudarte con:
📊 Skills más demandados en el mercado
💰 Qué tecnologías pagan más
🔍 Perfiles y requisitos de ofertas reales
🌍 Dónde buscar trabajo
🇪🇸 🌍 Ofertas de hoy en el mercado de España/Internacional

¿Qué quieres saber? I also speak English 🇬🇧

_Powered by real job market data + AI_"""

    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pregunta = update.message.text
    
    print(f"📩 [{user_id}]: {pregunta}")
    
    # Obtener o crear historial para este usuario
    if user_id not in historiales:
        historiales[user_id] = []
    
    # Responder
    respuesta, historiales[user_id] = responder(pregunta, historiales[user_id])
    
    await update.message.reply_text(respuesta, parse_mode="Markdown")

def main():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))  
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()