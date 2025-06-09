import pandas as pd
import streamlit as st
import re
import io
import os

def integrar_exportacion_noc(df_servicios, df_resumen, equipo_seleccionado):
    """
    Integra la funcionalidad de exportación NOC directamente en la interfaz principal.
    
    Args:
        df_servicios (DataFrame): DataFrame con información de servicios
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        equipo_seleccionado (str): Nombre del equipo seleccionado
    """
    # Verificar si hay un equipo seleccionado
    if not equipo_seleccionado:
        return
    
    # Verificar si hay datos de servicios totales cargados
    if 'df_servicios_totales' not in st.session_state or st.session_state.df_servicios_totales is None:
        st.warning("Para generar el reporte NOC, primero debe cargar el archivo de servicios totales en el panel lateral.")
        return
    
    try:
        # Verificar si la columna 'target' existe en df_servicios
        if 'target' not in df_servicios.columns:
            st.error("Error: La columna 'target' no existe en los datos de servicios.")
            return
        
        # Filtrar servicios del equipo seleccionado - CORREGIDO: Filtrado exacto por target
        servicios_equipo = df_servicios[df_servicios['target'].astype(str).str.strip() == equipo_seleccionado.strip()]
        
        if servicios_equipo.empty:
            st.info(f"No se encontraron servicios para el equipo {equipo_seleccionado}.")
            return
        
        # Mostrar información sobre los servicios encontrados
        st.info(f"Se encontraron {len(servicios_equipo)} servicios para el equipo {equipo_seleccionado}.")
        
        # Mostrar botón para exportar a NOC
        button_key = f"exportar_noc_btn_{equipo_seleccionado.replace('-', '_').replace('.', '_')}"
        if st.button(f"Exportar servicios de {equipo_seleccionado} a NOC", key=button_key):
            # Generar el archivo Excel para NOC
            excel_data = generar_excel_noc(servicios_equipo, st.session_state.df_servicios_totales)
            
            # Ofrecer descarga del archivo
            download_key = f"download_noc_btn_{equipo_seleccionado.replace('-', '_').replace('.', '_')}"
            st.download_button(
                label="Descargar List of Services",
                data=excel_data,
                file_name="List of Services.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=download_key
            )
    except Exception as e:
        st.error(f"Error al procesar servicios: {str(e)}")

def generar_excel_noc(servicios_equipo, df_servicios_totales):
    """
    Genera un archivo Excel con el formato requerido para el NOC.
    
    Args:
        servicios_equipo (DataFrame): DataFrame con los servicios del equipo seleccionado
        df_servicios_totales (DataFrame): DataFrame con todos los servicios de la red
    
    Returns:
        bytes: Datos del archivo Excel generado
    """
    # Crear DataFrame para el reporte NOC
    df_noc = pd.DataFrame(columns=['ID', 'Customer/Company', 'NAME', 'Service Impact'])
    
    # Procesar cada servicio
    for _, servicio in servicios_equipo.iterrows():
        # Obtener el ServiceId exacto
        service_id = str(servicio['service_id']).strip()
        
        # Obtener el nombre del servicio del archivo original (puede estar truncado)
        service_name_original = servicio['service_name'] if pd.notna(servicio['service_name']) else ""
        
        # Buscar la descripción completa en el Excel/CSV usando el ServiceId exacto
        descripcion_completa = buscar_servicio_en_totales(service_id, df_servicios_totales)
        
        # Si encontramos la descripción completa en el Excel/CSV, usarla; si no, usar la del archivo original
        nombre_completo = descripcion_completa if descripcion_completa is not None else service_name_original
        
        # Extraer el código CI o CO de la descripción completa
        id_tipo = extraer_codigo_ci_co(nombre_completo)
        
        # Añadir fila al DataFrame NOC
        df_noc = df_noc._append({
            'ID': id_tipo,  # El código CI o CO extraído
            'Customer/Company': 'LibertyNet',  # Siempre es LibertyNet
            'NAME': nombre_completo,  # La descripción completa del servicio
            'Service Impact': 'Loss of Service'  # Siempre es Loss of Service
        }, ignore_index=True)
    
    # CORREGIDO: Eliminar filas duplicadas antes de exportar
    df_noc = df_noc.drop_duplicates()
    
    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_noc.to_excel(writer, sheet_name='List of Services', index=False)
    
    # Obtener los datos del archivo
    output.seek(0)
    return output.getvalue()

