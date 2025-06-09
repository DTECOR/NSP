import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import re

def mostrar_servicios(df_servicios, df_resumen):
    """
    Muestra la pestaña de servicios con búsqueda dinámica y extracción de códigos CI.
    
    Args:
        df_servicios (DataFrame): DataFrame con información de servicios
        df_resumen (DataFrame): DataFrame con el resumen de equipos
    """
    st.header("Análisis de Servicios")
    
    if df_servicios.empty:
        st.warning("No se encontraron datos de servicios en los equipos analizados.")
        return
    
    # Estadísticas generales de servicios
    st.subheader("Estadísticas Generales de Servicios")
    
    # Contar servicios por tipo
    servicios_por_tipo = df_servicios['type'].value_counts().reset_index()
    servicios_por_tipo.columns = ['Tipo de Servicio', 'Cantidad']
    
    # Crear gráfico de barras para tipos de servicios
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=servicios_por_tipo['Tipo de Servicio'],
        y=servicios_por_tipo['Cantidad'],
        marker_color='lightblue',
        name='Servicios por Tipo'
    ))
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title='Cantidad de Servicios por Tipo',
        xaxis_title='Tipo de Servicio',
        yaxis_title='Cantidad',
        height=500
    )
    
    # Mostrar el gráfico interactivo
    st.plotly_chart(fig)
    
    # Contar servicios por estado operativo
    servicios_por_estado = df_servicios['oper_state'].value_counts().reset_index()
    servicios_por_estado.columns = ['Estado Operativo', 'Cantidad']
    
    # Definir colores según estado
    colors = []
    for estado in servicios_por_estado['Estado Operativo']:
        if estado == 'Up':
            colors.append('green')
        elif estado == 'Down':
            colors.append('red')
        else:
            colors.append('gray')
    
    # Crear gráfico de pastel para estado de servicios
    fig = go.Figure(data=[go.Pie(
        labels=servicios_por_estado['Estado Operativo'],
        values=servicios_por_estado['Cantidad'],
        hole=0.4,
        textinfo='label+percent',
        marker=dict(colors=colors)
    )])
    
    # Hacer el gráfico interactivo
    fig.update_layout(
        title='Distribución de Servicios por Estado Operativo',
        height=500
    )
    
    # Mostrar el gráfico interactivo
    st.plotly_chart(fig)
    
    # Búsqueda de servicios por equipo
    st.subheader("Búsqueda de Servicios por Equipo")
    
    # Obtener lista de equipos
    equipos = sorted(df_servicios['target'].unique().tolist())
    
    # Crear campo de búsqueda con autocompletado
    equipo_busqueda = st.text_input("Buscar equipo (escriba para filtrar):", "")
    
    # Filtrar equipos según la búsqueda
    equipos_filtrados = [equipo for equipo in equipos if equipo_busqueda.lower() in equipo.lower()]
    
    # Mostrar selector con equipos filtrados
    if equipos_filtrados:
        # Usar session_state para almacenar la selección de equipo
        if 'equipo_servicios_seleccionado' not in st.session_state:
            st.session_state.equipo_servicios_seleccionado = None
        
        # Selector para equipo
        equipo_seleccionado = st.selectbox(
            "Seleccionar Equipo:",
            ['Seleccione un equipo...'] + equipos_filtrados,
            key="equipo_servicios_selector"
        )
        
        # Actualizar equipo_servicios_seleccionado en session_state
        if equipo_seleccionado != 'Seleccione un equipo...':
            st.session_state.equipo_servicios_seleccionado = equipo_seleccionado
        
        # Mostrar servicios del equipo seleccionado
        if st.session_state.equipo_servicios_seleccionado:
            # Filtrar servicios del equipo seleccionado
            servicios_equipo = df_servicios[df_servicios['target'] == st.session_state.equipo_servicios_seleccionado]
            
            # Mostrar información del equipo
            equipo_info = df_resumen[df_resumen['target'] == st.session_state.equipo_servicios_seleccionado]
            if not equipo_info.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Servicios", equipo_info['total_servicios'].values[0])
                with col2:
                    st.metric("Ciudad", equipo_info['ciudad'].values[0])
                with col3:
                    st.metric("Estado", equipo_info['estado'].values[0])  # Corregido: 'status' -> 'estado'
            
            # Mostrar tabla de servicios con extracción de CI
            st.subheader(f"Servicios en {st.session_state.equipo_servicios_seleccionado}")
            
            # Extraer códigos CI de las descripciones de servicios
            servicios_equipo.loc[:, 'codigo_ci'] = servicios_equipo['service_name'].apply(extraer_codigo_ci)
            
            # Identificar servicios con descripción cortada
            servicios_equipo.loc[:, 'descripcion_cortada'] = servicios_equipo['service_name'].apply(lambda x: True if x and x.endswith('*') else False)
            
            # Mostrar tabla de servicios
            st.dataframe(servicios_equipo[['service_id', 'type', 'admin_state', 'oper_state', 'customer_id', 'service_name', 'codigo_ci', 'descripcion_cortada']])
            
            # Contar servicios con descripción cortada
            servicios_cortados = servicios_equipo[servicios_equipo['descripcion_cortada'] == True]
            if not servicios_cortados.empty:
                st.warning(f"Se encontraron {len(servicios_cortados)} servicios con descripción cortada (terminan en *). Para obtener la descripción completa, se recomienda ejecutar el comando 'show service id all base' en el equipo.")
                
                # Mostrar comandos recomendados
                st.subheader("Comandos Recomendados para Obtener Información Completa")
                
                # Comando para todos los servicios
                st.code(f"show service id all base")
                
                # Comandos para servicios específicos
                st.subheader("O para servicios específicos:")
                for _, servicio in servicios_cortados.iterrows():
                    st.code(f"show service id {servicio['service_id']} base")
            
            # Análisis de códigos CI
            st.subheader("Análisis de Códigos CI")
            
            # Filtrar servicios con código CI
            servicios_con_ci = servicios_equipo[servicios_equipo['codigo_ci'].notna()]
            
            if not servicios_con_ci.empty:
                # Contar servicios por código CI
                ci_counts = servicios_con_ci['codigo_ci'].value_counts().reset_index()
                ci_counts.columns = ['Código CI', 'Cantidad']
                
                # Mostrar tabla de códigos CI
                st.dataframe(ci_counts)
            else:
                st.info("No se encontraron códigos CI en las descripciones de servicios.")
    else:
        st.info("No se encontraron equipos que coincidan con la búsqueda.")
    
    # Recomendaciones para mejorar la recolección de datos
    st.subheader("Recomendaciones para Mejorar la Recolección de Datos")
    
    st.markdown("""
    Para obtener información completa de los servicios, se recomienda modificar el script NSP para incluir los siguientes comandos:
    
    1. Comando actual para listar servicios:
    ```
    show service service-using
    ```
    
    2. Comando adicional para obtener detalles completos de todos los servicios:
    ```
    show service id all base
    ```
    
    3. Alternativamente, para equipos con muchos servicios, se puede usar un enfoque más selectivo:
       - Primero ejecutar `show service service-using` para identificar los IDs
       - Luego, para cada servicio con descripción cortada (con *), ejecutar:
       ```
       show service id [ID_SERVICIO] base
       ```
    
    Estos comandos permitirán obtener las descripciones completas de los servicios, incluyendo los códigos CI.
    """)

def extraer_codigo_ci(descripcion):
    """
    Extrae el código CI de la descripción del servicio.
    
    Args:
        descripcion (str): Descripción del servicio
    
    Returns:
        str: Código CI o None si no se encuentra
    """
    if not descripcion:
        return None
    
    # Buscar patrón CI seguido de números
    match = re.search(r'CI\d+', descripcion)
    if match:
        return match.group(0)
    else:
        return None
