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
from parser.procesar_datos_optimizado import procesar_datos

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
from utils.database_manager import DatabaseManager

# Verificar si se debe usar la base de datos
USE_DATABASE = os.environ.get('USE_DATABASE', 'false').lower() == 'true'

# Configuración de la página
st.set_page_config(
    page_title="NSP Visualizer Enterprise",
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
    st.session_state.db_manager = None

# Inicializar el gestor de base de datos si se debe usar
if USE_DATABASE and st.session_state.db_manager is None:
    # Obtener la cadena de conexión desde las variables de entorno
    connection_string = os.environ.get('DATABASE_URL')
    
    # Inicializar el gestor de base de datos
    st.session_state.db_manager = DatabaseManager(connection_string=connection_string)
    
    # Inicializar la base de datos
    try:
        st.session_state.db_manager.initialize_database()
        st.sidebar.success("Conexión a la base de datos establecida correctamente")
    except Exception as e:
        st.sidebar.error(f"Error al conectar con la base de datos: {str(e)}")
        USE_DATABASE = False

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
st.title("📊 NSP Visualizer Enterprise")
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
                            
                            # Guardar en la base de datos si está habilitada
                            if USE_DATABASE and st.session_state.db_manager:
                                with st.spinner("Guardando datos en la base de datos..."):
                                    try:
                                        # Limpiar datos existentes
                                        st.session_state.db_manager.limpiar_datos()
                                        
                                        # Guardar nuevos datos
                                        st.session_state.db_manager.guardar_equipos(df_resumen)
                                        st.session_state.db_manager.guardar_servicios(df_servicios)
                                        st.session_state.db_manager.guardar_puertos(df_puertos)
                                        st.session_state.db_manager.guardar_descripciones_puertos(df_descripciones)
                                        st.session_state.db_manager.guardar_versiones(df_versiones)
                                        st.session_state.db_manager.guardar_mda(df_mda)
                                        
                                        st.success("Datos guardados en la base de datos correctamente")
                                    except Exception as e:
                                        st.error(f"Error al guardar en la base de datos: {str(e)}")
                            
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
                        
                        # Guardar en la base de datos si está habilitada
                        if USE_DATABASE and st.session_state.db_manager:
                            with st.spinner("Guardando datos en la base de datos..."):
                                try:
                                    # Limpiar datos existentes
                                    st.session_state.db_manager.limpiar_datos()
                                    
                                    # Guardar nuevos datos
                                    st.session_state.db_manager.guardar_equipos(df_resumen)
                                    st.session_state.db_manager.guardar_servicios(df_servicios)
                                    st.session_state.db_manager.guardar_puertos(df_puertos)
                                    st.session_state.db_manager.guardar_descripciones_puertos(df_descripciones)
                                    st.session_state.db_manager.guardar_versiones(df_versiones)
                                    st.session_state.db_manager.guardar_mda(df_mda)
                                    
                                    st.success("Datos guardados en la base de datos correctamente")
                                except Exception as e:
                                    st.error(f"Error al guardar en la base de datos: {str(e)}")
                        
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
            
            # Guardar en la base de datos si está habilitada
            if USE_DATABASE and st.session_state.db_manager:
                with st.spinner("Guardando servicios totales en la base de datos..."):
                    try:
                        st.session_state.db_manager.guardar_servicios_totales(df_servicios_totales)
                        st.success("Servicios totales guardados en la base de datos correctamente")
                    except Exception as e:
                        st.error(f"Error al guardar servicios totales en la base de datos: {str(e)}")
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
    tab_names = ["Dashboard", "Mapa Geográfico", "Por Ciudad", "Servicios", "Exportación NOC", "Asistente IA", "Filtros Avanzados", "Base de Datos"]
    
    # Inicializar tab_seleccionada en session_state si no existe
    if 'tab_seleccionada' not in st.session_state:
        st.session_state.tab_seleccionada = "Dashboard"
    
    # Crear las pestañas
    tabs = st.tabs(tab_names)
    
    # Pestaña de Dashboard
    with tabs[0]:
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
    with tabs[1]:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Mapa Geográfico"
        
        # Mostrar mapa geográfico
        mostrar_mapa_geografico(st.session_state.df_resumen)
    
    # Pestaña Por Ciudad
    with tabs[2]:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Por Ciudad"
        
        # Mostrar contenido de Por Ciudad
        mostrar_por_ciudad_mejorado(st.session_state.df_resumen)
    
    # Pestaña Servicios
    with tabs[3]:
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
    with tabs[4]:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Exportación NOC"
        
        # Mostrar contenido de Exportación NOC
        mostrar_exportacion_noc(
            st.session_state.df_servicios,
            st.session_state.df_resumen
        )
    
    # Pestaña Asistente IA
    with tabs[5]:
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
    with tabs[6]:
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
    
    # Pestaña Base de Datos (solo en versión Enterprise)
    with tabs[7]:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Base de Datos"
        
        st.header("Gestión de Base de Datos")
        
        if USE_DATABASE and st.session_state.db_manager:
            st.success("Base de datos PostgreSQL conectada y operativa")
            
            # Mostrar información de la base de datos
            st.subheader("Información de la Base de Datos")
            
            # Contar registros en cada tabla
            with st.spinner("Consultando información de la base de datos..."):
                try:
                    # Obtener datos de la base de datos
                    df_equipos_db = st.session_state.db_manager.obtener_equipos()
                    df_servicios_db = st.session_state.db_manager.obtener_servicios()
                    df_puertos_db = st.session_state.db_manager.obtener_puertos()
                    
                    # Mostrar conteos
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Equipos en BD", len(df_equipos_db))
                    
                    with col2:
                        st.metric("Servicios en BD", len(df_servicios_db))
                    
                    with col3:
                        st.metric("Puertos en BD", len(df_puertos_db))
                    
                    # Mostrar datos de equipos
                    st.subheader("Equipos en Base de Datos")
                    st.dataframe(df_equipos_db)
                    
                    # Opciones de mantenimiento
                    st.subheader("Mantenimiento de Base de Datos")
                    
                    if st.button("Limpiar todos los datos", key="limpiar_bd_btn"):
                        with st.spinner("Limpiando datos de la base de datos..."):
                            if st.session_state.db_manager.limpiar_datos():
                                st.success("Datos limpiados correctamente")
                            else:
                                st.error("Error al limpiar los datos")
                except Exception as e:
                    st.error(f"Error al consultar la base de datos: {str(e)}")
        else:
            st.warning("La conexión a la base de datos no está habilitada o no se pudo establecer")
            
            # Mostrar instrucciones para habilitar la base de datos
            st.markdown("""
            Para habilitar la conexión a la base de datos:
            
            1. Asegúrese de tener PostgreSQL instalado y en ejecución
            2. Configure las variables de entorno:
               - `USE_DATABASE=true`
               - `DATABASE_URL=postgresql://usuario:contraseña@host:puerto/nombre_bd`
            3. Reinicie la aplicación
            
            Si está utilizando Docker, estas variables ya están configuradas en el archivo docker-compose.yml
            """)

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
            st.session_state.df_chassis,
            st.session_state.df_versiones,
            st.session_state.df_mda
        )
        
        # Añadir respuesta al historial
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        
        # Recargar la página para mostrar la respuesta
        st.experimental_rerun()
