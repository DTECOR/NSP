"""
Módulo para visualizar equipos no leídos por errores de conexión.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def mostrar_equipos_no_leidos(df_no_leidos):
    """
    Muestra información sobre equipos que no pudieron ser leídos debido a errores de conexión.
    
    Args:
        df_no_leidos (DataFrame): DataFrame con información de equipos no leídos
    """
    st.header("Equipos No Leídos")
    
    if df_no_leidos is None or df_no_leidos.empty:
        st.info("No se detectaron equipos con errores de conexión.")
        return
    
    # Mostrar resumen
    st.subheader("Resumen de Equipos No Leídos")
    
    # Contar por tipo de error
    conteo_por_tipo = df_no_leidos['tipo_error'].value_counts().reset_index()
    conteo_por_tipo.columns = ['Tipo de Error', 'Cantidad']
    
    # Mostrar estadísticas
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de Equipos No Leídos", len(df_no_leidos))
    
    with col2:
        # Mostrar el tipo de error más común
        if not conteo_por_tipo.empty:
            error_comun = conteo_por_tipo.iloc[0]['Tipo de Error']
            cantidad = conteo_por_tipo.iloc[0]['Cantidad']
            st.metric(f"Error más común", f"{error_comun} ({cantidad})")
    
    # Crear gráfico de barras para tipos de error
    fig = px.bar(
        conteo_por_tipo, 
        x='Tipo de Error', 
        y='Cantidad',
        title='Distribución de Errores',
        color='Tipo de Error',
        color_discrete_map={
            'Timeout': 'red',
            'Conexión': 'orange',
            'Autenticación': 'yellow',
            'Desconocido': 'gray'
        }
    )
    
    st.plotly_chart(fig)
    
    # Mostrar tabla detallada
    st.subheader("Detalle de Equipos No Leídos")
    
    # Crear tabla interactiva con Plotly
    tabla_fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Equipo', 'Tipo de Error', 'Detalle del Error'],
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[
                df_no_leidos['target'],
                df_no_leidos['tipo_error'],
                df_no_leidos['error']
            ],
            fill_color=[['white', 'lightgrey'] * len(df_no_leidos)],
            align='left'
        )
    )])
    
    tabla_fig.update_layout(
        title='Equipos No Leídos por Errores de Conexión',
        height=400,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    st.plotly_chart(tabla_fig)
    
    # Extraer códigos de ciudad de los equipos no leídos
    from parser.extraer_ciudad import extraer_ciudad_desde_nombre_equipo, normalizar_ciudad
    
    # Añadir columnas de ciudad
    df_analisis = df_no_leidos.copy()
    df_analisis['ciudad'] = df_analisis['target'].apply(extraer_ciudad_desde_nombre_equipo)
    df_analisis['ciudad_normalizada'] = df_analisis['ciudad'].apply(normalizar_ciudad)
    
    # Agrupar por ciudad normalizada
    if 'ciudad_normalizada' in df_analisis.columns and not df_analisis['ciudad_normalizada'].isna().all():
        st.subheader("Distribución por Ciudad")
        
        ciudad_stats = df_analisis.groupby('ciudad_normalizada').size().reset_index(name='cantidad')
        
        # Crear gráfico de barras para distribución por ciudad
        fig_ciudad = px.bar(
            ciudad_stats, 
            x='ciudad_normalizada', 
            y='cantidad',
            title='Equipos No Leídos por Ciudad',
            labels={'ciudad_normalizada': 'Ciudad', 'cantidad': 'Cantidad de Equipos'},
            color='cantidad',
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig_ciudad)
