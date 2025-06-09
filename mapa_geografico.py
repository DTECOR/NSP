import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import plotly.express as px

def mostrar_mapa_geografico(df_resumen):
    """
    Muestra un mapa geográfico interactivo de Colombia con los equipos y su estado.
    
    Args:
        df_resumen: DataFrame con información resumida de los equipos
    """
    st.header("Mapa Geográfico de Equipos")
    
    # Explicación de la visualización
    st.markdown("""
    Este mapa muestra la ubicación geográfica de los equipos en Colombia, con códigos de color según su estado:
    - 🟢 **Verde**: Equipos en estado OK
    - 🟡 **Amarillo**: Equipos en estado de Alerta
    - 🔴 **Rojo**: Equipos en estado Crítico
    
    Puede hacer zoom, desplazarse y hacer clic en los marcadores para ver más detalles.
    """)
    
    # Definir coordenadas de las ciudades colombianas
    coordenadas_ciudades = {
        # Códigos estándar
        'BAQ': [10.9639, -74.7964],  # Barranquilla
        'BOG': [4.7110, -74.0721],   # Bogotá
        'BGA': [7.1254, -73.1198],   # Bucaramanga (corregido)
        'CAL': [3.4516, -76.5320],   # Cali
        'CLO': [3.4516, -76.5320],   # Cali (mismo que CAL)
        'CTG': [10.3932, -75.4832],  # Cartagena
        'CUC': [7.8939, -72.5078],   # Cúcuta
        'IBE': [4.4389, -75.2322],   # Ibagué
        'MON': [8.7575, -75.8878],   # Montería
        'PPN': [2.4448, -76.6147],   # Popayán
        'SBL': [9.3047, -75.3977],   # Sincelejo
        'SIN': [9.3047, -75.3977],   # Sincelejo (mismo que SBL)
        'BUC': [7.1254, -73.1198],   # Bucaramanga
        
        # Casos especiales mencionados
        'PAS': [1.2136, -77.2811],   # Pasto
        'SMA': [11.2404, -74.1990],  # Santa Marta
        'SMT': [11.2404, -74.1990],  # Santa Marta (mismo que SMA)
        'VDP': [10.4631, -73.2532],  # Valledupar
        'VUP': [10.4631, -73.2532],  # Valledupar (mismo que VDP)
        'WOM': [4.7110, -74.0721]    # WOM sin ciudad (usamos Bogotá como referencia)
    }
    
    # Crear un mapa centrado en Colombia
    m = folium.Map(location=[4.5709, -74.2973], zoom_start=6)
    
    # Añadir capa de mapa base
    folium.TileLayer('cartodbpositron').add_to(m)
    
    # Crear clusters de marcadores para mejor rendimiento
    marker_cluster = MarkerCluster().add_to(m)
    
    # Contador de equipos por ciudad y estado
    equipos_por_ciudad = {}
    
    # Importar función de extracción de ciudad
    from parser.extraer_ciudad import extraer_ciudad_desde_nombre_equipo
    
    # Añadir marcadores para cada equipo
    for _, equipo in df_resumen.iterrows():
        # Extraer código de ciudad del nombre del equipo usando la función especializada
        codigo_ciudad = extraer_ciudad_desde_nombre_equipo(equipo['target'])
        
        # Verificar si el código de ciudad está en nuestras coordenadas conocidas
        if codigo_ciudad in coordenadas_ciudades:
            # Determinar el color según el estado
            if 'estado' in equipo:
                if equipo['estado'] == 'Crítico':
                    color = 'red'
                elif equipo['estado'] == 'Alerta':
                    color = 'orange'
                else:
                    color = 'green'
            else:
                # Si no hay estado, usar temperatura o algún otro indicador
                if 'temperature' in equipo and equipo['temperature'] > 50:
                    color = 'red'
                elif 'puertos_down' in equipo and equipo['puertos_down'] > 10:
                    color = 'orange'
                else:
                    color = 'green'
            
            # Crear popup con información del equipo
            popup_text = f"""
            <b>Equipo:</b> {equipo['target']}<br>
            <b>Tipo:</b> {equipo.get('type', 'No disponible')}<br>
            <b>Temperatura:</b> {equipo.get('temperature', 'No disponible')}°C<br>
            <b>Servicios:</b> {equipo.get('total_servicios', 'No disponible')}<br>
            <b>Puertos:</b> {equipo.get('total_puertos', 'No disponible')}<br>
            <b>Puertos Up:</b> {equipo.get('puertos_up', 'No disponible')}<br>
            <b>Puertos Down:</b> {equipo.get('puertos_down', 'No disponible')}<br>
            <b>TMOS:</b> {equipo.get('timos_version', 'No disponible')}<br>
            """
            
            # Añadir marcador al cluster
            folium.Marker(
                location=coordenadas_ciudades[codigo_ciudad],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=equipo['target'],
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(marker_cluster)
            
            # Actualizar contador de equipos por ciudad
            if codigo_ciudad not in equipos_por_ciudad:
                equipos_por_ciudad[codigo_ciudad] = {'total': 0, 'ok': 0, 'alerta': 0, 'critico': 0}
            
            equipos_por_ciudad[codigo_ciudad]['total'] += 1
            
            if color == 'green':
                equipos_por_ciudad[codigo_ciudad]['ok'] += 1
            elif color == 'orange':
                equipos_por_ciudad[codigo_ciudad]['alerta'] += 1
            else:
                equipos_por_ciudad[codigo_ciudad]['critico'] += 1
    
    # Mostrar el mapa
    st.subheader("Mapa de Equipos por Ciudad")
    folium_static(m, width=1000, height=600)
    
    # Crear DataFrame para visualización de estadísticas por ciudad
    ciudades = []
    totales = []
    ok = []
    alerta = []
    critico = []
    
    for ciudad, datos in equipos_por_ciudad.items():
        ciudades.append(ciudad)
        totales.append(datos['total'])
        ok.append(datos['ok'])
        alerta.append(datos['alerta'])
        critico.append(datos['critico'])
    
    df_ciudades = pd.DataFrame({
        'Ciudad': ciudades,
        'Total Equipos': totales,
        'OK': ok,
        'Alerta': alerta,
        'Crítico': critico
    })
    
    # Mostrar estadísticas por ciudad
    st.subheader("Estadísticas por Ciudad")
    st.dataframe(df_ciudades)
    
    # Crear gráfico de barras apiladas para visualizar distribución de estados por ciudad
    fig = px.bar(
        df_ciudades, 
        x='Ciudad', 
        y=['OK', 'Alerta', 'Crítico'],
        title='Distribución de Estados por Ciudad',
        labels={'value': 'Cantidad de Equipos', 'variable': 'Estado'},
        color_discrete_map={'OK': 'green', 'Alerta': 'orange', 'Crítico': 'red'}
    )
    
    st.plotly_chart(fig)
