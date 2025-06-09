import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def mostrar_por_ciudad(df_resumen):
    """
    Muestra la vista agrupada por ciudad con métricas y gráficas.
    
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
    
    # Agrupar por ciudad
    ciudades_stats = df_con_ciudad.groupby('ciudad').agg({
        'target': 'count',
        'total_servicios': 'sum',
        'total_puertos': 'sum',
        'puertos_up': 'sum',
        'puertos_down': 'sum',
        'puertos_unused': 'sum'
    }).reset_index()
    
    # Renombrar columnas
    ciudades_stats = ciudades_stats.rename(columns={
        'target': 'total_equipos'
    })
    
    # Calcular porcentaje de puertos activos
    ciudades_stats['porcentaje_puertos_activos'] = (ciudades_stats['puertos_up'] / ciudades_stats['total_puertos'] * 100).round(1)
    
    # Mostrar tabla de resumen por ciudad
    st.subheader("Resumen por Ciudad")
    st.dataframe(ciudades_stats)
    
    # Gráfico de equipos por ciudad
    st.subheader("Distribución de Equipos por Ciudad")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='ciudad', y='total_equipos', data=ciudades_stats, ax=ax)
    ax.set_title('Cantidad de Equipos por Ciudad')
    ax.set_xlabel('Ciudad')
    ax.set_ylabel('Cantidad de Equipos')
    
    # Mostrar valores en las barras
    for i, v in enumerate(ciudades_stats['total_equipos']):
        ax.text(i, v + 0.1, str(v), ha='center')
    
    st.pyplot(fig)
    
    # Gráfico de servicios por ciudad
    st.subheader("Distribución de Servicios por Ciudad")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='ciudad', y='total_servicios', data=ciudades_stats, ax=ax)
    ax.set_title('Cantidad de Servicios por Ciudad')
    ax.set_xlabel('Ciudad')
    ax.set_ylabel('Cantidad de Servicios')
    
    # Mostrar valores en las barras
    for i, v in enumerate(ciudades_stats['total_servicios']):
        ax.text(i, v + 0.1, str(v), ha='center')
    
    st.pyplot(fig)
    
    # Gráfico de puertos activos por ciudad
    st.subheader("Porcentaje de Puertos Activos por Ciudad")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
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
    
    # Crear gráfico de barras
    bars = sns.barplot(x='ciudad', y='porcentaje_puertos_activos', data=ciudades_stats_sorted, palette=colors, ax=ax)
    ax.set_title('Porcentaje de Puertos Activos por Ciudad')
    ax.set_xlabel('Ciudad')
    ax.set_ylabel('Porcentaje de Puertos Activos')
    ax.set_ylim(0, 100)  # Establecer límite de 0 a 100%
    
    # Mostrar valores en las barras
    for i, v in enumerate(ciudades_stats_sorted['porcentaje_puertos_activos']):
        ax.text(i, v + 1, f"{v}%", ha='center')
    
    st.pyplot(fig)
    
    # Mostrar equipos por ciudad
    st.subheader("Detalle de Equipos por Ciudad")
    
    # Crear selectbox para elegir ciudad
    ciudades = sorted(df_con_ciudad['ciudad'].unique())
    ciudad_seleccionada = st.selectbox("Seleccionar Ciudad", ciudades)
    
    if ciudad_seleccionada:
        # Filtrar equipos de la ciudad seleccionada
        equipos_ciudad = df_con_ciudad[df_con_ciudad['ciudad'] == ciudad_seleccionada]
        
        # Mostrar tabla de equipos
        st.dataframe(equipos_ciudad[['target', 'total_servicios', 'total_puertos', 
                                    'puertos_up', 'puertos_down', 'timos_version', 'status']])
