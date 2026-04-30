from __future__ import annotations

import re

class InputNormalizer:
    """
    Pilar 1: Preprocesamiento y Limpieza de Datos
    Se encarga de limpiar y normalizar el texto antes de segmentarlo.
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        
        # Eliminar caracteres nulos o no imprimibles básicos
        text = text.replace("\x00", "")
        
        # Reemplazar múltiples saltos de línea por un doble salto de línea (separador de párrafo lógico)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Reemplazar múltiples espacios por uno solo
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalizar comillas y caracteres tipográficos
        text = text.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
        
        # TODO: Aquí se integrarían adaptadores OCR para tablas y extractores semánticos
        
        return text.strip()
