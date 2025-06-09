"""
Módulo para automatizar la carga de archivos Excel de servicios para NOC.
Optimizado para manejar grandes volúmenes de datos.
"""

import os
import pandas as pd
import streamlit as st
import glob
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def cargar_archivos_excel_noc():
    """
    Carga automáticamente los archivos Excel de servicios para NOC desde la carpeta InformeNokia.
    Detecta automáticamente si son de NSP19 o NSP24 basado en su estructura.
    
    Returns:
        tuple: (df_nsp19, df_nsp24) DataFrames con los servicios de NSP19 y NSP24
    """
    # Inicializar DataFrames vacíos
    df_nsp19 = pd.DataFrame()
    df_nsp24 = pd.DataFrame()
    
    # Buscar archivos Excel en la carpeta InformeNokia
    excel_files = glob.glob(os.path.join('InformeNokia', '*.xlsx'))
    excel_files.extend(glob.glob(os.path.join('InformeNokia', '*.csv')))
    
    # Si no hay archivos en InformeNokia, buscar en la carpeta raíz
    if not excel_files:
        excel_files = glob.glob('*.xlsx')
        excel_files.extend(glob.glob('*.csv'))
    
    # Procesar cada archivo encontrado
    for file_path in excel_files:
        try:
            # Determinar el tipo de archivo y cargarlo
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:  # Excel
                df = pd.read_excel(file_path)
            
            # Detectar si es NSP19 o NSP24 basado en la estructura
            if es_formato_nsp19(df):
                df_nsp19 = df
                print(f"Archivo NSP19 cargado: {file_path}")
            elif es_formato_nsp24(df):
                df_nsp24 = df
                print(f"Archivo NSP24 cargado: {file_path}")
            else:
                print(f"Formato desconocido en archivo: {file_path}")
        except Exception as e:
            print(f"Error al cargar el archivo {file_path}: {str(e)}")
    
    return df_nsp19, df_nsp24

def es_formato_nsp19(df):
    """
    Detecta si un DataFrame tiene el formato de NSP19.
    
    Args:
        df (DataFrame): DataFrame a analizar
        
    Returns:
        bool: True si es formato NSP19, False en caso contrario
    """
    # Verificar columnas características de NSP19
    columnas_nsp19 = ['ServiceId', 'ServiceName', 'CustomerName']
    return any(col in df.columns for col in columnas_nsp19) and len(df.columns) < 15

def es_formato_nsp24(df):
    """
    Detecta si un DataFrame tiene el formato de NSP24.
    
    Args:
        df (DataFrame): DataFrame a analizar
        
    Returns:
        bool: True si es formato NSP24, False en caso contrario
    """
    # Verificar columnas características de NSP24
    columnas_nsp24 = ['Service ID', 'Service Name', 'Description']
    return any(col in df.columns for col in columnas_nsp24) and len(df.columns) >= 15

def buscar_servicio_en_ambos_excel(service_id, df_nsp19, df_nsp24):
    """
    Busca un servicio en ambos DataFrames (NSP19 y NSP24) y devuelve la descripción y origen.
    
    Args:
        service_id (str): ServiceId del servicio a buscar
        df_nsp19 (DataFrame): DataFrame con servicios de NSP19
        df_nsp24 (DataFrame): DataFrame con servicios de NSP24
        
    Returns:
        tuple: (descripcion, origen) Descripción completa del servicio y su origen (NSP19 o NSP24)
    """
    # Convertir service_id a string para comparación
    service_id_str = str(service_id).strip()
    
    # Primero buscar en NSP24 (prioridad)
    if not df_nsp24.empty:
        descripcion, encontrado = buscar_en_dataframe(service_id_str, df_nsp24, formato="NSP24")
        if encontrado:
            return descripcion, "NSP24"
    
    # Si no se encuentra en NSP24, buscar en NSP19
    if not df_nsp19.empty:
        descripcion, encontrado = buscar_en_dataframe(service_id_str, df_nsp19, formato="NSP19")
        if encontrado:
            return descripcion, "NSP19"
    
    # Si no se encuentra en ninguno
    return None, "No encontrado"

