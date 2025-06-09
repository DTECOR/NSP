import pandas as pd
import streamlit as st
import os
import sys
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go

# Agregar directorios al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos de parser
from parser.cargar_archivos import cargar_archivos_automaticamente, cargar_archivos_manual
from parser.procesar_datos import procesar_datos

# Importar módulos de visualización
from visualizaciones.dashboard_mejorado import mostrar_dashboard_mejorado
from visualizaciones.por_ciudad_mejorado import mostrar_por_ciudad_mejorado
from visualizaciones.servicios import mostrar_servicios
from visualizaciones.chatbot_ia import procesar_consulta
from visualizaciones.exportacion_noc import mostrar_exportacion_noc
from visualizaciones.mapa_geografico import mostrar_mapa_geografico

# Importar utilidades
from utils.exportar_excel import exportar_todo
from utils.exportacion_noc_integrada import integrar_exportacion_noc
from utils.filtros_avanzados import aplicar_filtros_avanzados

# Configuración de la página
st.set_page_config(
    page_title="NSP Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session_state para almacenar datos procesados y estado de carga
if 'datos_procesados' not in st.session_state:
    st.session_state.datos_procesados = False
    st.session_state.df_servicios = None
    st.session_state.df_puertos = None
    st.session_state.df_descripciones = None
    st.session_state.df_chassis = None
    st.session_state.df_versiones = None
    st.session_state.df_mda = None
    st.session_state.df_resumen = None
    st.session_state.carga_activada = False
    st.session_state.chat_history = []
    st.session_state.tema_oscuro = False

# Función para aplicar tema oscuro
def aplicar_tema():
    if st.session_state.tema_oscuro:
        # Aplicar tema oscuro
        st.markdown("""
        <style>
        .stApp {
            background-color: #121212;
            color: #FFFFFF;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1E1E1E;
        }
        .stTabs [data-baseweb="tab"] {
            color: #FFFFFF;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2E2E2E;
        }
        .stMarkdown {
            color: #FFFFFF;
        }
        .stTable {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        .stDataFrame {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        .stSelectbox [data-baseweb="select"] {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        .stTextInput [data-baseweb="input"] {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        .stButton>button {
            background-color: #2E2E2E;
            color: #FFFFFF;
        }
        .stSidebar {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        </style>
        """, unsafe_allow_html=True)

# Aplicar tema según configuración
aplicar_tema()

# Título principal
st.title("📊 NSP Visualizer")
st.markdown("Herramienta avanzada para visualizar, analizar e interpretar datos operativos de equipos de red Nokia")

# Sidebar para carga de datos
with st.sidebar:
    st.header("Configuración")
    
    # Selector de tema
    tema_oscuro = st.checkbox("Modo Oscuro", value=st.session_state.tema_oscuro, key="tema_oscuro_checkbox")
    if tema_oscuro != st.session_state.tema_oscuro:
        st.session_state.tema_oscuro = tema_oscuro
        aplicar_tema()
        st.experimental_rerun()
    
    st.header("Carga de Datos")
    
    # Opciones de carga
    opcion_carga = st.radio(
        "Seleccione método de carga:",
        ["Automática (carpeta InformeNokia)", "Manual (subir archivos)"],
        key="opcion_carga_radio"
    )
    
    if opcion_carga == "Automática (carpeta InformeNokia)":
        # Checkbox para activar carga automática
        carga_activada = st.checkbox("Cargar archivos automáticamente", key="carga_automatica_checkbox")
        
        # Actualizar estado de carga en session_state
        if carga_activada != st.session_state.carga_activada:
            st.session_state.carga_activada = carga_activada
            
            if carga_activada:
                with st.spinner("Cargando archivos de la carpeta InformeNokia..."):
                    contenido = cargar_archivos_automaticamente("InformeNokia")
                    
                    if contenido:
                        st.success(f"Archivos cargados correctamente")
                        
                        # Procesar datos
                        with st.spinner("Procesando datos..."):
                            df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda, df_resumen = procesar_datos(contenido)
                            
                            # Guardar en session_state
                            st.session_state.datos_procesados = True
                            st.session_state.df_servicios = df_servicios
                            st.session_state.df_puertos = df_puertos
                            st.session_state.df_descripciones = df_descripciones
                            st.session_state.df_chassis = df_chassis
                            st.session_state.df_versiones = df_versiones
                            st.session_state.df_mda = df_mda
                            st.session_state.df_resumen = df_resumen
                            
                            st.success(f"Datos procesados correctamente. Se encontraron {len(df_resumen)} equipos.")
                    else:
                        st.error("No se encontraron archivos en la carpeta InformeNokia")
                        st.session_state.carga_activada = False
    else:
        # Carga manual de archivos
        archivos_subidos = st.file_uploader(
            "Seleccione archivos .txt para procesar",
            type=["txt"],
            accept_multiple_files=True,
            key="archivos_txt_uploader"
        )
        
        if archivos_subidos:
            if st.button("Procesar archivos", key="procesar_archivos_btn"):
                with st.spinner("Procesando archivos subidos..."):
                    contenido = cargar_archivos_manual(archivos_subidos)
                    
                    if contenido:
                        # Procesar datos
                        df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda, df_resumen = procesar_datos(contenido)
                        
                        # Guardar en session_state
                        st.session_state.datos_procesados = True
                        st.session_state.df_servicios = df_servicios
                        st.session_state.df_puertos = df_puertos
                        st.session_state.df_descripciones = df_descripciones
                        st.session_state.df_chassis = df_chassis
                        st.session_state.df_versiones = df_versiones
                        st.session_state.df_mda = df_mda
                        st.session_state.df_resumen = df_resumen
                        
                        st.success(f"Datos procesados correctamente. Se encontraron {len(df_resumen)} equipos.")
                    else:
                        st.error("Error al procesar los archivos subidos")
    
    # Carga del archivo Excel o CSV de servicios totales
    st.header("Cargar Servicios Totales")
    uploaded_file = st.file_uploader(
        "Cargar archivo de servicios totales", 
        type=["xlsx", "csv"],
        key="servicios_totales_uploader_sidebar"
    )
    
    if uploaded_file is not None:
        try:
            # Determinar el tipo de archivo y cargarlo
            if uploaded_file.name.endswith('.csv'):
                df_servicios_totales = pd.read_csv(uploaded_file)
                st.success(f"Archivo CSV cargado correctamente. Se encontraron {len(df_servicios_totales)} servicios.")
            else:  # Excel
                df_servicios_totales = pd.read_excel(uploaded_file)
                st.success(f"Archivo Excel cargado correctamente. Se encontraron {len(df_servicios_totales)} servicios.")
            
            # Guardar en session_state
            st.session_state.df_servicios_totales = df_servicios_totales
        except Exception as e:
            st.error(f"Error al cargar el archivo: {str(e)}")
    
    # Botón para exportar todos los datos
    if st.session_state.datos_procesados:
        st.header("Exportar Datos")
        if st.button("Exportar todos los datos a Excel", key="exportar_todos_datos_btn"):
            with st.spinner("Generando archivo Excel..."):
                excel_data = exportar_todo(
                    st.session_state.df_servicios,
                    st.session_state.df_puertos,
                    st.session_state.df_descripciones,
                    st.session_state.df_chassis,
                    st.session_state.df_versiones,
                    st.session_state.df_mda,
                    st.session_state.df_resumen
                )
                
                st.download_button(
                    label="Descargar Excel",
                    data=excel_data,
                    file_name="NSP_Visualizer_Datos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_todos_datos_btn"
                )

# Contenido principal
if st.session_state.datos_procesados:
    # Crear pestañas para navegación
    tab_names = ["Dashboard", "Mapa Geográfico", "Por Ciudad", "Servicios", "Exportación NOC", "Asistente IA", "Filtros Avanzados"]
    
    # Inicializar tab_seleccionada en session_state si no existe
    if 'tab_seleccionada' not in st.session_state:
        st.session_state.tab_seleccionada = "Dashboard"
    
    # Crear las pestañas
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)
    
    # Pestaña de Dashboard
    with tab1:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Dashboard"
        
        # Mostrar contenido del dashboard
        mostrar_dashboard_mejorado(
            st.session_state.df_resumen,
            st.session_state.df_servicios,
            st.session_state.df_puertos,
            st.session_state.df_mda
        )
        
        # Integrar exportación NOC en la vista de Dashboard
        st.subheader("Exportación NOC Directa")
        
        # Selector para equipo
        equipos = sorted(st.session_state.df_resumen['target'].unique().tolist())
        equipo_seleccionado = st.selectbox(
            "Seleccionar Equipo para exportar servicios a NOC:",
            ['Seleccione un equipo...'] + equipos,
            key="equipo_noc_dashboard"
        )
        
        if equipo_seleccionado != 'Seleccione un equipo...':
            # Integrar exportación NOC
            integrar_exportacion_noc(
                st.session_state.df_servicios,
                st.session_state.df_resumen,
                equipo_seleccionado
            )
    
    # Pestaña Mapa Geográfico
    with tab2:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Mapa Geográfico"
        
        # Mostrar mapa geográfico
        mostrar_mapa_geografico(st.session_state.df_resumen)
    
    # Pestaña Por Ciudad
    with tab3:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Por Ciudad"
        
        # Mostrar contenido de Por Ciudad
        mostrar_por_ciudad_mejorado(st.session_state.df_resumen)
    
    # Pestaña Servicios
    with tab4:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Servicios"
        
        # Mostrar contenido de Servicios
        mostrar_servicios(
            st.session_state.df_servicios,
            st.session_state.df_resumen
        )
        
        # Integrar exportación NOC en la vista de Servicios
        st.subheader("Exportación NOC Directa")
        
        # Selector para equipo
        equipos = sorted(st.session_state.df_servicios['target'].unique().tolist())
        equipo_seleccionado = st.selectbox(
            "Seleccionar Equipo para exportar servicios a NOC:",
            ['Seleccione un equipo...'] + equipos,
            key="equipo_noc_servicios"
        )
        
        if equipo_seleccionado != 'Seleccione un equipo...':
            # Integrar exportación NOC
            integrar_exportacion_noc(
                st.session_state.df_servicios,
                st.session_state.df_resumen,
                equipo_seleccionado
            )
    
    # Pestaña Exportación NOC
    with tab5:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Exportación NOC"
        
        # Mostrar contenido de Exportación NOC
        mostrar_exportacion_noc(
            st.session_state.df_servicios,
            st.session_state.df_resumen
        )
    
    # Pestaña Asistente IA
    with tab6:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Asistente IA"
        
        # Mostrar contenido estático del asistente IA
        st.header("Asistente IA para Consultas de Red")
        
        # Explicación del asistente
        st.markdown("""
        Este asistente te permite realizar consultas en lenguaje natural sobre los datos de tu red Nokia.
        
        ### Ejemplos de preguntas que puedes hacer:
        - ¿Cuántos equipos hay en total?
        - ¿Cuáles son los equipos en estado crítico?
        - ¿Qué equipos tienen temperatura mayor a 50 grados?
        - ¿Cuáles son los puertos libres en el equipo BAQ_CLR_7210_01?
        - ¿Cuántos servicios tiene el equipo IBE_ITX_7210_01?
        - ¿Qué versión de TMOS tiene el equipo BOG_ARB_7210_01?
        - ¿Cuáles son los equipos en Barranquilla?
        - Muestra los equipos con más de 100 servicios
        """)
        
        # Mostrar historial de chat
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.chat_message('user').write(message['content'])
            else:
                st.chat_message('assistant').write(message['content'])
        
        # Botón para limpiar historial
        if st.button("Limpiar historial de chat", key="clear_chat_history"):
            st.session_state.chat_history = []
            st.experimental_rerun()
    
    # Pestaña Filtros Avanzados
    with tab7:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Filtros Avanzados"
        
        # Mostrar filtros avanzados
        aplicar_filtros_avanzados(
            st.session_state.df_resumen,
            st.session_state.df_servicios,
            st.session_state.df_puertos,
            st.session_state.df_chassis,
            st.session_state.df_versiones,
            st.session_state.df_mda
        )

