import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from parser.extraer_tipo_equipo import extraer_tipo_equipo

def mostrar_dashboard_mejorado(df_resumen, df_servicios, df_puertos, df_mda, df_versiones=None):
    """
    Muestra el dashboard principal con métricas generales y gráficas interactivas mejoradas.
    
    Args:
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
        df_mda (DataFrame): DataFrame con información de tarjetas MDA
        df_versiones (DataFrame): DataFrame con información de versiones TiMOS
    """
    st.header("Dashboard General")
    
    # Verificar que df_resumen no sea None y tenga datos
    if df_resumen is None or df_resumen.empty:
        st.warning("No hay datos de equipos disponibles para mostrar en el dashboard.")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Equipos", len(df_resumen))
    
    with col2:
        # Verificar si existe la columna total_servicios
        if 'total_servicios' in df_resumen.columns:
            total_servicios = df_resumen['total_servicios'].sum()
            st.metric("Total Servicios", total_servicios)
        else:
            st.metric("Total Servicios", "N/A")
    
    with col3:
        # Verificar si existe la columna total_puertos
        if 'total_puertos' in df_resumen.columns:
            total_puertos = df_resumen['total_puertos'].sum()
            st.metric("Total Puertos", total_puertos)
        else:
            st.metric("Total Puertos", "N/A")
    
    with col4:
        # Calcular porcentaje de puertos activos
        if 'total_puertos' in df_resumen.columns and 'puertos_up' in df_resumen.columns:
            total_puertos = df_resumen['total_puertos'].sum()
            puertos_up = df_resumen['puertos_up'].sum()
            if total_puertos > 0:
                porcentaje_activos = round((puertos_up / total_puertos) * 100, 1)
                st.metric("Puertos Activos", f"{porcentaje_activos}%")
            else:
                st.metric("Puertos Activos", "0%")
        else:
            st.metric("Puertos Activos", "N/A")
    
    # Estado general de equipos con explicación mejorada
    st.subheader("Estado de Equipos")
    
    # Explicación de los estados
    st.info("""
    **Información sobre los estados de equipos:**
    
    - **OK**: Equipos funcionando correctamente, con temperatura normal (<45°C), sin puertos en estado crítico y sin problemas de ventiladores.
    - **Alerta**: Equipos con temperatura elevada (45-55°C), o con más del 30% de puertos caídos, o con algunos puertos críticos.
    - **Crítico**: Equipos con temperatura crítica (>55°C), o con puertos con Admin State UP pero Port State DOWN, o con más del 50% de puertos caídos, o con ventiladores fallidos, o con LED crítico encendido.
    
    Esta clasificación permite identificar rápidamente equipos que requieren atención inmediata o mantenimiento preventivo.
    """)
    
    # Verificar si existe la columna estado
    if 'estado' in df_resumen.columns:
        # Contar equipos por estado
        estado_counts = df_resumen['estado'].value_counts().reset_index()
        estado_counts.columns = ['Estado', 'Cantidad']
        
        # Definir colores según estado
        colors = {'OK': 'green', 'Alerta': 'orange', 'Crítico': 'red'}
        color_values = [colors.get(estado, 'blue') for estado in estado_counts['Estado']]
        
        # Crear gráfico de barras usando go.Bar
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=estado_counts['Estado'],
            y=estado_counts['Cantidad'],
            marker_color=color_values,
            name='Estado de Equipos',
            text=estado_counts['Cantidad'],
            textposition='auto'
        ))
        
        # Hacer el gráfico interactivo
        fig.update_layout(
            title='Cantidad de Equipos por Estado',
            xaxis_title='Estado',
            yaxis_title='Cantidad de Equipos',
            height=500
        )
        
        # Mostrar el gráfico interactivo
        st.plotly_chart(fig)
        
        # Usar session_state para almacenar la selección del estado
        if 'estado_seleccionado' not in st.session_state:
            st.session_state.estado_seleccionado = None
        
        # Obtener estados únicos y filtrar None
        estados_unicos = [estado for estado in df_resumen['estado'].unique() if estado is not None]
        
        # Selector para estado
        estado_seleccionado = st.selectbox(
            "Seleccionar Estado para ver detalles",
            ['Todos'] + sorted(estados_unicos),
            key="estado_selector"
        )
        
        # Actualizar estado_seleccionado en session_state
        if estado_seleccionado != 'Todos':
            st.session_state.estado_seleccionado = estado_seleccionado
        
        # Mostrar detalles del estado seleccionado
        if st.session_state.estado_seleccionado:
            st.subheader(f"Detalles de Equipos en Estado: {st.session_state.estado_seleccionado}")
            equipos_estado = df_resumen[df_resumen['estado'] == st.session_state.estado_seleccionado]
            
            # Seleccionar columnas disponibles para mostrar, incluyendo la razón del estado
            available_columns = []
            for col in ['target', 'ciudad', 'razon_estado', 'total_servicios', 'total_puertos', 'puertos_up', 'puertos_down', 'puertos_admin_up_oper_down', 'temperature', 'estado', 'fuente']:
                if col in equipos_estado.columns:
                    available_columns.append(col)
            
            if available_columns:
                # Asegurar que razon_estado esté entre las primeras columnas si existe
                if 'razon_estado' in available_columns:
                    available_columns.remove('razon_estado')
                    available_columns.insert(2, 'razon_estado')
                
                st.dataframe(equipos_estado[available_columns])
            else:
                st.warning("No hay columnas disponibles para mostrar.")
    else:
        st.warning("No se encontró información de estado en los datos disponibles.")
    
    # Distribución de tipos de equipos - CAMBIADO a gráfico de torta
    st.subheader("Distribución por Tipo de Equipo Nokia")
    
    # Asegurar que df_resumen tenga una columna tipo_equipo_nokia
    if 'tipo_equipo_nokia' not in df_resumen.columns:
        # Verificar si hay información de chassis
        if 'chassis_type' in df_resumen.columns and not df_resumen['chassis_type'].isna().all():
            # Usar el tipo de chassis para la clasificación
            df_resumen['tipo_equipo_nokia'] = df_resumen['chassis_type'].apply(lambda x: extraer_modelo_nokia(x) if pd.notna(x) else "No clasificado")
        elif 'target' in df_resumen.columns:
            # Fallback a la extracción del nombre del target
            df_resumen['tipo_equipo_nokia'] = df_resumen['target'].apply(lambda x: extraer_tipo_equipo(x) if pd.notna(x) else "No clasificado")
        else:
            # Si no hay target, crear una columna con valor por defecto
            df_resumen['tipo_equipo_nokia'] = "No clasificado"
            st.warning("No se pudo determinar el tipo de equipo Nokia debido a falta de información.")
    
    # Asegurar que no haya valores None en tipo_equipo_nokia
    df_resumen['tipo_equipo_nokia'] = df_resumen['tipo_equipo_nokia'].fillna("No clasificado")
    
    # Contar equipos por tipo
    tipo_counts = df_resumen['tipo_equipo_nokia'].value_counts().reset_index()
    tipo_counts.columns = ['Tipo de Equipo Nokia', 'Cantidad']
    
    # Calcular el total para mostrar porcentajes
    total_equipos = tipo_counts['Cantidad'].sum()
    
    # Crear gráfico de torta para tipos de equipos
    fig = go.Figure(data=[go.Pie(
        labels=tipo_counts['Tipo de Equipo Nokia'],
        values=tipo_counts['Cantidad'],
        hole=0.4,  # Crear un donut chart para mejor visualización
        textinfo='label+percent+value',  # Mostrar etiqueta, porcentaje y valor
        textposition='auto',
        marker=dict(
            colors=px.colors.qualitative.Plotly,  # Usar una paleta de colores predefinida
            line=dict(color='#FFFFFF', width=2)  # Borde blanco para mejor separación visual
        ),
        pull=[0.05 if i == 0 else 0 for i in range(len(tipo_counts))]  # Destacar el primer segmento
    )])
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title={
            'text': 'Distribución de Equipos por Modelo Nokia',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        annotations=[
            dict(
                text=f'Total: {total_equipos} equipos',
                x=0.5,
                y=0.5,
                font_size=20,
                showarrow=False
            )
        ]
    )
    
    # Mostrar el gráfico interactivo
    st.plotly_chart(fig)
    
    # Mostrar tabla con detalles de tipos de equipos
    st.subheader("Detalle por Tipo de Equipo")
    st.dataframe(tipo_counts)
    
    # Verificar que el total de equipos en la tabla coincida con el total general
    if total_equipos != len(df_resumen):
        st.warning(f"¡Atención! El total de equipos en la tabla ({total_equipos}) no coincide con el total general ({len(df_resumen)}). Esto puede indicar un problema en la clasificación.")
    else:
        st.success(f"El total de equipos en la tabla ({total_equipos}) coincide con el total general ({len(df_resumen)}), lo que confirma que todos los equipos están correctamente clasificados.")
    
    # Usar session_state para almacenar la selección del tipo de equipo
    if 'tipo_equipo_seleccionado' not in st.session_state:
        st.session_state.tipo_equipo_seleccionado = None
    
    # Obtener tipos de equipo únicos y filtrar None
    tipos_equipo_unicos = [tipo for tipo in df_resumen['tipo_equipo_nokia'].unique() if tipo is not None]
    
    # Selector para tipo de equipo
    tipo_equipo_seleccionado = st.selectbox(
        "Seleccionar Tipo de Equipo para ver detalles de TiMOS",
        ['Todos'] + sorted(tipos_equipo_unicos),
        key="tipo_equipo_selector"
    )
    
    # Actualizar tipo_equipo_seleccionado en session_state
    if tipo_equipo_seleccionado != 'Todos':
        st.session_state.tipo_equipo_seleccionado = tipo_equipo_seleccionado
    
    # Mostrar detalles de versiones TiMOS para el tipo de equipo seleccionado
    if st.session_state.tipo_equipo_seleccionado and 'target' in df_resumen.columns:
        st.subheader(f"Distribución de Versiones TiMOS en Equipos Tipo: {st.session_state.tipo_equipo_seleccionado}")
        
        # Filtrar equipos del tipo seleccionado
        equipos_tipo = df_resumen[df_resumen['tipo_equipo_nokia'] == st.session_state.tipo_equipo_seleccionado]['target'].tolist()
        
        # Verificar que df_versiones no sea None y tenga datos
        if df_versiones is None or df_versiones.empty:
            st.warning("No hay datos de versiones TiMOS disponibles para mostrar.")
        elif 'target' not in df_versiones.columns:
            st.warning("Los datos de versiones TiMOS no contienen información de target.")
        else:
            # Filtrar versiones de esos equipos
            versiones_tipo = df_versiones[df_versiones['target'].isin(equipos_tipo)]
            
            if not versiones_tipo.empty:
                # Verificar si hay datos de versión
                if 'main_version' not in versiones_tipo.columns or versiones_tipo['main_version'].isna().all():
                    # Intentar extraer de timos_version si está disponible
                    if 'timos_version' in versiones_tipo.columns and not versiones_tipo['timos_version'].isna().all():
                        # Extraer versión principal de timos_version
                        versiones_tipo['main_version'] = versiones_tipo['timos_version'].apply(
                            lambda x: x.split('-')[0] if isinstance(x, str) and '-' in x else x
                        )
                    else:
                        st.warning(f"No se encontraron datos de versiones TiMOS para equipos tipo {st.session_state.tipo_equipo_seleccionado}.")
                        return
                
                # Filtrar valores nulos
                versiones_tipo_clean = versiones_tipo[versiones_tipo['main_version'].notna()].copy()
                
                if versiones_tipo_clean.empty:
                    st.warning(f"No se encontraron datos válidos de versiones TiMOS para equipos tipo {st.session_state.tipo_equipo_seleccionado}.")
                else:
                    # Agrupar por versión principal
                    versiones_count = versiones_tipo_clean['main_version'].value_counts().reset_index()
                    versiones_count.columns = ['Versión', 'Cantidad']
                    
                    # Mostrar tabla de versiones
                    st.subheader(f"Distribución de Versiones TiMOS en {st.session_state.tipo_equipo_seleccionado}")
                    st.dataframe(versiones_count)
                    
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
                        title=f'Cantidad de Equipos por Versión TiMOS en {st.session_state.tipo_equipo_seleccionado}',
                        xaxis_title='Versión',
                        yaxis_title='Cantidad de Equipos',
                        height=500
                    )
                    
                    # Mostrar el gráfico interactivo
                    st.plotly_chart(fig)
                    
                    # Gráfico de torta para visualizar distribución porcentual
                    st.subheader(f"Distribución Porcentual de Versiones TiMOS en {st.session_state.tipo_equipo_seleccionado}")
                    
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
                        title=f'Distribución Porcentual de Versiones TiMOS en {st.session_state.tipo_equipo_seleccionado}',
                        height=500
                    )
                    
                    # Mostrar el gráfico interactivo
                    st.plotly_chart(fig_pie)
                    
                    # Mostrar detalle de equipos con su versión
                    st.subheader(f"Detalle de Versiones TiMOS por Equipo en {st.session_state.tipo_equipo_seleccionado}")
                    
                    # Verificar que df_resumen no sea None y tenga datos
                    if df_resumen is None or df_resumen.empty:
                        # Mostrar solo la información de versiones
                        st.dataframe(versiones_tipo_clean[['target', 'timos_version', 'main_version']])
                    else:
                        # Verificar que target esté en ambos DataFrames
                        if 'target' not in df_resumen.columns or 'target' not in versiones_tipo_clean.columns:
                            # Mostrar solo la información de versiones
                            st.dataframe(versiones_tipo_clean[['target', 'timos_version', 'main_version']])
                        else:
                            # Unir información de versiones con resumen
                            df_detalle = pd.merge(
                                versiones_tipo_clean[['target', 'timos_version', 'main_version']], 
                                df_resumen[['target', 'ciudad', 'estado', 'razon_estado', 'fuente']] if 'ciudad' in df_resumen.columns and 'estado' in df_resumen.columns else df_resumen[['target']], 
                                on='target', 
                                how='left'
                            )
                            
                            # Mostrar tabla de detalle
                            st.dataframe(df_detalle)
            else:
                st.warning(f"No se encontraron datos de versiones TiMOS para equipos tipo {st.session_state.tipo_equipo_seleccionado}.")