def buscar_en_dataframe(service_id_str, df, formato):
    """
    Busca un servicio en un DataFrame específico según su formato.
    Optimizado para rendimiento.
    
    Args:
        service_id_str (str): ServiceId del servicio a buscar
        df (DataFrame): DataFrame donde buscar
        formato (str): Formato del DataFrame ("NSP19" o "NSP24")
        
    Returns:
        tuple: (descripcion, encontrado) Descripción completa y booleano indicando si se encontró
    """
    try:
        if formato == "NSP24":
            # Formato NSP24: Buscar por la columna 'Service ID'
            if 'Service ID' in df.columns:
                # Convertir la columna a string y eliminar espacios
                service_ids = df['Service ID'].astype(str).str.strip()
                
                # Buscar coincidencia exacta (operación vectorizada)
                matches = df[service_ids == service_id_str]
                
                if not matches.empty:
                    # Encontramos una coincidencia exacta
                    row = matches.iloc[0]
                    
                    # Intentar obtener la descripción de las columnas relevantes
                    if pd.notna(row.get('Description')) and row['Description'] != 'N/A' and row['Description'] != 'NaN':
                        return row['Description'], True
                    elif pd.notna(row.get('Service Name')):
                        return row['Service Name'], True
                    
                    # Si no hay descripción útil, combinar información disponible
                    service_name = row.get('Service Name', '')
                    service_type = row.get('Service Type', '')
                    if service_name and service_type:
                        return f"{service_name} ({service_type})", True
                    elif service_name:
                        return service_name, True
                    elif service_type:
                        return service_type, True
        
        elif formato == "NSP19":
            # Formato NSP19: Buscar por la columna 'ServiceId'
            if 'ServiceId' in df.columns:
                # Convertir la columna a string y eliminar espacios
                service_ids = df['ServiceId'].astype(str).str.strip()
                
                # Buscar coincidencia exacta (operación vectorizada)
                matches = df[service_ids == service_id_str]
                
                if not matches.empty:
                    # Encontramos una coincidencia exacta
                    row = matches.iloc[0]
                    
                    # Intentar obtener la descripción de las columnas relevantes
                    if pd.notna(row.get('ServiceName')) and row['ServiceName'] != 'N/A' and row['ServiceName'] != 'NaN':
                        return row['ServiceName'], True
                    elif pd.notna(row.get('CustomerName')):
                        return f"{row['ServiceName']} - {row['CustomerName']}", True
                    
                    # Si no hay descripción útil, usar ServiceName
                    return row.get('ServiceName', ''), True
        
        # Búsqueda genérica en todas las columnas (solo si no se encontró por las búsquedas específicas)
        # Limitamos la búsqueda a columnas clave para mejorar rendimiento
        columnas_clave = [col for col in df.columns if any(term in str(col).lower() for term in ['id', 'service', 'name', 'desc'])]
        if not columnas_clave:
            columnas_clave = df.columns  # Si no hay columnas clave, usar todas
        
        for col in columnas_clave:
            try:
                # Convertir la columna a string para poder buscar
                col_str = df[col].astype(str)
                
                # Buscar filas donde el ServiceId coincida exactamente
                matches = df[col_str.str.strip() == service_id_str]
                
                if not matches.empty:
                    # Encontramos una coincidencia exacta
                    row = matches.iloc[0]
                    
                    # Buscar columnas que puedan contener la descripción del servicio
                    desc_columns = [c for c in df.columns if any(term in str(c).lower() for term in ['desc', 'name', 'servicio', 'service'])]
                    
                    # Si hay columnas de descripción, buscar en ellas primero
                    if desc_columns:
                        for desc_col in desc_columns:
                            val = row[desc_col]
                            if isinstance(val, str) and len(val) > 5 and val != 'N/A':
                                return val, True
                    
                    # Si no encontramos en columnas de descripción específicas, buscar en cualquier columna
                    for col2 in df.columns:
                        val = row[col2]
                        if isinstance(val, str) and len(val) > 5 and val != 'N/A' and any(term in val for term in ['CI', '.CO', 'ETB', 'MGMT']):
                            return val, True
            except Exception:
                # Ignorar errores en columnas específicas y continuar con la siguiente
                continue
    except Exception as e:
        print(f"Error al buscar servicio {service_id_str}: {str(e)}")
    
    return None, False

