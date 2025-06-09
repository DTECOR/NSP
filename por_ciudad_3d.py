import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

def mostrar_por_ciudad_3d(df_resumen):
    """
    Muestra la vista agrupada por ciudad con métricas y gráficas 3D interactivas.
    
    Args:
        df_resumen (DataFrame): DataFrame con el resumen de equipos
    """
    st.header("Análisis por Ciudad")
    
    # Verificar si hay datos de ciudad
    if 'ciudad' not in df_resumen.columns or df_resumen['ciudad'].isna().all():
        st.warning("No se encontraron datos de ciudad en los equipos analizados.")
        return
    
    # Filtrar registros sin ciudad
    df_con_ciudad = df_resumen.dropna(subset=['ciudad'])
    
    if df_con_ciudad.empty:
        st.warning("No se encontraron datos de ciudad en los equipos analizados.")
        return
    
    # Agrupar por ciudad
    ciudades_stats = df_con_ciudad.groupby('ciudad').agg({
        'target': 'count',
        'total_servicios': 'sum',
        'total_puertos': 'sum',
        'puertos_up': 'sum',
        'puertos_down': 'sum',
        'puertos_unused': 'sum'
    }).reset_index()
    
    # Renombrar columnas
    ciudades_stats = ciudades_stats.rename(columns={
        'target': 'total_equipos'
    })
    
    # Calcular porcentaje de puertos activos
    ciudades_stats['porcentaje_puertos_activos'] = (ciudades_stats['puertos_up'] / ciudades_stats['total_puertos'] * 100).round(1)
    
    # Mostrar tabla de resumen por ciudad (interactiva)
    st.subheader("Resumen por Ciudad")
    
    # Crear tabla interactiva con Plotly
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Ciudad', 'Equipos', 'Servicios', 'Puertos', 'Puertos Up', 'Puertos Down', 'Sin Usar', '% Activos'],
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[
                ciudades_stats['ciudad'],
                ciudades_stats['total_equipos'],
                ciudades_stats['total_servicios'],
                ciudades_stats['total_puertos'],
                ciudades_stats['puertos_up'],
                ciudades_stats['puertos_down'],
                ciudades_stats['puertos_unused'],
                ciudades_stats['porcentaje_puertos_activos']
            ],
            fill_color=[['white', 'lightgrey'] * len(ciudades_stats)],
            align='left'
        )
    )])
    
    fig.update_layout(
        title='Tabla Interactiva de Resumen por Ciudad',
        height=400,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    # Mostrar la tabla interactiva
    selected_points = plotly_events(fig, click_event=True, hover_event=False, key="tabla_ciudades")
    
    # Mostrar detalles al hacer clic
    if selected_points:
        selected_row = selected_points[0]['pointIndex']
        selected_ciudad = ciudades_stats.iloc[selected_row]['ciudad']
        st.subheader(f"Detalles de Equipos en Ciudad: {selected_ciudad}")
        equipos_ciudad = df_con_ciudad[df_con_ciudad['ciudad'] == selected_ciudad]
        st.dataframe(equipos_ciudad[['target', 'total_servicios', 'total_puertos', 
                                    'puertos_up', 'puertos_down', 'timos_version', 'status']])
    
    # Gráfico 3D de equipos por ciudad
    st.subheader("Distribución de Equipos por Ciudad")
    
    # Crear gráfico 3D de dispersión para equipos por ciudad
    fig = px.scatter_3d(
        ciudades_stats, 
        x='ciudad', 
        y='total_equipos', 
        z='total_servicios',
        color='total_equipos',
        color_continuous_scale='Viridis',
        size='total_equipos',
        size_max=20,
        opacity=0.8,
        title='Distribución de Equipos y Servicios por Ciudad (3D)',
        labels={'total_equipos': 'Cantidad de Equipos', 'ciudad': 'Ciudad', 'total_servicios': 'Total Servicios'},
        height=600
    )
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        scene=dict(
            xaxis_title='Ciudad',
            yaxis_title='Equipos',
            zaxis_title='Servicios',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    # Mostrar el gráfico interactivo
    selected_points = plotly_events(fig, click_event=True, hover_event=False, key="equipos_3d_plot")
    
    # Mostrar detalles al hacer clic
    if selected_points:
        selected_ciudad = ciudades_stats.iloc[selected_points[0]['pointIndex']]['ciudad']
        st.subheader(f"Detalles de Equipos en Ciudad: {selected_ciudad}")
        equipos_ciudad = df_con_ciudad[df_con_ciudad['ciudad'] == selected_ciudad]
        st.dataframe(equipos_ciudad[['target', 'total_servicios', 'total_puertos', 
                                    'puertos_up', 'puertos_down', 'timos_version', 'status']])
    
    # Gráfico 3D de puertos activos por ciudad
    st.subheader("Porcentaje de Puertos Activos por Ciudad")
    
    # Ordenar por porcentaje de puertos activos
    ciudades_stats_sorted = ciudades_stats.sort_values('porcentaje_puertos_activos', ascending=False)
    
    # Definir colores según porcentaje
    colors = []
    for porcentaje in ciudades_stats_sorted['porcentaje_puertos_activos']:
        if porcentaje >= 80:
            colors.append('green')
        elif porcentaje >= 50:
            colors.append('orange')
        else:
            colors.append('red')
    
    # Crear gráfico de barras para porcentaje de puertos activos
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=ciudades_stats_sorted['ciudad'],
        y=ciudades_stats_sorted['porcentaje_puertos_activos'],
        marker_color=colors,
        name='% Puertos Activos'
    ))
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title='Porcentaje de Puertos Activos por Ciudad',
        xaxis_title='Ciudad',
        yaxis_title='% Puertos Activos',
        height=500
    )
    
    # Mostrar el gráfico interactivo
    selected_points = plotly_events(fig, click_event=True, hover_event=False, key="puertos_activos_plot")
    
    # Mostrar detalles al hacer clic
    if selected_points:
        selected_ciudad = ciudades_stats_sorted.iloc[selected_points[0]['pointIndex']]['ciudad']
        st.subheader(f"Detalles de Puertos en Ciudad: {selected_ciudad}")
        equipos_ciudad = df_con_ciudad[df_con_ciudad['ciudad'] == selected_ciudad]
        st.dataframe(equipos_ciudad[['target', 'puertos_up', 'puertos_down', 'puertos_unused', 'total_puertos', 'status']])
    
    # Mostrar equipos por ciudad (con selector)
    st.subheader("Detalle de Equipos por Ciudad")
    
    # Crear selectbox para elegir ciudad
    ciudades = sorted(df_con_ciudad['ciudad'].unique())
    ciudad_seleccionada = st.selectbox("Seleccionar Ciudad", ciudades, key="ciudad_select")
    
    if ciudad_seleccionada:
        # Filtrar equipos de la ciudad seleccionada
        equipos_ciudad = df_con_ciudad[df_con_ciudad['ciudad'] == ciudad_seleccionada]
        
        # Crear tabla interactiva con Plotly
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['Target', 'Servicios', 'Puertos', 'Puertos Up', 'Puertos Down', 'TiMOS', 'Estado'],
                fill_color='paleturquoise',
                align='left'
            ),
            cells=dict(
                values=[
                    equipos_ciudad['target'],
                    equipos_ciudad['total_servicios'],
                    equipos_ciudad['total_puertos'],
                    equipos_ciudad['puertos_up'],
                    equipos_ciudad['puertos_down'],
                    equipos_ciudad['timos_version'],
                    equipos_ciudad['status']
                ],
                fill_color=[['white', 'lightgrey'] * len(equipos_ciudad)],
                align='left'
            )
        )])
        
        fig.update_layout(
            title=f'Equipos en Ciudad: {ciudad_seleccionada}',
            height=400,
            margin=dict(l=0, r=0, b=0, t=30)
        )
        
        # Mostrar la tabla interactiva
        selected_points = plotly_events(fig, click_event=True, hover_event=False, key="tabla_equipos_ciudad")
        
        # Mostrar detalles al hacer clic
        if selected_points:
            selected_row = selected_points[0]['pointIndex']
            selected_equipo = equipos_ciudad.iloc[selected_row]['target']
            st.subheader(f"Detalles Completos del Equipo: {selected_equipo}")
            equipo_info = df_resumen[df_resumen['target'] == selected_equipo].iloc[0]
            st.json({
                "target": equipo_info['target'],
                "ciudad": equipo_info['ciudad'],
                "total_servicios": int(equipo_info['total_servicios']),
                "total_puertos": int(equipo_info['total_puertos']),
                "puertos_up": int(equipo_info['puertos_up']),
                "puertos_down": int(equipo_info['puertos_down']),
                "puertos_unused": int(equipo_info['puertos_unused']),
                "timos_version": equipo_info['timos_version'],
                "temperature": equipo_info['temperature'],
                "status": equipo_info['status']
            })
