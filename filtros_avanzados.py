import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def aplicar_filtros_avanzados(df_resumen, df_servicios, df_puertos, df_chassis, df_versiones, df_mda):
    """
    Implementa filtros avanzados para analizar los datos de equipos de red Nokia.
    
    Args:
        df_resumen: DataFrame con información resumida de los equipos
        df_servicios: DataFrame con información de servicios
        df_puertos: DataFrame con información de puertos
        df_chassis: DataFrame con información de chassis
        df_versiones: DataFrame con información de versiones
        df_mda: DataFrame con información de MDA
    """
    st.header("Filtros Avanzados")
    
    st.markdown("""
    Esta sección permite aplicar filtros avanzados para analizar en detalle los datos de su red Nokia.
    Combine múltiples criterios para identificar patrones, problemas o oportunidades de optimización.
    """)
    
    # Inicializar variables de estado para filtros si no existen
    if 'filtros_aplicados' not in st.session_state:
        st.session_state.filtros_aplicados = False
        st.session_state.filtro_ciudad = []
        st.session_state.filtro_tipo_equipo = []
        st.session_state.filtro_temperatura = [0, 100]
        st.session_state.filtro_servicios = [0, 10000]
        st.session_state.filtro_puertos_down = [0, 1000]
        st.session_state.filtro_version = []
        st.session_state.filtro_estado = []
    
    # Crear columnas para organizar los filtros
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Filtros de Ubicación y Hardware")
        
        # Mapeo de ciudades
        mapeo_ciudades = {
            'BAQ': 'Barranquilla',
            'BGA': 'Bogotá',
            'BOG': 'Bogotá',
            'CAL': 'Cali',
            'CLO': 'Cali',
            'CTG': 'Cartagena',
            'CUC': 'Cúcuta',
            'IBE': 'Ibagué',
            'MON': 'Montería',
            'PPN': 'Popayán',
            'SBL': 'Sincelejo',
            'SIN': 'Sincelejo',
            'BUC': 'Bucaramanga'
        }
        
        # Extraer prefijos de ciudad de los equipos
        prefijos_ciudad = []
        for equipo in df_resumen['target']:
            prefijo = equipo.split('_')[0]
            if prefijo in mapeo_ciudades:
                prefijos_ciudad.append(prefijo)
        
        # Obtener ciudades únicas y ordenadas
        ciudades_unicas = sorted(list(set(prefijos_ciudad)))
        ciudades_nombres = [f"{c} ({mapeo_ciudades[c]})" for c in ciudades_unicas]
        
        # Filtro de ciudad
        st.session_state.filtro_ciudad = st.multiselect(
            "Filtrar por Ciudad:",
            options=ciudades_nombres,
            default=st.session_state.filtro_ciudad,
            key="filtro_ciudad_multi"
        )
        
        # Extraer tipos de equipo únicos
        tipos_equipo = []
        for _, equipo in df_chassis.iterrows():
            if 'type' in equipo and pd.notna(equipo['type']):
                tipo = equipo['type']
                # Extraer solo el modelo (7210, 7750, etc.)
                for modelo in ['7210', '7750', '7450', '7705', '7950']:
                    if modelo in str(tipo):
                        tipos_equipo.append(modelo)
                        break
        
        tipos_equipo = sorted(list(set(tipos_equipo)))
        
        # Filtro de tipo de equipo
        st.session_state.filtro_tipo_equipo = st.multiselect(
            "Filtrar por Tipo de Equipo:",
            options=tipos_equipo,
            default=st.session_state.filtro_tipo_equipo,
            key="filtro_tipo_equipo_multi"
        )
        
        # Filtro de temperatura - CORREGIDO: Manejo seguro de NaN
        temp_min = 0
        temp_max = 100
        if 'temperature' in df_chassis.columns and not df_chassis['temperature'].empty:
            # Filtrar valores NaN antes de calcular min/max
            temp_values = df_chassis['temperature'].dropna()
            if not temp_values.empty:
                temp_min = int(temp_values.min())
                temp_max = int(temp_values.max())
        
        st.session_state.filtro_temperatura = st.slider(
            "Rango de Temperatura (°C):",
            min_value=temp_min,
            max_value=max(temp_max, temp_min + 1),  # Asegurar que max sea mayor que min
            value=st.session_state.filtro_temperatura,
            key="filtro_temperatura_slider"
        )
    
    with col2:
        st.subheader("Filtros de Servicios y Estado")
        
        # Filtro de cantidad de servicios - CORREGIDO: Manejo seguro de NaN
        servicios_min = 0
        servicios_max = 1000
        if 'total_servicios' in df_resumen.columns and not df_resumen['total_servicios'].empty:
            # Filtrar valores NaN antes de calcular min/max
            servicios_values = df_resumen['total_servicios'].dropna()
            if not servicios_values.empty:
                servicios_min = int(servicios_values.min())
                servicios_max = int(servicios_values.max())
        
        st.session_state.filtro_servicios = st.slider(
            "Rango de Servicios:",
            min_value=servicios_min,
            max_value=max(servicios_max, servicios_min + 1),  # Asegurar que max sea mayor que min
            value=st.session_state.filtro_servicios,
            key="filtro_servicios_slider"
        )
        
        # Filtro de puertos down - CORREGIDO: Manejo seguro de NaN
        puertos_min = 0
        puertos_max = 100
        if 'puertos_down' in df_resumen.columns and not df_resumen['puertos_down'].empty:
            # Filtrar valores NaN antes de calcular min/max
            puertos_values = df_resumen['puertos_down'].dropna()
            if not puertos_values.empty:
                puertos_min = int(puertos_values.min())
                puertos_max = int(puertos_values.max())
        
        st.session_state.filtro_puertos_down = st.slider(
            "Rango de Puertos Down:",
            min_value=puertos_min,
            max_value=max(puertos_max, puertos_min + 1),  # Asegurar que max sea mayor que min
            value=st.session_state.filtro_puertos_down,
            key="filtro_puertos_down_slider"
        )
        
        # Filtro de versión TMOS
        versiones = []
        if 'timos_version' in df_versiones.columns:
            versiones = sorted(df_versiones['timos_version'].dropna().unique().tolist())
        
        st.session_state.filtro_version = st.multiselect(
            "Filtrar por Versión TMOS:",
            options=versiones,
            default=st.session_state.filtro_version,
            key="filtro_version_multi"
        )
        
        # Filtro de estado
        estados = ['OK', 'Alerta', 'Crítico']
        
        st.session_state.filtro_estado = st.multiselect(
            "Filtrar por Estado:",
            options=estados,
            default=st.session_state.filtro_estado,
            key="filtro_estado_multi"
        )
    
    # Botones para aplicar o limpiar filtros
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("Aplicar Filtros", key="aplicar_filtros_btn"):
            st.session_state.filtros_aplicados = True
    
    with col_btn2:
        if st.button("Limpiar Filtros", key="limpiar_filtros_btn"):
            st.session_state.filtros_aplicados = False
            st.session_state.filtro_ciudad = []
            st.session_state.filtro_tipo_equipo = []
            st.session_state.filtro_temperatura = [temp_min, temp_max]
            st.session_state.filtro_servicios = [servicios_min, servicios_max]
            st.session_state.filtro_puertos_down = [puertos_min, puertos_max]
            st.session_state.filtro_version = []
            st.session_state.filtro_estado = []
            st.experimental_rerun()
    
    # Aplicar filtros si se ha presionado el botón
    if st.session_state.filtros_aplicados:
        # Crear una copia del DataFrame original
        df_filtrado = df_resumen.copy()
        
        # Filtrar por ciudad
        if st.session_state.filtro_ciudad:
            # Extraer solo los códigos de ciudad del filtro (BAQ, BOG, etc.)
            codigos_ciudad = [c.split(' ')[0] for c in st.session_state.filtro_ciudad]
            mask_ciudad = df_filtrado['target'].apply(lambda x: x.split('_')[0] in codigos_ciudad)
            df_filtrado = df_filtrado[mask_ciudad]
        
        # Filtrar por tipo de equipo
        if st.session_state.filtro_tipo_equipo:
            # Unir con df_chassis para obtener el tipo
            df_chassis_tipo = df_chassis[['target', 'type']].dropna()
            df_filtrado = df_filtrado.merge(df_chassis_tipo, on='target', how='left')
            
            # Aplicar filtro de tipo
            mask_tipo = df_filtrado['type'].apply(
                lambda x: any(tipo in str(x) for tipo in st.session_state.filtro_tipo_equipo) if pd.notna(x) else False
            )
            df_filtrado = df_filtrado[mask_tipo]
        
        # Filtrar por temperatura - CORREGIDO: Manejo seguro de NaN
        if 'temperature' in df_filtrado.columns:
            temp_min, temp_max = st.session_state.filtro_temperatura
            # Filtrar solo valores no nulos dentro del rango
            mask_temp = df_filtrado['temperature'].notna() & (df_filtrado['temperature'] >= temp_min) & (df_filtrado['temperature'] <= temp_max)
            df_filtrado = df_filtrado[mask_temp]
        
        # Filtrar por cantidad de servicios - CORREGIDO: Manejo seguro de NaN
        if 'total_servicios' in df_filtrado.columns:
            serv_min, serv_max = st.session_state.filtro_servicios
            # Filtrar solo valores no nulos dentro del rango
            mask_serv = df_filtrado['total_servicios'].notna() & (df_filtrado['total_servicios'] >= serv_min) & (df_filtrado['total_servicios'] <= serv_max)
            df_filtrado = df_filtrado[mask_serv]
        
        # Filtrar por puertos down - CORREGIDO: Manejo seguro de NaN
        if 'puertos_down' in df_filtrado.columns:
            port_min, port_max = st.session_state.filtro_puertos_down
            # Filtrar solo valores no nulos dentro del rango
            mask_port = df_filtrado['puertos_down'].notna() & (df_filtrado['puertos_down'] >= port_min) & (df_filtrado['puertos_down'] <= port_max)
            df_filtrado = df_filtrado[mask_port]
        
        # Filtrar por versión TMOS
        if st.session_state.filtro_version and 'timos_version' in df_filtrado.columns:
            mask_version = df_filtrado['timos_version'].isin(st.session_state.filtro_version)
            df_filtrado = df_filtrado[mask_version]
        
        # Filtrar por estado
        if st.session_state.filtro_estado and 'estado' in df_filtrado.columns:
            mask_estado = df_filtrado['estado'].isin(st.session_state.filtro_estado)
            df_filtrado = df_filtrado[mask_estado]
        
        # Mostrar resultados
        st.subheader(f"Resultados Filtrados ({len(df_filtrado)} equipos)")
        
        if len(df_filtrado) > 0:
            # Mostrar tabla de resultados
            st.dataframe(df_filtrado)
            
            # Visualizaciones de los resultados filtrados
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                # Gráfico de distribución por ciudad
                if 'target' in df_filtrado.columns:
                    # Extraer prefijos de ciudad
                    df_filtrado['ciudad'] = df_filtrado['target'].apply(lambda x: x.split('_')[0])
                    
                    # Contar equipos por ciudad
                    ciudad_counts = df_filtrado['ciudad'].value_counts().reset_index()
                    ciudad_counts.columns = ['Ciudad', 'Cantidad']
                    
                    # Mapear códigos a nombres completos
                    ciudad_counts['Nombre'] = ciudad_counts['Ciudad'].map(mapeo_ciudades)
                    ciudad_counts['Ciudad_Nombre'] = ciudad_counts['Ciudad'] + ' (' + ciudad_counts['Nombre'] + ')'
                    
                    # Crear gráfico
                    fig = px.bar(
                        ciudad_counts,
                        x='Ciudad_Nombre',
                        y='Cantidad',
                        title='Distribución por Ciudad',
                        labels={'Ciudad_Nombre': 'Ciudad', 'Cantidad': 'Cantidad de Equipos'},
                        color='Cantidad',
                        color_continuous_scale='Viridis'
                    )
                    
                    st.plotly_chart(fig)
            
            with col_viz2:
                # Gráfico de distribución por tipo de equipo
                if 'type' in df_filtrado.columns:
                    # Extraer solo el modelo (7210, 7750, etc.)
                    df_filtrado['modelo'] = df_filtrado['type'].apply(
                        lambda x: next((m for m in ['7210', '7750', '7450', '7705', '7950'] if m in str(x)), 'Otro') 
                        if pd.notna(x) else 'No disponible'
                    )
                    
                    # Contar equipos por modelo
                    modelo_counts = df_filtrado['modelo'].value_counts().reset_index()
                    modelo_counts.columns = ['Modelo', 'Cantidad']
                    
                    # Crear gráfico
                    fig = px.pie(
                        modelo_counts,
                        values='Cantidad',
                        names='Modelo',
                        title='Distribución por Tipo de Equipo',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    
                    st.plotly_chart(fig)
            
            # Exportar resultados filtrados
            excel_data = df_filtrado.to_excel(index=False)
            st.download_button(
                label="Exportar Resultados Filtrados",
                data=excel_data,
                file_name="NSP_Resultados_Filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_filtrados_btn"
            )
        else:
            st.warning("No se encontraron equipos que cumplan con los criterios de filtrado.")
    else:
        st.info("Seleccione los filtros deseados y haga clic en 'Aplicar Filtros' para ver los resultados.")