def buscar_servicios_en_lote(servicios_df, df_nsp19, df_nsp24, batch_size=100):
    """
    Busca servicios en lotes para mejorar el rendimiento con grandes volúmenes de datos.
    
    Args:
        servicios_df (DataFrame): DataFrame con los servicios a buscar
        df_nsp19 (DataFrame): DataFrame con servicios de NSP19
        df_nsp24 (DataFrame): DataFrame con servicios de NSP24
        batch_size (int): Tamaño del lote para procesar en paralelo
        
    Returns:
        tuple: (resultados, estadisticas) Lista de resultados y estadísticas de origen
    """
    # Inicializar resultados y estadísticas
    resultados = []
    estadisticas = {
        'NSP19': 0,
        'NSP24': 0,
        'No encontrado': 0
    }
    
    # Dividir en lotes para procesar
    total_servicios = len(servicios_df)
    
    # Función para procesar un servicio
    def procesar_servicio(servicio):
        service_id = str(servicio['service_id']).strip()
        target = servicio['target']
        service_name_original = servicio['service_name'] if pd.notna(servicio['service_name']) else ""
        
        # Buscar la descripción completa en ambos Excel/CSV
        descripcion_completa, origen = buscar_servicio_en_ambos_excel(service_id, df_nsp19, df_nsp24)
        
        # Si encontramos la descripción completa en algún Excel/CSV, usarla; si no, usar la del archivo original
        nombre_completo = descripcion_completa if descripcion_completa is not None else service_name_original
        
        # Extraer el código CI o CO de la descripción completa
        id_tipo = extraer_codigo_ci_co(nombre_completo)
        
        return {
            'Target': target,
            'Service ID': id_tipo,
            'Customer/Company': 'LibertyNet',
            'Name': nombre_completo,
            'Service Impact': 'Loss of Service',
            'Origen': origen
        }
    
    # Procesar en lotes con ThreadPoolExecutor para paralelizar
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Crear tareas para cada servicio
        futures = []
        for _, servicio in servicios_df.iterrows():
            futures.append(executor.submit(procesar_servicio, servicio))
        
        # Recoger resultados a medida que se completan
        for future in as_completed(futures):
            try:
                resultado = future.result()
                resultados.append(resultado)
                estadisticas[resultado['Origen']] += 1
            except Exception as e:
                print(f"Error al procesar servicio: {str(e)}")
    
    return resultados, estadisticas

def extraer_codigo_ci_co(descripcion):
    """
    Extrae el código CI o CO de la descripción del servicio.
    
    Args:
        descripcion (str): Descripción completa del servicio
        
    Returns:
        str: Código CI o CO extraído, o la descripción original si no se encuentra
    """
    if not descripcion or not isinstance(descripcion, str):
        return "N/A"
    
    # Patrones para buscar códigos CI o CO
    patrones = [
        r'CI\d+',  # Patrón para CI seguido de números
        r'CO\d+',  # Patrón para CO seguido de números
        r'CI[_-]\d+',  # Patrón para CI_XXXX o CI-XXXX
        r'CO[_-]\d+',  # Patrón para CO_XXXX o CO-XXXX
        r'C[I|O]\s+\d+',  # Patrón para CI XXXX o CO XXXX con espacio
        r'CI\w+',  # Patrón para CI seguido de caracteres alfanuméricos
        r'CO\w+'   # Patrón para CO seguido de caracteres alfanuméricos
    ]
    
    # Buscar cada patrón en la descripción
    for patron in patrones:
        match = re.search(patron, descripcion, re.IGNORECASE)
        if match:
            return match.group(0)
    
    # Si no se encuentra ningún patrón, devolver la descripción original
    return descripcion
