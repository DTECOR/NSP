"""
Módulo para extraer información de versión TiMOS de los equipos Nokia.
"""

import re

def extraer_version_timos(bloque):
    """
    Extrae la versión TiMOS completa y la versión principal del bloque de texto.
    Compatible con múltiples formatos de NSP.
    
    Args:
        bloque (str): Bloque de texto del equipo
        
    Returns:
        tuple: (timos_version_completa, main_version)
    """
    # Patrones para buscar versión TiMOS en diferentes formatos
    patrones = [
        # Patrón estándar para "show version"
        r'TiMOS-[A-Z]-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón alternativo que puede aparecer en algunos equipos
        r'TiMOS-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones con formato diferente
        r'TiMOS.*?(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato simple
        r'[Vv]ersion\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de sistema
        r'System\s+[Vv]ersion\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de software
        r'Software\s+[Vv]ersion\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de TiMOS
        r'TiMOS.*?version\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de SROS
        r'SROS.*?version\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de SR OS
        r'SR\s+OS.*?version\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de SR
        r'SR.*?version\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión
        r'[Vv]ersion\s*:?\s*TiMOS-[A-Z]-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión sin prefijo
        r'[Vv]ersion\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de build
        r'[Bb]uild\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de release
        r'[Rr]elease\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de software release
        r'[Ss]oftware\s+[Rr]elease\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de TiMOS release
        r'TiMOS\s+[Rr]elease\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de SROS release
        r'SROS\s+[Rr]elease\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de SR OS release
        r'SR\s+OS\s+[Rr]elease\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de SR release
        r'SR\s+[Rr]elease\s*:?\s*(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo
        r'[Vv]ersion\s*:?\s*TiMOS-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo SROS
        r'[Vv]ersion\s*:?\s*SROS-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo SR OS
        r'[Vv]ersion\s*:?\s*SR\s+OS-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo SR
        r'[Vv]ersion\s*:?\s*SR-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS
        r'[Vv]ersion\s*:?\s*TiMOS\s+(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo SROS
        r'[Vv]ersion\s*:?\s*SROS\s+(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo SR OS
        r'[Vv]ersion\s*:?\s*SR\s+OS\s+(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo SR
        r'[Vv]ersion\s*:?\s*SR\s+(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-C
        r'[Vv]ersion\s*:?\s*TiMOS-C-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-B
        r'[Vv]ersion\s*:?\s*TiMOS-B-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-A
        r'[Vv]ersion\s*:?\s*TiMOS-A-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-D
        r'[Vv]ersion\s*:?\s*TiMOS-D-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-L
        r'[Vv]ersion\s*:?\s*TiMOS-L-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-M
        r'[Vv]ersion\s*:?\s*TiMOS-M-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-X
        r'[Vv]ersion\s*:?\s*TiMOS-X-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-U
        r'[Vv]ersion\s*:?\s*TiMOS-U-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-S
        r'[Vv]ersion\s*:?\s*TiMOS-S-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-R
        r'[Vv]ersion\s*:?\s*TiMOS-R-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-T
        r'[Vv]ersion\s*:?\s*TiMOS-T-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-I
        r'[Vv]ersion\s*:?\s*TiMOS-I-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-E
        r'[Vv]ersion\s*:?\s*TiMOS-E-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-F
        r'[Vv]ersion\s*:?\s*TiMOS-F-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-G
        r'[Vv]ersion\s*:?\s*TiMOS-G-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-H
        r'[Vv]ersion\s*:?\s*TiMOS-H-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-J
        r'[Vv]ersion\s*:?\s*TiMOS-J-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-K
        r'[Vv]ersion\s*:?\s*TiMOS-K-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-N
        r'[Vv]ersion\s*:?\s*TiMOS-N-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-O
        r'[Vv]ersion\s*:?\s*TiMOS-O-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-P
        r'[Vv]ersion\s*:?\s*TiMOS-P-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-Q
        r'[Vv]ersion\s*:?\s*TiMOS-Q-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-V
        r'[Vv]ersion\s*:?\s*TiMOS-V-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-W
        r'[Vv]ersion\s*:?\s*TiMOS-W-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-Y
        r'[Vv]ersion\s*:?\s*TiMOS-Y-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón para versiones en formato de línea de versión con prefijo TiMOS-Z
        r'[Vv]ersion\s*:?\s*TiMOS-Z-(\d+\.\d+\.[A-Z]\d+)',
        # Patrón más general para capturar cualquier secuencia de dígitos y puntos que parezca una versión
        r'(\d+\.\d+(?:\.\d+)?(?:\.[A-Z]\d+)?)'
    ]
    
    # Buscar versión TiMOS usando los patrones
    timos_version_completa = None
    for patron in patrones:
        match = re.search(patron, bloque)
        if match:
            timos_version_completa = match.group(1)
            break
    
    # Si no se encontró versión, devolver None
    if not timos_version_completa:
        return None, None
    
    # Extraer versión principal (major.minor) si timos_version_completa fue encontrada
    main_version = None
    main_match = re.match(r'(\d+\.\d+)', timos_version_completa)
    if main_match:
        main_version = main_match.group(1)
    
    return timos_version_completa, main_version

def extraer_tipo_equipo_desde_version(bloque):
    """
    Extrae el tipo de equipo desde el bloque de versión.
    
    Args:
        bloque (str): Bloque de texto del equipo
        
    Returns:
        str: Tipo de equipo o None si no se puede determinar
    """
    # Patrones para buscar tipo de equipo en diferentes formatos
    patrones = [
        # Patrón para "for 7750 SR"
        r'for\s+(\d{4}\s+\w+(?:-\w+)?))',
        # Patrón para "Nokia 7750 SR"
        r'Nokia\s+(\d{4}\s+\w+(?:-\w+)?))',
        # Patrón para "7750 SR"
        r'(\d{4}\s+\w+(?:-\w+)?))',
        # Patrón para "7750-SR"
        r'(\d{4}-\w+(?:-\w+)?))',
        # Patrón para "7750SR"
        r'(\d{4}\w+(?:-\w+)?))',
    ]
    
    # Buscar tipo de equipo usando los patrones
    for patron in patrones:
        match = re.search(patron, bloque)
        if match:
            return match.group(1)
    
    # Si no se encontró tipo de equipo, intentar extraer solo el número de modelo
    modelo_match = re.search(r'(?:^|\s)(\d{4})(?:\s|$)', bloque)
    if modelo_match:
        return modelo_match.group(1)
    
    return None


