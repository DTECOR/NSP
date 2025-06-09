"""
Módulo para identificar y reportar equipos no leídos por errores de conexión.
"""

import re
import pandas as pd

def identificar_equipos_no_leidos(contenido):
    """
    Identifica equipos que no pudieron ser leídos debido a errores de conexión u otros problemas.
    
    Args:
        contenido (str): Contenido concatenado de todos los archivos
        
    Returns:
        list: Lista de diccionarios con información de equipos no leídos
    """
    equipos_no_leidos = []
    
    # Patrón para identificar bloques de equipos con errores
    patron_bloques_error = r'#Script Name:[^\n]+\s+Script Version:[^\n]+\s+Target:([^\n]+)\s+#Status:Unknown[^\n]*\s+#Detailed Status/Error:\s+#([^\n]+)'
    
    # Buscar todos los bloques con errores
    matches = re.finditer(patron_bloques_error, contenido, re.MULTILINE)
    
    for match in matches:
        target = match.group(1).strip()
        error = match.group(2).strip()
        
        # Extraer más detalles si están disponibles
        error_detallado = None
        error_match = re.search(r'Unknown exception: (.+)', contenido[match.end():match.end()+500])
        if error_match:
            error_detallado = error_match.group(1).strip()
        
        # Determinar tipo de error
        tipo_error = "Desconocido"
        if "timeout" in error.lower() or (error_detallado and "timeout" in error_detallado.lower()):
            tipo_error = "Timeout"
        elif "connection" in error.lower() or (error_detallado and "connection" in error_detallado.lower()):
            tipo_error = "Conexión"
        elif "authentication" in error.lower() or (error_detallado and "authentication" in error_detallado.lower()):
            tipo_error = "Autenticación"
        
        equipos_no_leidos.append({
            'target': target,
            'error': error,
            'error_detallado': error_detallado,
            'tipo_error': tipo_error
        })
    
    return equipos_no_leidos

def generar_resumen_equipos_no_leidos(equipos_no_leidos):
    """
    Genera un resumen de los equipos no leídos agrupados por tipo de error.
    
    Args:
        equipos_no_leidos (list): Lista de diccionarios con información de equipos no leídos
        
    Returns:
        dict: Diccionario con resumen de equipos no leídos
    """
    if not equipos_no_leidos:
        return {
            'total': 0,
            'por_tipo': {},
            'equipos': []
        }
    
    # Contar por tipo de error
    conteo_por_tipo = {}
    for equipo in equipos_no_leidos:
        tipo = equipo['tipo_error']
        if tipo not in conteo_por_tipo:
            conteo_por_tipo[tipo] = 0
        conteo_por_tipo[tipo] += 1
    
    return {
        'total': len(equipos_no_leidos),
        'por_tipo': conteo_por_tipo,
        'equipos': equipos_no_leidos
    }

def crear_dataframe_equipos_no_leidos(equipos_no_leidos):
    """
    Crea un DataFrame con la información de equipos no leídos.
    
    Args:
        equipos_no_leidos (list): Lista de diccionarios con información de equipos no leídos
        
    Returns:
        DataFrame: DataFrame con información de equipos no leídos
    """
    if not equipos_no_leidos:
        return pd.DataFrame(columns=['target', 'tipo_error', 'error'])
    
    return pd.DataFrame(equipos_no_leidos)
