# Implementación de Notificador para Telegram
# Para cambiar a Discord: crear discord.py heredando de Notificador
import telegram
import asyncio
import os
from dotenv import load_dotenv
from notificador.base import Notificador

load_dotenv()

class TelegramNotificador(Notificador):
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    async def _enviar(self, texto: str):
        bot = telegram.Bot(token=self.token)
        await bot.send_message(chat_id=self.chat_id, text=texto, parse_mode="HTML")
    
    def enviar_resumen(self, total_ofertas: int, skills_top: list):
        skills_texto = "\n".join([
            f"  {i+1}. <b>{s['skill']}</b> → {s['total_ofertas']} ofertas"
            for i, s in enumerate(skills_top[:5])
        ])
        
        mensaje = f"""
🤖 <b>Job Market Intelligence - Resumen Diario</b>

📊 Ofertas analizadas hoy: <b>{total_ofertas}</b>

🔥 <b>Top 5 Skills más demandados:</b>
{skills_texto}
        """
        asyncio.run(self._enviar(mensaje))
    
    def enviar_alerta(self, mensaje: str):
        asyncio.run(self._enviar(f"⚠️ {mensaje}"))