# IMPORTANTE: El chat_input debe estar FUERA de cualquier contenedor (expander, form, tabs, columns, sidebar)
# y debe ser el único en toda la aplicación
if st.session_state.datos_procesados and st.session_state.tab_seleccionada == "Asistente IA":
    # Campo de entrada para la consulta - FUERA de cualquier contenedor
    user_query = st.chat_input("Escribe tu consulta aquí...")
    
    if user_query:
        # Añadir consulta del usuario al historial
        st.session_state.chat_history.append({'role': 'user', 'content': user_query})
        
        # Procesar la consulta y obtener respuesta
        response = procesar_consulta(
            user_query, 
            st.session_state.df_resumen,
            st.session_state.df_servicios,
            st.session_state.df_puertos,
            st.session_state.df_descripciones,
            st.session_state.df_chassis,
            st.session_state.df_versiones,
            st.session_state.df_mda
        )
        
        # Añadir respuesta al historial
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        
        # Recargar la página para mostrar la nueva conversación
        st.experimental_rerun()

# Mostrar información cuando no hay datos cargados
if not st.session_state.datos_procesados:
    # Mensaje cuando no hay datos cargados
    st.info("👈 Por favor, cargue los archivos utilizando las opciones del panel lateral para comenzar el análisis.")
    
    # Mostrar información sobre la aplicación
    st.markdown("""
    ## 🎯 Objetivo de NSP Visualizer
    
    NSP Visualizer es una herramienta web avanzada desarrollada en Streamlit cuyo propósito principal es visualizar, analizar e interpretar de forma inteligente los datos operativos de equipos de red Nokia, extraídos desde archivos de texto generados por comandos del sistema NSP (Network Services Platform).
    
    ### 🧠 Características principales
    
    Esta app permite a ingenieros de red:
    
    - ✅ Obtener un inventario detallado y confiable de los equipos de red (targets) y su configuración.
    - ✅ Visualizar la ocupación real de puertos por equipo, discriminando entre puertos administrativamente activos, caídos o libres.
    - ✅ Detectar inconsistencias técnicas entre la configuración esperada y lo que realmente reporta el equipo.
    - ✅ Identificar versiones de sistema operativo TMOS por equipo, destacando cuáles están obsoletas o deben ser migradas.
    - ✅ Verificar la información de chasis y tarjetas MDA instaladas en cada dispositivo.
    - ✅ Discriminar la información por ciudad, utilizando el prefijo del target como nemónico geográfico.
    - ✅ Activar una vista de análisis inteligente que clasifica el estado de cada equipo (OK, Alerta, Crítico) según criterios técnicos definidos.
    
    ### 🚀 Funcionalidades
    
    - 📊 **Visualizaciones interactivas**: Gráficos interactivos que permiten una mejor comprensión de los datos sin recargas de página.
    - 🔍 **Navegación fluida**: Selección de elementos sin recargar la página completa gracias al manejo de estado mejorado.
    - 🌆 **Mapeo de ciudades personalizado**: Agrupación correcta de equipos por ciudad según el mapeo proporcionado.
    - 📈 **Gráficos anidados**: Visualización de tipos de equipos, MDA y puertos en gráficos anidados interactivos.
    - 🔎 **Búsqueda dinámica de servicios**: Nueva pestaña para buscar y filtrar servicios por equipo con autocompletado.
    - 🔢 **Extracción de códigos CI**: Identificación automática de códigos CI en las descripciones de servicios.
    - 📄 **Exportación NOC integrada**: Generación de reportes en formato NOC directamente desde la interfaz principal.
    - 🤖 **Asistente IA integrado**: Chatbot que permite realizar consultas en lenguaje natural sobre los datos de la red.
    - 🗺️ **Mapa geográfico interactivo**: Visualización de equipos en un mapa de Colombia con códigos de color según su estado.
    - 🌙 **Modo oscuro**: Interfaz con tema oscuro para reducir la fatiga visual.
    - 🔍 **Filtros avanzados**: Opciones avanzadas de filtrado y búsqueda para análisis de grandes volúmenes de datos.
    """)
    
    # Mostrar instrucciones de uso
    st.markdown("""
    ## 📋 Instrucciones de Uso
    
    1. **Carga de Datos**: Seleccione el método de carga en el panel lateral (automática o manual).
    2. **Carga de Servicios Totales**: Suba el archivo Excel o CSV de servicios totales desde el panel lateral.
    3. **Navegación**: Una vez cargados los datos, utilice las pestañas superiores para navegar entre las diferentes vistas.
    4. **Exportación NOC Directa**: Seleccione un equipo en la interfaz principal y genere el reporte NOC con un solo clic.
    5. **Interacción**: Explore los gráficos interactivos y use los selectores para ver información detallada sin recargas.
    6. **Consultas al Asistente IA**: Utilice el asistente IA para realizar consultas en lenguaje natural sobre los datos de su red.
    7. **Exportación**: Puede exportar todos los datos utilizando el botón correspondiente en el panel lateral.
    8. **Mapa Geográfico**: Visualice la ubicación de los equipos en un mapa interactivo de Colombia.
    9. **Modo Oscuro**: Active el modo oscuro desde el panel lateral para reducir la fatiga visual.
    10. **Filtros Avanzados**: Utilice la pestaña de filtros avanzados para análisis detallados.
    """)

# Pie de página
st.markdown("---")
st.markdown("NSP Visualizer | Desarrollado para análisis avanzado de equipos de red Nokia")
