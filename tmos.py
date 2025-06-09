import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

def mostrar_tmos(df_versiones, df_resumen):
    """
    Muestra la vista de versiones TMOS por equipo.
    
    Args:
        df_versiones (DataFrame): DataFrame con información de versiones
        df_resumen (DataFrame): DataFrame con el resumen de equipos
    """
    st.header("Análisis de Versiones TiMOS")
    
    # Verificar que df_versiones no sea None y tenga datos
    if df_versiones is None or df_versiones.empty:
        st.warning("No se encontraron datos de versiones TiMOS en los equipos analizados.")
        return
    
    # Verificar si hay datos de versión
    if 'main_version' not in df_versiones.columns or df_versiones['main_version'].isna().all():
        # Intentar extraer de timos_version si está disponible
        if 'timos_version' in df_versiones.columns and not df_versiones['timos_version'].isna().all():
            # Extraer versión principal de timos_version
            df_versiones['main_version'] = df_versiones['timos_version'].apply(
                lambda x: x.split('-')[0] if isinstance(x, str) and '-' in x else x
            )
        else:
            st.warning("No se encontraron datos de versiones TiMOS en los equipos analizados.")
            return
    
    # Filtrar valores nulos
    df_versiones_clean = df_versiones[df_versiones['main_version'].notna()].copy()
    
    if df_versiones_clean.empty:
        st.warning("No se encontraron datos válidos de versiones TiMOS en los equipos analizados.")
        return
    
    # Agrupar por versión principal
    versiones_count = df_versiones_clean['main_version'].value_counts().reset_index()
    versiones_count.columns = ['Versión', 'Cantidad']
    
    # Mostrar tabla de versiones
    st.subheader("Distribución de Versiones TiMOS")
    st.dataframe(versiones_count)
    
    # Gráfico de versiones usando Plotly para mejor interactividad
    st.subheader("Distribución de Equipos por Versión TiMOS")
    
    # Ordenar por versión
    versiones_count_sorted = versiones_count.sort_values('Versión')
    
    # Definir colores según versión (versiones más antiguas en rojo)
    colors = []
    for version in versiones_count_sorted['Versión']:
        try:
            version_str = str(version)
            version_num = float(version_str.split('.')[0])
            if version_num < 8.0:
                colors.append('red')
            elif version_num < 10.0:
                colors.append('orange')
            else:
                colors.append('green')
        except (ValueError, AttributeError, IndexError):
            colors.append('gray')
    
    # Crear gráfico de barras con Plotly
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=versiones_count_sorted['Versión'],
        y=versiones_count_sorted['Cantidad'],
        marker_color=colors,
        text=versiones_count_sorted['Cantidad'],
        textposition='auto'
    ))
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title='Cantidad de Equipos por Versión TiMOS',
        xaxis_title='Versión',
        yaxis_title='Cantidad de Equipos',
        height=500
    )
    
    # Mostrar el gráfico interactivo
    st.plotly_chart(fig)
    
    # Gráfico de torta para visualizar distribución porcentual
    st.subheader("Distribución Porcentual de Versiones TiMOS")
    
    # Crear gráfico de torta con Plotly
    fig_pie = go.Figure(data=[go.Pie(
        labels=versiones_count_sorted['Versión'],
        values=versiones_count_sorted['Cantidad'],
        hole=0.4,  # Crear un donut chart para mejor visualización
        textinfo='label+percent',  # Mostrar etiqueta y porcentaje
        marker=dict(colors=colors)
    )])
    
    # Hacer el gráfico interactivo
    fig_pie.update_layout(
        title='Distribución Porcentual de Versiones TiMOS',
        height=500
    )
    
    # Mostrar el gráfico interactivo
    st.plotly_chart(fig_pie)
    
    # Identificar versiones obsoletas
    st.subheader("Equipos con Versiones Obsoletas")
    
    # Filtrar versiones obsoletas (< 8.0)
    versiones_obsoletas = []
    for _, row in df_versiones_clean.iterrows():
        try:
            version = row['main_version']
            if version:
                version_str = str(version)
                version_num = float(version_str.split('.')[0])
                if version_num < 8.0:
                    versiones_obsoletas.append(row['target'])
        except (ValueError, AttributeError, IndexError):
            pass
    
    if versiones_obsoletas:
        # Verificar que df_resumen no sea None y tenga datos
        if df_resumen is None or df_resumen.empty:
            st.warning(f"Se encontraron {len(versiones_obsoletas)} equipos con versiones obsoletas (< 8.0), pero no hay datos de resumen disponibles.")
        else:
            # Verificar que target esté en df_resumen
            if 'target' not in df_resumen.columns:
                st.warning(f"Se encontraron {len(versiones_obsoletas)} equipos con versiones obsoletas (< 8.0), pero no se puede mostrar el detalle porque falta la columna 'target' en el resumen.")
            else:
                # Filtrar equipos con versiones obsoletas
                equipos_obsoletos = df_resumen[df_resumen['target'].isin(versiones_obsoletas)]
                
                # Seleccionar columnas disponibles para mostrar
                available_columns = []
                for col in ['target', 'ciudad', 'timos_version', 'status', 'fuente']:
                    if col in equipos_obsoletos.columns:
                        available_columns.append(col)
                
                if available_columns:
                    # Mostrar tabla de equipos con versiones obsoletas
                    st.dataframe(equipos_obsoletos[available_columns])
                else:
                    st.warning(f"Se encontraron {len(versiones_obsoletas)} equipos con versiones obsoletas (< 8.0), pero no hay columnas disponibles para mostrar.")
                
                # Mostrar advertencia
                st.warning(f"Se encontraron {len(versiones_obsoletas)} equipos con versiones obsoletas (< 8.0).")
    else:
        st.success("No se encontraron equipos con versiones obsoletas.")
    
    # Mostrar detalle de todos los equipos con su versión
    st.subheader("Detalle de Versiones por Equipo")
    
    # Verificar que df_resumen no sea None y tenga datos
    if df_resumen is None or df_resumen.empty:
        # Mostrar solo la información de versiones
        st.dataframe(df_versiones_clean[['target', 'timos_version', 'main_version']])
    else:
        # Verificar que target esté en ambos DataFrames
        if 'target' not in df_resumen.columns or 'target' not in df_versiones_clean.columns:
            # Mostrar solo la información de versiones
            st.dataframe(df_versiones_clean[['target', 'timos_version', 'main_version']])
        else:
            # Unir información de versiones con resumen
            df_detalle = pd.merge(
                df_versiones_clean[['target', 'timos_version', 'main_version']], 
                df_resumen[['target', 'ciudad', 'status', 'fuente']] if 'ciudad' in df_resumen.columns and 'status' in df_resumen.columns else df_resumen[['target']], 
                on='target', 
                how='left'
            )
            
            # Mostrar tabla de detalle
            st.dataframe(df_detalle)
