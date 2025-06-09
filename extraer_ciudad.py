"""
Módulo para extraer y normalizar nombres de ciudades a partir de nombres de equipos.
Soporta múltiples formatos y casos especiales de nomenclatura.
"""

import re

# Diccionario de equivalencias de códigos de ciudades
EQUIVALENCIAS_CIUDADES = {
    # Códigos proporcionados por el usuario
    'ATL': 'Atlántico',
    'BQL': 'Barranquilla',
    'BAR': 'Barranquilla',
    'BTA': 'Bogotá',
    'CAR': 'Cartagena',
    'CLI': 'Cali',
    'COL': 'Colombia',
    'IBG': 'Ibagué',
    'MTR': 'Montería',
    'NAR': 'Nariño',
    'PAL': 'Palmira',
    'PAN': 'Panamá',
    'SAT': 'Santa Marta',
    'VAC': 'Valledupar',
    'VVC': 'Villavicencio',
    
    # Códigos estándar existentes
    'BAQ': 'Barranquilla',
    'BGA': 'Bucaramanga',
    'BOG': 'Bogotá',
    'CAL': 'Cali',
    'CLO': 'Cali',
    'CTG': 'Cartagena',
    'CUC': 'Cúcuta',
    'IBE': 'Ibagué',
    'MON': 'Montería',
    'PPN': 'Popayán',
    'SBL': 'Sincelejo',
    'SIN': 'Sincelejo',
    'BUC': 'Bucaramanga',
    
    # Casos especiales mencionados explícitamente
    'PAS': 'Pasto',
    'SMA': 'Santa Marta',
    'SMT': 'Santa Marta',
    'VDP': 'Valledupar',
    'VUP': 'Valledupar',
    
    # Otros códigos comunes
    'MED': 'Medellín',
    'PER': 'Pereira',
    'MAN': 'Manizales',
    'VIL': 'Villavicencio',
    'NEI': 'Neiva',
    'ARM': 'Armenia',
    'POP': 'Popayán',
    'VAL': 'Valledupar',
    'TUN': 'Tunja',
    'BUE': 'Buenaventura',
    'QUI': 'Quibdó',
    'RIO': 'Riohacha',
    'YOP': 'Yopal',
    'FLO': 'Florencia',
    'MOC': 'Mocoa',
    'LET': 'Leticia',
    'MIT': 'Mitú',
    'PTO': 'Puerto Carreño',
    'INI': 'Inírida',
    'SJG': 'San José del Guaviare',
}

def extraer_ciudad_desde_nombre_equipo(nombre_equipo):
    """
    Extrae el código de ciudad desde el nombre del equipo, soportando múltiples formatos:
    1. Con guión bajo: "XXX_YYY_ZZZ" (donde XXX es el código de ciudad)
    2. Con números directamente: "XXXNNNN" (como CAL0284)
    3. Con prefijo WOM: "WOM_XXX_NNNN" (como WOM_VDP_03338)
    
    Args:
        nombre_equipo (str): Nombre del equipo
        
    Returns:
        str: Código de ciudad extraído o None si no se puede extraer
    """
    if not nombre_equipo or not isinstance(nombre_equipo, str):
        return None
    
    # Limpiar el nombre del equipo
    nombre_equipo = nombre_equipo.strip().upper()
    
    # Caso especial: WOM sin ciudad
    if nombre_equipo == 'WOM':
        return 'WOM'
    
    # Caso especial: Prefijo WOM (WOM_VDP_03338)
    if nombre_equipo.startswith('WOM_'):
        partes = nombre_equipo.split('_')
        if len(partes) > 1 and len(partes[1]) == 3:  # El código de ciudad suele tener 3 letras
            return partes[1]
        return 'WOM'  # Si no hay ciudad identificable después de WOM_
    
    # Formato 1: Con guión bajo (XXX_YYY_ZZZ)
    if '_' in nombre_equipo:
        partes = nombre_equipo.split('_')
        if partes and len(partes[0]) == 3:  # El código de ciudad suele tener 3 letras
            return partes[0]
    
    # Formato 2: Con números directamente (XXXNNNN)
    # Buscar un patrón de 3 letras seguidas de números
    match = re.match(r'^([A-Z]{3})\d+', nombre_equipo)
    if match:
        return match.group(1)
    
    # Si no se pudo extraer con ninguno de los métodos anteriores
    return None

def normalizar_ciudad(codigo_ciudad):
    """
    Normaliza el código de ciudad a un nombre completo.
    
    Args:
        codigo_ciudad (str): Código de ciudad (3 letras)
        
    Returns:
        str: Nombre completo de la ciudad o mensaje de error para casos especiales
    """
    if not codigo_ciudad:
        return None
    
    codigo_ciudad = codigo_ciudad.strip().upper()
    
    # Caso especial: WOM sin ciudad
    if codigo_ciudad == 'WOM':
        return "Error en hostname, verificar"
    
    # Buscar en el diccionario de equivalencias
    return EQUIVALENCIAS_CIUDADES.get(codigo_ciudad, codigo_ciudad)
