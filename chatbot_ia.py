import pandas as pd
import streamlit as st
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

def mostrar_chatbot_ia(df_resumen, df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda):
    """
    Muestra un asistente IA mejorado para consultas en lenguaje natural sobre los datos de red.
    
    Args:
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
        df_descripciones (DataFrame): DataFrame con información de descripciones de puertos
        df_chassis (DataFrame): DataFrame con información de chassis
        df_versiones (DataFrame): DataFrame con información de versiones
        df_mda (DataFrame): DataFrame con información de tarjetas MDA
    """
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
    
    # Inicializar historial de chat en session_state si no existe
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Mostrar historial de chat
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.chat_message('user').write(message['content'])
        else:
            st.chat_message('assistant').write(message['content'])
    
    # IMPORTANTE: El chat_input debe estar fuera de cualquier contenedor (expander, form, tabs, columns, sidebar)
    # y debe ser el único en toda la aplicación
    user_query = st.chat_input("Escribe tu consulta aquí...")
    
    if user_query:
        # Añadir consulta del usuario al historial
        st.session_state.chat_history.append({'role': 'user', 'content': user_query})
        
        # Mostrar consulta del usuario
        st.chat_message('user').write(user_query)
        
        # Procesar la consulta y obtener respuesta
        response = procesar_consulta(user_query, df_resumen, df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda)
        
        # Añadir respuesta al historial
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        
        # Mostrar respuesta
        st.chat_message('assistant').write(response)
    
    # Botón para limpiar historial
    if st.button("Limpiar historial de chat", key="clear_chat_history"):
        st.session_state.chat_history = []
        st.experimental_rerun()

