import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

def mostrar_dashboard_3d(df_resumen, df_servicios, df_puertos):
    """
    Muestra el dashboard principal con métricas generales y gráficas 3D interactivas.
    
    Args:
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
    """
    st.header("Dashboard General")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Equipos", len(df_resumen))
    
    with col2:
        total_servicios = df_resumen['total_servicios'].sum()
        st.metric("Total Servicios", total_servicios)
    
    with col3:
        total_puertos = df_resumen['total_puertos'].sum()
        st.metric("Total Puertos", total_puertos)
    
    with col4:
        # Calcular porcentaje de puertos activos
        puertos_up = df_resumen['puertos_up'].sum()
        if total_puertos > 0:
            porcentaje_activos = round((puertos_up / total_puertos) * 100, 1)
            st.metric("Puertos Activos", f"{porcentaje_activos}%")
        else:
            st.metric("Puertos Activos", "0%")
    
    # Estado general de equipos
    st.subheader("Estado de Equipos")
    
    # Contar equipos por estado
    estado_counts = df_resumen['status'].value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Cantidad']
    
    # Definir colores según estado
    colors = {'OK': 'green', 'Alerta': 'orange', 'Crítico': 'red'}
    color_values = [colors.get(estado, 'blue') for estado in estado_counts['Estado']]
    
    # Crear gráfico de barras 3D usando go.Bar
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=estado_counts['Estado'],
        y=estado_counts['Cantidad'],
        marker_color=color_values,
        name='Estado de Equipos'
    ))
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title='Cantidad de Equipos por Estado',
        xaxis_title='Estado',
        yaxis_title='Cantidad de Equipos',
        height=500
    )
    
    # Mostrar el gráfico interactivo
    selected_points = plotly_events(fig, click_event=True, hover_event=False, key="estado_plot")
    
    # Mostrar detalles al hacer clic
    if selected_points:
        selected_estado = estado_counts.iloc[selected_points[0]['pointIndex']]['Estado']
        st.subheader(f"Detalles de Equipos en Estado: {selected_estado}")
        equipos_estado = df_resumen[df_resumen['status'] == selected_estado]
        st.dataframe(equipos_estado[['target', 'ciudad', 'total_servicios', 'total_puertos', 
                                    'puertos_up', 'puertos_down', 'temperature', 'status']])
    
    # Distribución de servicios por equipo
    st.subheader("Distribución de Servicios por Equipo")
    
    # Ordenar equipos por cantidad de servicios
    top_servicios = df_resumen.sort_values('total_servicios', ascending=False).head(10)
    
    # Crear gráfico 3D de dispersión para servicios por equipo
    fig = px.scatter_3d(
        top_servicios, 
        x='target', 
        y='ciudad', 
        z='total_servicios',
        color='total_servicios',
        color_continuous_scale='Viridis',
        size='total_servicios',
        size_max=20,
        opacity=0.8,
        title='Top 10 Equipos por Cantidad de Servicios (3D)',
        labels={'total_servicios': 'Cantidad de Servicios', 'target': 'Equipo', 'ciudad': 'Ciudad'},
        height=600
    )
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        scene=dict(
            xaxis_title='Equipo',
            yaxis_title='Ciudad',
            zaxis_title='Servicios',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    # Mostrar el gráfico interactivo
    selected_points = plotly_events(fig, click_event=True, hover_event=False, key="servicios_3d_plot")
    
    # Mostrar detalles al hacer clic
    if selected_points:
        selected_equipo = top_servicios.iloc[selected_points[0]['pointIndex']]['target']
        st.subheader(f"Detalles de Servicios para Equipo: {selected_equipo}")
        servicios_equipo = df_servicios[df_servicios['target'] == selected_equipo]
        st.dataframe(servicios_equipo[['service_id', 'type', 'admin_state', 'oper_state', 'customer_id', 'service_name']])
    
    # Distribución de puertos por estado
    st.subheader("Distribución de Puertos por Estado")
    
    # Calcular totales de puertos por estado
    total_up = df_resumen['puertos_up'].sum()
    total_down = df_resumen['puertos_down'].sum()
    total_unused = df_resumen['puertos_unused'].sum()
    
    # Crear DataFrame para el gráfico
    puertos_estado = pd.DataFrame({
        'Estado': ['Activos (Up)', 'Caídos (Down)', 'Sin Usar'],
        'Cantidad': [total_up, total_down, total_unused]
    })
    
    # Definir colores
    colors = ['green', 'red', 'gray']
    
    # Crear gráfico 3D de pastel
    fig = go.Figure(data=[go.Pie(
        labels=puertos_estado['Estado'],
        values=puertos_estado['Cantidad'],
        hole=0.4,
        textinfo='label+percent',
        marker=dict(colors=colors)
    )])
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title='Distribución de Puertos por Estado',
        scene=dict(
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        height=500
    )
    
    # Mostrar el gráfico interactivo
    selected_points = plotly_events(fig, click_event=True, hover_event=False, key="puertos_3d_plot")
    
    # Mostrar detalles al hacer clic
    if selected_points:
        selected_estado = puertos_estado.iloc[selected_points[0]['pointIndex']]['Estado']
        st.subheader(f"Detalles de Puertos en Estado: {selected_estado}")
        
        if selected_estado == 'Activos (Up)':
            # Mostrar equipos con puertos activos
            equipos_puertos = df_resumen[df_resumen['puertos_up'] > 0].sort_values('puertos_up', ascending=False)
            st.dataframe(equipos_puertos[['target', 'ciudad', 'puertos_up', 'total_puertos', 'status']])
        elif selected_estado == 'Caídos (Down)':
            # Mostrar equipos con puertos caídos
            equipos_puertos = df_resumen[df_resumen['puertos_down'] > 0].sort_values('puertos_down', ascending=False)
            st.dataframe(equipos_puertos[['target', 'ciudad', 'puertos_down', 'total_puertos', 'status']])
        else:  # Sin Usar
            # Mostrar equipos con puertos sin usar
            equipos_puertos = df_resumen[df_resumen['puertos_unused'] > 0].sort_values('puertos_unused', ascending=False)
            st.dataframe(equipos_puertos[['target', 'ciudad', 'puertos_unused', 'total_puertos', 'status']])
    
    # Tabla de resumen interactiva
    st.subheader("Resumen por Equipo")
    
    # Crear tabla interactiva con Plotly
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Target', 'Ciudad', 'Servicios', 'Puertos', 'Puertos Up', 'Puertos Down', 'TiMOS', 'Estado'],
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[
                df_resumen['target'],
                df_resumen['ciudad'],
                df_resumen['total_servicios'],
                df_resumen['total_puertos'],
                df_resumen['puertos_up'],
                df_resumen['puertos_down'],
                df_resumen['timos_version'],
                df_resumen['status']
            ],
            fill_color=[['white', 'lightgrey'] * len(df_resumen)],
            align='left'
        )
    )])
    
    fig.update_layout(
        title='Tabla Interactiva de Resumen por Equipo',
        height=500,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    # Mostrar la tabla interactiva
    selected_points = plotly_events(fig, click_event=True, hover_event=False, key="tabla_resumen")
    
    # Mostrar detalles al hacer clic
    if selected_points:
        selected_row = selected_points[0]['pointIndex']
        selected_equipo = df_resumen.iloc[selected_row]['target']
        st.subheader(f"Detalles Completos del Equipo: {selected_equipo}")
        
        # Crear pestañas para diferentes tipos de información
        tabs = st.tabs(["Información General", "Servicios", "Puertos"])
        
        with tabs[0]:
            # Mostrar información general del equipo
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
        
        with tabs[1]:
            # Mostrar servicios del equipo
            servicios_equipo = df_servicios[df_servicios['target'] == selected_equipo]
            if not servicios_equipo.empty:
                st.dataframe(servicios_equipo[['service_id', 'type', 'admin_state', 'oper_state', 'customer_id', 'service_name']])
            else:
                st.info(f"No hay información de servicios para el equipo {selected_equipo}")
        
        with tabs[2]:
            # Mostrar puertos del equipo
            puertos_equipo = df_puertos[df_puertos['target'] == selected_equipo]
            if not puertos_equipo.empty:
                st.dataframe(puertos_equipo[['port_id', 'admin_state', 'link', 'port_state', 'port_mode', 'port_encp', 'port_type']])
            else:
                st.info(f"No hay información de puertos para el equipo {selected_equipo}")
