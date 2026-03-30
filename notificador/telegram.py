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
    
    def enviar_resumen(self, datos_españa: dict, datos_internacional: dict):
        
        def formatear_skills(skills: list) -> str:
            return "\n".join([
                f"  {i+1}. <b>{s['skill']}</b> → {s['total_ofertas']} ofertas"
                for i, s in enumerate(skills[:5])
            ])
        
        def formatear_salarios(salarios: list) -> str:
            if not salarios:
                return "  Sin datos suficientes"
            return "\n".join([
                f"  {i+1}. <b>{s['skill']}</b> → {s['salario']}"
                for i, s in enumerate(salarios[:3])
            ])
        
        mensaje = f"""
🤖 <b>Job Market Intelligence - Resumen Diario</b>

🇪🇸 <b>MERCADO ESPAÑA</b>
📊 Ofertas hoy: <b>{datos_españa['total_ofertas']}</b>
🔥 Top Skills:
{formatear_skills(datos_españa['skills'])}
💰 Skills mejor pagados:
{formatear_salarios(datos_españa['salarios'])}

🌍 <b>MERCADO INTERNACIONAL</b>
📊 Ofertas hoy: <b>{datos_internacional['total_ofertas']}</b>
🔥 Top Skills:
{formatear_skills(datos_internacional['skills'])}
💰 Skills mejor pagados:
{formatear_salarios(datos_internacional['salarios'])}
        """
        
        asyncio.run(self._enviar(mensaje))
    
    def enviar_alerta(self, mensaje: str):
        asyncio.run(self._enviar(f"⚠️ {mensaje}"))