def procesar_consulta(query, df_resumen, df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda):
    """
    Procesa una consulta en lenguaje natural y devuelve una respuesta basada en los datos.
    
    Args:
        query (str): Consulta del usuario
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
        df_descripciones (DataFrame): DataFrame con información de descripciones de puertos
        df_chassis (DataFrame): DataFrame con información de chassis
        df_versiones (DataFrame): DataFrame con información de versiones
        df_mda (DataFrame): DataFrame con información de tarjetas MDA
    
    Returns:
        str: Respuesta a la consulta
    """
    # Convertir consulta a minúsculas para facilitar el procesamiento
    query_lower = query.lower()
    
    # Inicializar NLTK si es necesario
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except:
            pass  # Si falla la descarga, continuamos con el procesamiento básico
    
    # Tokenizar la consulta
    try:
        tokens = word_tokenize(query_lower)
        # Eliminar stopwords
        stop_words = set(stopwords.words('spanish') + stopwords.words('english'))
        tokens = [word for word in tokens if word not in stop_words]
    except:
        # Si falla la tokenización avanzada, usar split básico
        tokens = query_lower.split()
    
    # Detectar intención de la consulta
    
    # 1. Consultas sobre cantidad total de equipos
    if any(word in query_lower for word in ['cuantos', 'cuántos', 'total']) and any(word in query_lower for word in ['equipos', 'dispositivos', 'targets']):
        total_equipos = len(df_resumen)
        return f"Hay un total de {total_equipos} equipos en la red."
    
    # 2. Consultas sobre equipos en estado crítico
    if any(word in query_lower for word in ['crítico', 'critico', 'críticos', 'criticos', 'alerta']) and any(word in query_lower for word in ['estado', 'equipos']):
        estado_buscar = 'Crítico' if any(word in query_lower for word in ['crítico', 'critico', 'críticos', 'criticos']) else 'Alerta'
        equipos_estado = df_resumen[df_resumen['status'] == estado_buscar]
        
        if equipos_estado.empty:
            return f"No hay equipos en estado {estado_buscar}."
        
        equipos_lista = equipos_estado['target'].tolist()
        return f"Hay {len(equipos_lista)} equipos en estado {estado_buscar}:\n\n" + "\n".join(equipos_lista)
    
    # 3. Consultas sobre temperatura
    if any(word in query_lower for word in ['temperatura', 'caliente', 'grados']):
        # Buscar un valor numérico en la consulta
        temp_match = re.search(r'(\d+)\s*(?:grados|°|c|celsius)?', query_lower)
        
        if temp_match:
            temp_threshold = int(temp_match.group(1))
            # Convertir temperaturas a valores numéricos cuando sea posible
            df_resumen['temp_num'] = df_resumen['temperature'].apply(lambda x: 
                int(re.search(r'(\d+)', str(x)).group(1)) if isinstance(x, str) and re.search(r'(\d+)', str(x)) else None
            )
            
            # Filtrar por temperatura
            equipos_temp = df_resumen[df_resumen['temp_num'] > temp_threshold]
            
            if equipos_temp.empty:
                return f"No hay equipos con temperatura mayor a {temp_threshold}°C."
            
            equipos_lista = [f"{row['target']}: {row['temperature']}" for _, row in equipos_temp.iterrows()]
            return f"Hay {len(equipos_lista)} equipos con temperatura mayor a {temp_threshold}°C:\n\n" + "\n".join(equipos_lista)
        else:
            # Mostrar todas las temperaturas
            equipos_temp = df_resumen[['target', 'temperature']].dropna(subset=['temperature'])
            
            if equipos_temp.empty:
                return "No hay información de temperatura disponible."
            
            equipos_lista = [f"{row['target']}: {row['temperature']}" for _, row in equipos_temp.iterrows()]
            return f"Temperaturas de los equipos:\n\n" + "\n".join(equipos_lista[:20]) + (f"\n\n... y {len(equipos_lista) - 20} más." if len(equipos_lista) > 20 else "")
    
    # 4. Consultas sobre puertos libres en un equipo específico
    if any(word in query_lower for word in ['puertos', 'puerto']) and any(word in query_lower for word in ['libre', 'libres', 'disponible', 'disponibles', 'unused', 'sin usar']):
        # Buscar nombre de equipo en la consulta
        equipo_match = None
        for target in df_resumen['target'].tolist():
            if target.lower() in query_lower:
                equipo_match = target
                break
        
        if equipo_match:
            # Obtener información de puertos del equipo
            puertos_equipo = df_puertos[df_puertos['target'] == equipo_match]
            
            if puertos_equipo.empty:
                return f"No hay información de puertos para el equipo {equipo_match}."
            
            # Filtrar puertos libres (admin_state=Up y link=Down)
            puertos_libres = puertos_equipo[(puertos_equipo['admin_state'] == 'Up') & (puertos_equipo['link'] == 'Down')]
            
            if puertos_libres.empty:
                return f"No hay puertos libres en el equipo {equipo_match}."
            
            puertos_lista = puertos_libres['port_id'].tolist()
            return f"El equipo {equipo_match} tiene {len(puertos_lista)} puertos libres:\n\n" + "\n".join(puertos_lista[:20]) + (f"\n\n... y {len(puertos_lista) - 20} más." if len(puertos_lista) > 20 else "")
        else:
            return "Por favor, especifica el nombre del equipo para consultar sus puertos libres."
    
    # 5. Consultas sobre servicios de un equipo específico
    if any(word in query_lower for word in ['servicios', 'servicio']) and not any(word in query_lower for word in ['total']):
        # Buscar nombre de equipo en la consulta
        equipo_match = None
        for target in df_resumen['target'].tolist():
            if target.lower() in query_lower:
                equipo_match = target
                break
        
        if equipo_match:
            # Obtener información de servicios del equipo
            servicios_equipo = df_servicios[df_servicios['target'] == equipo_match]
            
            if servicios_equipo.empty:
                return f"No hay información de servicios para el equipo {equipo_match}."
            
            total_servicios = len(servicios_equipo)
            
            # Si solo piden cantidad
            if any(word in query_lower for word in ['cuantos', 'cuántos', 'cantidad']):
                return f"El equipo {equipo_match} tiene {total_servicios} servicios."
            
            # Si piden detalles
            servicios_lista = [f"{row['service_id']}: {row['service_name']}" for _, row in servicios_equipo.iterrows()]
            return f"El equipo {equipo_match} tiene {total_servicios} servicios:\n\n" + "\n".join(servicios_lista[:20]) + (f"\n\n... y {len(servicios_lista) - 20} más." if len(servicios_lista) > 20 else "")
        else:
            return "Por favor, especifica el nombre del equipo para consultar sus servicios."
    
    # 6. Consultas sobre versión TMOS
    if any(word in query_lower for word in ['timos', 'versión', 'version', 'software']):
        # Buscar nombre de equipo en la consulta
        equipo_match = None
        for target in df_resumen['target'].tolist():
            if target.lower() in query_lower:
                equipo_match = target
                break
        
        if equipo_match:
            # Obtener información de versión del equipo
            version_equipo = df_resumen[df_resumen['target'] == equipo_match]['timos_version'].values
            
            if len(version_equipo) == 0 or pd.isna(version_equipo[0]):
                return f"No hay información de versión TMOS para el equipo {equipo_match}."
            
            return f"El equipo {equipo_match} tiene la versión TMOS: {version_equipo[0]}"
        else:
            # Mostrar todas las versiones
            versiones = df_resumen[['target', 'timos_version']].dropna(subset=['timos_version'])
            
            if versiones.empty:
                return "No hay información de versiones TMOS disponible."
            
            versiones_lista = [f"{row['target']}: {row['timos_version']}" for _, row in versiones.iterrows()]
            return f"Versiones TMOS de los equipos:\n\n" + "\n".join(versiones_lista[:20]) + (f"\n\n... y {len(versiones_lista) - 20} más." if len(versiones_lista) > 20 else "")
    
    # 7. Consultas sobre equipos por ciudad
    ciudades = {
        'barranquilla': 'BAQ',
        'bogota': ['BGA', 'BOG'],
        'bogotá': ['BGA', 'BOG'],
        'cali': ['CAL', 'CLO'],
        'cartagena': 'CTG',
        'cucuta': 'CUC',
        'cúcuta': 'CUC',
        'ibague': 'IBE',
        'ibagué': 'IBE',
        'monteria': 'MON',
        'montería': 'MON',
        'popayan': 'PPN',
        'popayán': 'PPN',
        'sincelejo': ['SBL', 'SIN'],
        'bucaramanga': 'BUC'
    }
    
    for ciudad, prefijos in ciudades.items():
        if ciudad in query_lower:
            if isinstance(prefijos, list):
                equipos_ciudad = df_resumen[df_resumen['ciudad'].isin(prefijos)]
            else:
                equipos_ciudad = df_resumen[df_resumen['ciudad'] == prefijos]
            
            if equipos_ciudad.empty:
                return f"No hay equipos en {ciudad.capitalize()}."
            
            equipos_lista = equipos_ciudad['target'].tolist()
            return f"Hay {len(equipos_lista)} equipos en {ciudad.capitalize()}:\n\n" + "\n".join(equipos_lista)
    
    # 8. Consultas sobre equipos con más de X servicios
    if any(word in query_lower for word in ['más de', 'mas de', 'mayor', 'mayores']) and any(word in query_lower for word in ['servicios', 'servicio']):
        # Buscar un valor numérico en la consulta
        num_match = re.search(r'(\d+)\s*(?:servicios|servicio)?', query_lower)
        
        if num_match:
            num_threshold = int(num_match.group(1))
            equipos_servicios = df_resumen[df_resumen['total_servicios'] > num_threshold]
            
            if equipos_servicios.empty:
                return f"No hay equipos con más de {num_threshold} servicios."
            
            equipos_lista = [f"{row['target']}: {int(row['total_servicios'])} servicios" for _, row in equipos_servicios.iterrows()]
            return f"Hay {len(equipos_lista)} equipos con más de {num_threshold} servicios:\n\n" + "\n".join(equipos_lista)
    
    # 9. Consultas sobre seriales de equipos
    if any(word in query_lower for word in ['serial', 'seriales', 'número de serie']):
        # Verificar si hay información de seriales
        if 'serial_number' in df_chassis.columns:
            seriales = df_chassis[['target', 'serial_number']].dropna(subset=['serial_number'])
            
            if seriales.empty:
                return "No hay información de seriales disponible."
            
            seriales_lista = [f"{row['target']}: {row['serial_number']}" for _, row in seriales.iterrows()]
            return f"Seriales de los equipos:\n\n" + "\n".join(seriales_lista[:20]) + (f"\n\n... y {len(seriales_lista) - 20} más." if len(seriales_lista) > 20 else "")
        else:
            return "No hay información de seriales disponible en los datos."
    
    # 10. Consultas sobre tipos de equipos
    if any(word in query_lower for word in ['tipo', 'tipos', 'modelo', 'modelos']) and any(word in query_lower for word in ['equipo', 'equipos']):
        # Verificar si hay información de tipos de chassis
        if 'chassis_type' in df_chassis.columns:
            tipos = df_chassis[['target', 'chassis_type']].dropna(subset=['chassis_type'])
            
            if tipos.empty:
                return "No hay información de tipos de equipos disponible."
            
            tipos_lista = [f"{row['target']}: {row['chassis_type']}" for _, row in tipos.iterrows()]
            return f"Tipos de equipos:\n\n" + "\n".join(tipos_lista[:20]) + (f"\n\n... y {len(tipos_lista) - 20} más." if len(tipos_lista) > 20 else "")
        else:
            return "No hay información de tipos de equipos disponible en los datos."
    
    # Si no se identifica ninguna intención específica
    return "Lo siento, no pude entender tu consulta. Por favor, intenta reformularla o revisa los ejemplos de preguntas que puedes hacer."
