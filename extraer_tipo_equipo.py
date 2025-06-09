"""
Módulo para extraer el tipo de equipo Nokia desde el comando 'show chassis'.
"""

import re

def extraer_tipo_equipo_desde_chassis(bloque):
    """
    Extrae el tipo de equipo Nokia desde el bloque de texto del comando 'show chassis'.
    Solo considera válidos los tipos que comienzan con '7' seguido de tres dígitos.
    
    Args:
        bloque (str): Bloque de texto del equipo
        
    Returns:
        str: Tipo de equipo Nokia o None si no se encuentra
    """
    # Buscar el bloque de información del chassis
    chassis_match = re.search(r'show\s+chassis\s+={3,}[\s\S]+?Type\s*:\s*([^\n]+)', bloque)
    
    if not chassis_match:
        return None
    
    # Extraer el tipo de equipo del campo Type
    tipo_equipo_completo = chassis_match.group(1).strip()
    
    # Verificar que el tipo comience con '7' seguido de tres dígitos (7210, 7750, etc.)
    tipo_match = re.match(r'(7\d{3}\s+\S+(?:\s+\S+)*)', tipo_equipo_completo)
    
    if tipo_match:
        return tipo_match.group(1).strip()
    
    return None

def extraer_tipo_equipo(target):
    """
    Extrae el tipo de equipo Nokia desde el nombre del target.
    Esta función es un fallback cuando no se puede extraer el tipo desde 'show chassis'.
    Solo considera válidos los tipos que comienzan con '7' seguido de tres dígitos.
    
    Args:
        target (str): Nombre del equipo
        
    Returns:
        str: Tipo de equipo Nokia o 'No clasificado' si no se puede determinar
    """
    # Patrones para extraer tipo de equipo desde el nombre del target
    patrones = [
        # Patrón para nombres que contienen el modelo directamente (ej: SR12-7750)
        r'(?:^|[^0-9])(7\d{3})(?:[^0-9]|$)',
        # Patrón para nombres que contienen el modelo con guiones (ej: 7210-SAS)
        r'(7\d{3})-([A-Za-z]+)',
        # Patrón para nombres que contienen el modelo con guión bajo (ej: 7210_SAS)
        r'(7\d{3})_([A-Za-z]+)',
    ]
    
    # Buscar tipo de equipo usando los patrones
    for patron in patrones:
        match = re.search(patron, target)
        if match:
            modelo = match.group(1)
            
            # Mapeo de modelos a tipos completos
            if modelo == '7210':
                return '7210 SAS'
            elif modelo == '7750':
                return '7750 SR'
            elif modelo == '7450':
                return '7450 ESS'
            elif modelo == '7705':
                return '7705 SAR'
            elif modelo == '7950':
                return '7950 XRS'
            elif modelo == '7250':
                return '7250 IXR'
            elif modelo == '7710':
                return '7710 SR'
            elif modelo == '7950':
                return '7950 XRS'
            elif modelo == '7740':
                return '7740 SR'
            elif modelo == '7360':
                return '7360 ISAM'
            elif modelo == '7368':
                return '7368 ISAM'
            elif modelo == '7302':
                return '7302 ISAM'
            elif modelo == '7330':
                return '7330 ISAM'
            elif modelo == '7220':
                return '7220 VPLS'
            elif modelo == '7510':
                return '7510 SAR'
            elif modelo == '7520':
                return '7520 SAR'
            elif modelo == '7750':
                return '7750 SR'
            else:
                return f'{modelo}'
    
    # Si no se encuentra un patrón válido, devolver 'No clasificado'
    return 'No clasificado'

def validar_tipo_equipo(tipo_equipo):
    """
    Valida que el tipo de equipo sea un modelo Nokia válido.
    
    Args:
        tipo_equipo (str): Tipo de equipo a validar
        
    Returns:
        bool: True si es un tipo válido, False en caso contrario
    """
    if not tipo_equipo:
        return False
    
    # Verificar que el tipo comience con '7' seguido de tres dígitos
    return bool(re.match(r'7\d{3}', tipo_equipo))
