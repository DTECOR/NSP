import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def mostrar_por_ciudad_mejorado(df_resumen):
    """
    Muestra la vista agrupada por ciudad con métricas y gráficas interactivas mejoradas.
    
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
    
    # Usar la función de normalización de ciudades del módulo extraer_ciudad
    from parser.extraer_ciudad import normalizar_ciudad
    
    # Aplicar normalización de ciudades
    df_con_ciudad['ciudad_normalizada'] = df_con_ciudad['ciudad'].apply(normalizar_ciudad)
    
    # Calcular puertos sin usar (si no existe la columna)
    if 'puertos_unused' not in df_con_ciudad.columns:
        # Calcular puertos sin usar como total_puertos - (puertos_up + puertos_down)
        df_con_ciudad['puertos_unused'] = df_con_ciudad['total_puertos'] - (df_con_ciudad['puertos_up'] + df_con_ciudad['puertos_down'])
    
    # Agrupar por ciudad normalizada
    ciudades_stats = df_con_ciudad.groupby('ciudad_normalizada').agg({
        'target': 'count',
        'total_servicios': 'sum',
        'total_puertos': 'sum',
        'puertos_up': 'sum',
        'puertos_down': 'sum',
        'puertos_unused': 'sum'
    }).reset_index()
    
    # Renombrar columnas
    ciudades_stats = ciudades_stats.rename(columns={
        'ciudad_normalizada': 'ciudad',
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
    st.plotly_chart(fig)
    
    # Usar session_state para almacenar la selección de ciudad
    if 'ciudad_seleccionada' not in st.session_state:
        st.session_state.ciudad_seleccionada = None
    
    # Selector para ciudad
    ciudad_seleccionada = st.selectbox(
        "Seleccionar Ciudad para ver detalles",
        ['Todas'] + sorted(ciudades_stats['ciudad'].unique().tolist()),
        key="ciudad_selector"
    )
    
    # Actualizar ciudad_seleccionada en session_state
    if ciudad_seleccionada != 'Todas':
        st.session_state.ciudad_seleccionada = ciudad_seleccionada
    
    # Gráfico de equipos por ciudad
    st.subheader("Distribución de Equipos por Ciudad")
    
    # Crear gráfico de barras para equipos por ciudad
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=ciudades_stats['ciudad'],
        y=ciudades_stats['total_equipos'],
        marker_color='royalblue',
        name='Equipos por Ciudad'
    ))
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title='Cantidad de Equipos por Ciudad',
        xaxis_title='Ciudad',
        yaxis_title='Cantidad de Equipos',
        height=500
    )
    
    # Mostrar el gráfico interactivo
    st.plotly_chart(fig)
    
    # Gráfico de puertos activos por ciudad
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
    st.plotly_chart(fig)
    
    # Mostrar equipos de la ciudad seleccionada
    if st.session_state.ciudad_seleccionada:
        st.subheader(f"Equipos en {st.session_state.ciudad_seleccionada}")
        
        # Filtrar equipos de la ciudad seleccionada
        equipos_ciudad = df_con_ciudad[df_con_ciudad['ciudad_normalizada'] == st.session_state.ciudad_seleccionada]
        
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
                    equipos_ciudad['estado']  # Corregido: 'status' -> 'estado'
                ],
                fill_color=[['white', 'lightgrey'] * len(equipos_ciudad)],
                align='left'
            )
        )])
        
        fig.update_layout(
            title=f'Equipos en {st.session_state.ciudad_seleccionada}',
            height=400,
            margin=dict(l=0, r=0, b=0, t=30)
        )
        
        # Mostrar la tabla interactiva
        st.plotly_chart(fig)
        
        # Usar session_state para almacenar la selección de equipo
        if 'equipo_ciudad_seleccionado' not in st.session_state:
            st.session_state.equipo_ciudad_seleccionado = None
        
        # Selector para equipo
        equipo_seleccionado = st.selectbox(
            "Seleccionar Equipo para ver detalles",
            ['Seleccione un equipo...'] + sorted(equipos_ciudad['target'].unique().tolist()),
            key="equipo_ciudad_selector"
        )
        
        # Actualizar equipo_ciudad_seleccionado en session_state
        if equipo_seleccionado != 'Seleccione un equipo...':
            st.session_state.equipo_ciudad_seleccionado = equipo_seleccionado
        
        # Mostrar detalles del equipo seleccionado
        if st.session_state.equipo_ciudad_seleccionado:
            st.subheader(f"Detalles del Equipo: {st.session_state.equipo_ciudad_seleccionado}")
            equipo_info = df_resumen[df_resumen['target'] == st.session_state.equipo_ciudad_seleccionado].iloc[0]
            
            # Crear un diccionario con la información disponible
            equipo_dict = {
                "target": equipo_info['target'],
                "ciudad": equipo_info['ciudad'],
                "total_servicios": int(equipo_info['total_servicios']),
                "total_puertos": int(equipo_info['total_puertos']),
                "puertos_up": int(equipo_info['puertos_up']),
                "puertos_down": int(equipo_info['puertos_down']),
                "estado": equipo_info['estado']  # Corregido: 'status' -> 'estado'
            }
            
            # Añadir campos opcionales si están disponibles
            if 'puertos_unused' in equipo_info and pd.notna(equipo_info['puertos_unused']):
                equipo_dict["puertos_unused"] = int(equipo_info['puertos_unused'])
            else:
                # Calcular puertos sin usar
                equipo_dict["puertos_unused"] = equipo_dict["total_puertos"] - (equipo_dict["puertos_up"] + equipo_dict["puertos_down"])
            
            if 'timos_version' in equipo_info and pd.notna(equipo_info['timos_version']):
                equipo_dict["timos_version"] = equipo_info['timos_version']
            
            if 'temperature' in equipo_info and pd.notna(equipo_info['temperature']):
                equipo_dict["temperature"] = equipo_info['temperature']
            
            # Mostrar la información como JSON
            st.json(equipo_dict)
