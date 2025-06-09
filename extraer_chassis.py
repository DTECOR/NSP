"""
Módulo para extraer información del chassis de los equipos Nokia.
"""

import re

def extraer_info_chassis(bloque):
    """
    Extrae la información del chassis del bloque de texto.
    Compatible con múltiples formatos de NSP.
    
    Args:
        bloque (str): Bloque de texto del equipo
        
    Returns:
        dict: Diccionario con la información del chassis o None si no se encuentra
    """
    # Inicializar diccionario de información
    chassis_info = {
        'name': None,
        'type': None,
        'serial_number': None,
        'temperature': None,
        'fan_status': None,
        'power_status': None
    }
    
    # Patrones para buscar información del chassis
    patrones_name = [
        r'Name\s*:?\s*([^\n]+)',
        r'Chassis\s+Name\s*:?\s*([^\n]+)',
        r'System\s+Name\s*:?\s*([^\n]+)',
        r'Host\s+Name\s*:?\s*([^\n]+)',
        r'Hostname\s*:?\s*([^\n]+)',
    ]
    
    patrones_type = [
        r'Type\s*:?\s*([^\n]+)',
        r'Chassis\s+Type\s*:?\s*([^\n]+)',
        r'System\s+Type\s*:?\s*([^\n]+)',
        r'Hardware\s+Type\s*:?\s*([^\n]+)',
        r'Model\s*:?\s*([^\n]+)',
        r'Chassis\s+Model\s*:?\s*([^\n]+)',
        r'System\s+Model\s*:?\s*([^\n]+)',
    ]
    
    patrones_serial = [
        r'Serial\s+[Nn]umber\s*:?\s*([^\n]+)',
        r'Chassis\s+Serial\s+[Nn]umber\s*:?\s*([^\n]+)',
        r'System\s+Serial\s+[Nn]umber\s*:?\s*([^\n]+)',
        r'Serial\s*:?\s*([^\n]+)',
        r'Chassis\s+Serial\s*:?\s*([^\n]+)',
        r'System\s+Serial\s*:?\s*([^\n]+)',
        r'S/N\s*:?\s*([^\n]+)',
        r'Chassis\s+S/N\s*:?\s*([^\n]+)',
        r'System\s+S/N\s*:?\s*([^\n]+)',
    ]
    
    patrones_temp = [
        r'Temperature\s*:?\s*([0-9.]+)\s*C',
        r'Chassis\s+Temperature\s*:?\s*([0-9.]+)\s*C',
        r'System\s+Temperature\s*:?\s*([0-9.]+)\s*C',
        r'Temperature\s*:?\s*([0-9.]+)',
        r'Chassis\s+Temperature\s*:?\s*([0-9.]+)',
        r'System\s+Temperature\s*:?\s*([0-9.]+)',
        r'Temp\s*:?\s*([0-9.]+)\s*C',
        r'Chassis\s+Temp\s*:?\s*([0-9.]+)\s*C',
        r'System\s+Temp\s*:?\s*([0-9.]+)\s*C',
        r'Temp\s*:?\s*([0-9.]+)',
        r'Chassis\s+Temp\s*:?\s*([0-9.]+)',
        r'System\s+Temp\s*:?\s*([0-9.]+)',
    ]
    
    # Buscar información del chassis usando los patrones
    for patron in patrones_name:
        match = re.search(patron, bloque)
        if match:
            chassis_info['name'] = match.group(1).strip()
            break
    
    for patron in patrones_type:
        match = re.search(patron, bloque)
        if match:
            chassis_info['type'] = match.group(1).strip()
            break
    
    for patron in patrones_serial:
        match = re.search(patron, bloque)
        if match:
            chassis_info['serial_number'] = match.group(1).strip()
            break
    
    for patron in patrones_temp:
        match = re.search(patron, bloque)
        if match:
            chassis_info['temperature'] = match.group(1).strip()
            break
    
    # Buscar estado de ventiladores
    fan_match = re.search(r'Fan\s+Status\s*:?\s*([^\n]+)', bloque)
    if fan_match:
        chassis_info['fan_status'] = fan_match.group(1).strip()
    
    # Buscar estado de alimentación
    power_match = re.search(r'Power\s+Status\s*:?\s*([^\n]+)', bloque)
    if power_match:
        chassis_info['power_status'] = power_match.group(1).strip()
    
    # Verificar si se encontró al menos alguna información
    if chassis_info['name'] or chassis_info['type'] or chassis_info['serial_number'] or chassis_info['temperature']:
        return chassis_info
    
    # Si no se encontró información, intentar con patrones más generales
    chassis_section = re.search(r'show\s+chassis\s+={3,}([\s\S]+?)(?:={3,}|\Z)', bloque)
    if chassis_section:
        chassis_text = chassis_section.group(1)
        
        # Buscar líneas con información relevante
        lines = chassis_text.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'name' in key and not chassis_info['name']:
                    chassis_info['name'] = value
                elif 'type' in key and not chassis_info['type']:
                    chassis_info['type'] = value
                elif 'serial' in key and not chassis_info['serial_number']:
                    chassis_info['serial_number'] = value
                elif 'temp' in key and not chassis_info['temperature']:
                    # Extraer solo el número de temperatura
                    temp_match = re.search(r'([0-9.]+)', value)
                    if temp_match:
                        chassis_info['temperature'] = temp_match.group(1)
                elif 'fan' in key and not chassis_info['fan_status']:
                    chassis_info['fan_status'] = value
                elif 'power' in key and not chassis_info['power_status']:
                    chassis_info['power_status'] = value
    
    # Verificar si se encontró al menos alguna información
    if chassis_info['name'] or chassis_info['type'] or chassis_info['serial_number'] or chassis_info['temperature']:
        return chassis_info
    
    # Si no se encontró información, buscar en todo el bloque
    if not chassis_info['type']:
        # Intentar extraer tipo de equipo del nombre del target o del contenido
        model_match = re.search(r'(?:^|\s)(\d{4}(?:\s*[A-Za-z]+(?:-[A-Za-z0-9]+)?))', bloque)
        if model_match:
            chassis_info['type'] = model_match.group(1).strip()
    
    # Verificar si se encontró al menos alguna información
    if chassis_info['name'] or chassis_info['type'] or chassis_info['serial_number'] or chassis_info['temperature']:
        return chassis_info
    
    return None
