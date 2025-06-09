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
from visualizaciones.chatbot_ia import mostrar_chatbot_ia
from visualizaciones.exportacion_noc import mostrar_exportacion_noc
from visualizaciones.mapa_geografico import mostrar_mapa_geografico
from visualizaciones.equipos_no_leidos import mostrar_equipos_no_leidos

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
    st.session_state.df_servicios = pd.DataFrame()
    st.session_state.df_puertos = pd.DataFrame()
    st.session_state.df_descripciones = pd.DataFrame()
    st.session_state.df_chassis = pd.DataFrame()
    st.session_state.df_versiones = pd.DataFrame()
    st.session_state.df_mda = pd.DataFrame()
    st.session_state.df_resumen = pd.DataFrame()
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
        st.rerun()
    
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
                            df_servicios, df_puertos, df_chassis, df_versiones, df_mda, df_resumen, df_no_leidos = procesar_datos(contenido)
                            
                            # Guardar en session_state
                            st.session_state.datos_procesados = True
                            st.session_state.df_servicios = df_servicios
                            st.session_state.df_puertos = df_puertos
                            st.session_state.df_chassis = df_chassis
                            st.session_state.df_versiones = df_versiones
                            st.session_state.df_mda = df_mda
                            st.session_state.df_resumen = df_resumen
                            st.session_state.df_no_leidos = df_no_leidos
                            
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
                        df_servicios, df_puertos, df_chassis, df_versiones, df_mda, df_resumen, df_no_leidos = procesar_datos(contenido)
                        
                        # Guardar en session_state
                        st.session_state.datos_procesados = True
                        st.session_state.df_servicios = df_servicios
                        st.session_state.df_puertos = df_puertos
                        st.session_state.df_chassis = df_chassis
                        st.session_state.df_versiones = df_versiones
                        st.session_state.df_mda = df_mda
                        st.session_state.df_resumen = df_resumen
                        st.session_state.df_no_leidos = df_no_leidos
                        
                        st.success(f"Datos procesados correctamente. Se encontraron {len(df_resumen)} equipos.")
                    else:
                        st.error("Error al procesar los archivos subidos")
    
    # Carga del archivo Excel o CSV de servicios totales
    st.header("Cargar Servicios Totales")
    
    # Opción para elegir entre carga automática o manual
    opcion_carga_excel = st.radio(
        "Seleccione método de carga para Excel:",
        ["Automática (carpeta InformeNokia)", "Manual (subir archivos)"],
        key="opcion_carga_excel_radio"
    )
    
    if opcion_carga_excel == "Automática (carpeta InformeNokia)":
        # Checkbox para activar carga automática de Excel
        carga_excel_activada = st.checkbox("Cargar Excel automáticamente", key="carga_excel_automatica_checkbox")
        
        if carga_excel_activada:
            try:
                # Intentar cargar archivos Excel de NSP19 y NSP24
                excel_path_nsp19 = os.path.join("InformeNokia", "servicios_nsp19.xlsx")
                excel_path_nsp24 = os.path.join("InformeNokia", "servicios_nsp24.xlsx")
                
                df_nsp19 = None
                df_nsp24 = None
                
                if os.path.exists(excel_path_nsp19):
                    df_nsp19 = pd.read_excel(excel_path_nsp19)
                    st.success(f"Archivo Excel NSP19 cargado correctamente. Se encontraron {len(df_nsp19)} servicios.")
                    st.session_state.df_nsp19 = df_nsp19
                
                if os.path.exists(excel_path_nsp24):
                    df_nsp24 = pd.read_excel(excel_path_nsp24)
                    st.success(f"Archivo Excel NSP24 cargado correctamente. Se encontraron {len(df_nsp24)} servicios.")
                    st.session_state.df_nsp24 = df_nsp24
                
                if df_nsp19 is None and df_nsp24 is None:
                    st.warning("No se encontraron archivos Excel en la carpeta InformeNokia. Busque archivos llamados 'servicios_nsp19.xlsx' y 'servicios_nsp24.xlsx'.")
            except Exception as e:
                st.error(f"Error al cargar los archivos Excel: {str(e)}")
    else:
        # Carga manual de archivos Excel
        st.subheader("Excel NSP19")
        uploaded_file_nsp19 = st.file_uploader(
            "Cargar archivo de servicios NSP19", 
            type=["xlsx", "csv"],
            key="servicios_nsp19_uploader"
        )
        
        if uploaded_file_nsp19 is not None:
            try:
                # Determinar el tipo de archivo y cargarlo
                if uploaded_file_nsp19.name.endswith('.csv'):
                    df_nsp19 = pd.read_csv(uploaded_file_nsp19)
                else:  # Excel
                    df_nsp19 = pd.read_excel(uploaded_file_nsp19)
                
                st.success(f"Archivo NSP19 cargado correctamente. Se encontraron {len(df_nsp19)} servicios.")
                st.session_state.df_nsp19 = df_nsp19
            except Exception as e:
                st.error(f"Error al cargar el archivo NSP19: {str(e)}")
        
        st.subheader("Excel NSP24")
        uploaded_file_nsp24 = st.file_uploader(
            "Cargar archivo de servicios NSP24", 
            type=["xlsx", "csv"],
            key="servicios_nsp24_uploader"
        )
        
        if uploaded_file_nsp24 is not None:
            try:
                # Determinar el tipo de archivo y cargarlo
                if uploaded_file_nsp24.name.endswith('.csv'):
                    df_nsp24 = pd.read_csv(uploaded_file_nsp24)
                else:  # Excel
                    df_nsp24 = pd.read_excel(uploaded_file_nsp24)
                
                st.success(f"Archivo NSP24 cargado correctamente. Se encontraron {len(df_nsp24)} servicios.")
                st.session_state.df_nsp24 = df_nsp24
            except Exception as e:
                st.error(f"Error al cargar el archivo NSP24: {str(e)}")
    
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
    tab_names = ["Dashboard", "Mapa Geográfico", "Por Ciudad", "Servicios", "Exportación NOC", "Equipos No Leídos", "Asistente IA", "Filtros Avanzados"]
    
    # Inicializar tab_seleccionada en session_state si no existe
    if 'tab_seleccionada' not in st.session_state:
        st.session_state.tab_seleccionada = "Dashboard"
    
    # Crear las pestañas
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(tab_names)
    
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
    
    # Pestaña Equipos No Leídos
    with tab6:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Equipos No Leídos"
        
        # Mostrar equipos no leídos
        if 'df_no_leidos' in st.session_state and st.session_state.df_no_leidos is not None:
            mostrar_equipos_no_leidos(st.session_state.df_no_leidos)
        else:
            st.info("No hay información disponible sobre equipos no leídos.")
    
    # Pestaña Asistente IA
    with tab7:
        # Actualizar la pestaña seleccionada
        st.session_state.tab_seleccionada = "Asistente IA"
        
        # Asegurar que df_mda nunca sea None antes de llamar a mostrar_chatbot_ia
        if 'df_mda' not in st.session_state or st.session_state.df_mda is None:
            st.session_state.df_mda = pd.DataFrame(columns=['target', 'slot', 'mda', 'type', 'admin_state', 'oper_state'])
        
        # Mostrar el chatbot IA
        mostrar_chatbot_ia(
            st.session_state.df_resumen,
            st.session_state.df_servicios,
            st.session_state.df_puertos,
            st.session_state.df_descripciones,
            st.session_state.df_chassis,
            st.session_state.df_versiones,
            st.session_state.df_mda
        )
    
    # Pestaña Filtros Avanzados
    with tab8:
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

# Eliminado el chat_input duplicado que estaba fuera de las pestañas
