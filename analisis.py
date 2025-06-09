import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def mostrar_analisis(df_resumen, df_puertos, df_chassis, df_versiones, df_mda):
    """
    Muestra el análisis inteligente del estado de la red.
    
    Args:
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        df_puertos (DataFrame): DataFrame con información de puertos
        df_chassis (DataFrame): DataFrame con información de chasis
        df_versiones (DataFrame): DataFrame con información de versiones
        df_mda (DataFrame): DataFrame con información de tarjetas MDA
    """
    st.header("Análisis Inteligente de Estado de Red")
    
    if df_resumen.empty:
        st.warning("No hay datos suficientes para realizar el análisis.")
        return
    
    # Contar equipos por estado
    estado_counts = df_resumen['status'].value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Cantidad']
    
    # Mostrar resumen de estado
    st.subheader("Resumen de Estado de Equipos")
    
    # Crear columnas para métricas
    col1, col2, col3 = st.columns(3)
    
    # Obtener conteos por estado
    ok_count = estado_counts[estado_counts['Estado'] == 'OK']['Cantidad'].sum() if 'OK' in estado_counts['Estado'].values else 0
    alerta_count = estado_counts[estado_counts['Estado'] == 'Alerta']['Cantidad'].sum() if 'Alerta' in estado_counts['Estado'].values else 0
    critico_count = estado_counts[estado_counts['Estado'] == 'Crítico']['Cantidad'].sum() if 'Crítico' in estado_counts['Estado'].values else 0
    
    # Calcular porcentajes
    total_equipos = len(df_resumen)
    ok_percent = round((ok_count / total_equipos) * 100, 1) if total_equipos > 0 else 0
    alerta_percent = round((alerta_count / total_equipos) * 100, 1) if total_equipos > 0 else 0
    critico_percent = round((critico_count / total_equipos) * 100, 1) if total_equipos > 0 else 0
    
    # Mostrar métricas
    with col1:
        st.metric("Equipos OK", f"{ok_count} ({ok_percent}%)")
    
    with col2:
        st.metric("Equipos en Alerta", f"{alerta_count} ({alerta_percent}%)")
    
    with col3:
        st.metric("Equipos Críticos", f"{critico_count} ({critico_percent}%)")
    
    # Gráfico de estado
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Definir colores según estado
    colors = {'OK': 'green', 'Alerta': 'orange', 'Crítico': 'red'}
    bar_colors = [colors.get(estado, 'blue') for estado in estado_counts['Estado']]
    
    sns.barplot(x='Estado', y='Cantidad', data=estado_counts, palette=bar_colors, ax=ax)
    ax.set_title('Cantidad de Equipos por Estado')
    ax.set_xlabel('Estado')
    ax.set_ylabel('Cantidad de Equipos')
    
    # Mostrar valores en las barras
    for i, v in enumerate(estado_counts['Cantidad']):
        ax.text(i, v + 0.1, str(v), ha='center')
    
    st.pyplot(fig)
    
    # Gráfico de pastel para distribución de estado
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Crear gráfico de pastel
    wedges, texts, autotexts = ax.pie(
        estado_counts['Cantidad'], 
        labels=estado_counts['Estado'],
        autopct='%1.1f%%',
        startangle=90,
        colors=[colors.get(estado, 'blue') for estado in estado_counts['Estado']]
    )
    
    # Personalizar texto
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
    
    ax.set_title('Distribución de Equipos por Estado')
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    st.pyplot(fig)
    
    # Análisis de criterios de clasificación
    st.subheader("Criterios de Clasificación")
    
    # Crear tabs para diferentes criterios
    tab1, tab2, tab3, tab4 = st.tabs(["Temperatura", "Puertos sin Uso", "Versión TiMOS", "Ventiladores"])
    
    with tab1:
        st.write("### Equipos con Temperatura Crítica (> 60°C)")
        
        # Filtrar equipos con temperatura crítica
        equipos_temp_critica = []
        for _, row in df_chassis.iterrows():
            if row['temperature'] and row['temperature'].endswith('C'):
                try:
                    temp = int(row['temperature'][:-1])
                    if temp > 60:
                        equipos_temp_critica.append(row['target'])
                except (ValueError, AttributeError):
                    pass
        
        if equipos_temp_critica:
            # Filtrar equipos con temperatura crítica
            temp_critica_df = df_resumen[df_resumen['target'].isin(equipos_temp_critica)]
            
            st.dataframe(temp_critica_df[['target', 'ciudad', 'temperature', 'status']])
            st.warning(f"Se encontraron {len(equipos_temp_critica)} equipos con temperatura crítica (> 60°C).")
        else:
            st.success("No se encontraron equipos con temperatura crítica.")
    
    with tab2:
        st.write("### Equipos con Alto Porcentaje de Puertos sin Uso (> 50%)")
        
        # Filtrar equipos con alto porcentaje de puertos sin uso
        equipos_puertos_sin_uso = []
        for _, row in df_resumen.iterrows():
            if row['total_puertos'] > 0:
                unused_percent = (row['puertos_unused'] / row['total_puertos']) * 100
                if unused_percent > 50:
                    equipos_puertos_sin_uso.append(row['target'])
        
        if equipos_puertos_sin_uso:
            # Filtrar equipos con alto porcentaje de puertos sin uso
            puertos_sin_uso_df = df_resumen[df_resumen['target'].isin(equipos_puertos_sin_uso)]
            
            # Calcular porcentaje de puertos sin uso
            puertos_sin_uso_df['porcentaje_sin_uso'] = (puertos_sin_uso_df['puertos_unused'] / puertos_sin_uso_df['total_puertos'] * 100).round(1)
            
            st.dataframe(puertos_sin_uso_df[['target', 'ciudad', 'total_puertos', 'puertos_unused', 'porcentaje_sin_uso', 'status']])
            st.warning(f"Se encontraron {len(equipos_puertos_sin_uso)} equipos con más del 50% de puertos sin uso.")
        else:
            st.success("No se encontraron equipos con alto porcentaje de puertos sin uso.")
    
    with tab3:
        st.write("### Equipos con Versiones TiMOS Obsoletas (< 8.0)")
        
        # Filtrar equipos con versiones obsoletas
        equipos_version_obsoleta = []
        for _, row in df_versiones.iterrows():
            try:
                version = row['main_version']
                if version:
                    version_num = float(version.split('.')[0])
                    if version_num < 8.0:
                        equipos_version_obsoleta.append(row['target'])
            except (ValueError, AttributeError, IndexError):
                pass
        
        if equipos_version_obsoleta:
            # Filtrar equipos con versiones obsoletas
            version_obsoleta_df = df_resumen[df_resumen['target'].isin(equipos_version_obsoleta)]
            
            st.dataframe(version_obsoleta_df[['target', 'ciudad', 'timos_version', 'status']])
            st.warning(f"Se encontraron {len(equipos_version_obsoleta)} equipos con versiones TiMOS obsoletas (< 8.0).")
        else:
            st.success("No se encontraron equipos con versiones TiMOS obsoletas.")
    
    with tab4:
        st.write("### Equipos con Ventiladores Fallidos")
        
        # Filtrar equipos con ventiladores fallidos - VERSIÓN CORREGIDA
        equipos_ventiladores_fallidos = df_chassis[df_chassis['fan_status'].notna() & df_chassis['fan_status'].str.lower().eq('failed')]['target'].tolist()
        
        if equipos_ventiladores_fallidos:
            # Filtrar equipos con ventiladores fallidos
            ventiladores_fallidos_df = df_resumen[df_resumen['target'].isin(equipos_ventiladores_fallidos)]
            
            st.dataframe(ventiladores_fallidos_df[['target', 'ciudad', 'status']])
            st.warning(f"Se encontraron {len(equipos_ventiladores_fallidos)} equipos con ventiladores fallidos.")
        else:
            st.success("No se encontraron equipos con ventiladores fallidos.")
    
    # Mostrar todos los equipos con su estado
    st.subheader("Estado Detallado de Todos los Equipos")
    
    # Crear filtro por estado
    estados = ['Todos'] + sorted(df_resumen['status'].unique().tolist())
    estado_seleccionado = st.selectbox("Filtrar por Estado", estados)
    
    if estado_seleccionado == 'Todos':
        equipos_filtrados = df_resumen
    else:
        equipos_filtrados = df_resumen[df_resumen['status'] == estado_seleccionado]
    
    # Mostrar tabla con equipos filtrados
    st.dataframe(equipos_filtrados[['target', 'ciudad', 'total_servicios', 'total_puertos', 
                                   'puertos_up', 'puertos_down', 'puertos_unused', 
                                   'timos_version', 'temperature', 'status']])