def buscar_servicio_en_totales(service_id, df_servicios_totales):
    """
    Busca un servicio en el DataFrame de servicios totales por su ServiceId exacto.
    Compatible con formatos Excel y CSV.
    
    Args:
        service_id (str): ServiceId del servicio a buscar
        df_servicios_totales (DataFrame): DataFrame con todos los servicios de la red
    
    Returns:
        str: Descripción completa del servicio o None si no se encuentra
    """
    try:
        # Convertir service_id a string para comparación
        service_id_str = str(service_id).strip()
        
        # Verificar si el DataFrame tiene las columnas del formato CSV nuevo
        if 'Service ID' in df_servicios_totales.columns:
            # Formato CSV: Buscar por la columna 'Service ID'
            matches = df_servicios_totales[df_servicios_totales['Service ID'].astype(str).str.strip() == service_id_str]
            
            if not matches.empty:
                # Encontramos una coincidencia exacta
                row = matches.iloc[0]
                
                # Intentar obtener la descripción de las columnas relevantes
                if pd.notna(row.get('Description')) and row['Description'] != 'N/A' and row['Description'] != 'NaN':
                    return row['Description']
                elif pd.notna(row.get('Service Name')):
                    return row['Service Name']
                
                # Si no hay descripción útil, combinar información disponible
                service_name = row.get('Service Name', '')
                service_type = row.get('Service Type', '')
                if service_name and service_type:
                    return f"{service_name} ({service_type})"
                elif service_name:
                    return service_name
                elif service_type:
                    return service_type
        
        # Si no encontramos con el formato CSV o no es formato CSV, buscar en todas las columnas (formato Excel)
        for col in df_servicios_totales.columns:
            # Convertir la columna a string para poder buscar
            col_str = df_servicios_totales[col].astype(str)
            
            # Buscar filas donde el ServiceId coincida exactamente
            matches = df_servicios_totales[col_str.str.strip() == service_id_str]
            
            if not matches.empty:
                # Encontramos una coincidencia exacta
                row = matches.iloc[0]
                
                # Buscar columnas que puedan contener la descripción del servicio
                desc_columns = [c for c in df_servicios_totales.columns if any(term in str(c).lower() for term in ['desc', 'name', 'servicio', 'service'])]
                
                # Si hay columnas de descripción, buscar en ellas primero
                if desc_columns:
                    for desc_col in desc_columns:
                        val = row[desc_col]
                        if isinstance(val, str) and len(val) > 5 and val != 'N/A':  # Asumimos que la descripción tiene más de 5 caracteres
                            return val
                
                # Si no encontramos en columnas de descripción específicas, buscar en cualquier columna
                for col2 in df_servicios_totales.columns:
                    val = row[col2]
                    if isinstance(val, str) and len(val) > 5 and val != 'N/A' and any(term in val for term in ['CI', '.CO', 'ETB', 'MGMT']):
                        return val
        
        # Si no encontramos por coincidencia exacta, intentar buscar como parte de un campo
        for col in df_servicios_totales.columns:
            # Convertir la columna a string para poder buscar
            col_str = df_servicios_totales[col].astype(str)
            
            # Buscar filas que contengan el ServiceId como parte del valor
            pattern = r'\b' + re.escape(service_id_str) + r'\b'
            matches = df_servicios_totales[col_str.str.contains(pattern, regex=True, na=False)]
            
            if not matches.empty:
                # Encontramos una coincidencia parcial
                row = matches.iloc[0]
                
                # Buscar columnas que puedan contener la descripción del servicio
                desc_columns = [c for c in df_servicios_totales.columns if any(term in str(c).lower() for term in ['desc', 'name', 'servicio', 'service'])]
                
                # Si hay columnas de descripción, buscar en ellas primero
                if desc_columns:
                    for desc_col in desc_columns:
                        val = row[desc_col]
                        if isinstance(val, str) and len(val) > 5 and val != 'N/A':
                            return val
                
                # Si no encontramos en columnas de descripción específicas, buscar en cualquier columna
                for col2 in df_servicios_totales.columns:
                    val = row[col2]
                    if isinstance(val, str) and len(val) > 5 and val != 'N/A' and any(term in val for term in ['CI', '.CO', 'ETB', 'MGMT']):
                        return val
    except Exception as e:
        print(f"Error al buscar servicio {service_id}: {str(e)}")
    
    return None

def extraer_codigo_ci_co(service_name):
    """
    Extrae el código CI o CO de la descripción del servicio.
    
    Args:
        service_name (str): Descripción completa del servicio
    
    Returns:
        str: Código CI, CO, MGMT, WOM o No identificado
    """
    if not isinstance(service_name, str):
        return "No identificado"
    
    # Buscar patrón CI seguido de números (CI1234567)
    ci_match = re.search(r'CI\d+', service_name, re.IGNORECASE)
    if ci_match:
        return ci_match.group(0)  # Devolver el código CI encontrado
    
    # Buscar patrón número.CO (1234567.CO)
    co_match = re.search(r'\d+\.\s*CO', service_name, re.IGNORECASE)
    if co_match:
        return co_match.group(0)  # Devolver el código CO encontrado
    
    # Verificar si es un servicio de gestión
    if "MGMT" in service_name.upper() or "MANAGEMENT" in service_name.upper():
        return "MGMT"
    
    # Verificar si es un servicio WOM
    if "WOM" in service_name.upper():
        return "WOM"
    
    # Si no coincide con ninguno de los patrones anteriores
    return "No identificado"
