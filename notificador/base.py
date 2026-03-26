# Clase abstracta que define el contrato que todo notificador debe cumplir
# Si mañana queremos añadir Discord o Email, solo hay que heredar de esta clase
from abc import ABC, abstractmethod

class Notificador(ABC):
    
    @abstractmethod
    def enviar_resumen(self, total_ofertas: int, skills_top: list):
        """Envía el resumen diario de ofertas y skills"""
        pass
    
    @abstractmethod
    def enviar_alerta(self, mensaje: str):
        """Envía un mensaje puntual o alerta"""
        pass