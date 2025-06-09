import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def mostrar_dashboard(df_resumen, df_servicios, df_puertos):
    """
    Muestra el dashboard principal con métricas generales y gráficas.
    
    Args:
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
    """
    st.header("Dashboard General")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Equipos", len(df_resumen))
    
    with col2:
        total_servicios = df_resumen['total_servicios'].sum()
        st.metric("Total Servicios", total_servicios)
    
    with col3:
        total_puertos = df_resumen['total_puertos'].sum()
        st.metric("Total Puertos", total_puertos)
    
    with col4:
        # Calcular porcentaje de puertos activos
        puertos_up = df_resumen['puertos_up'].sum()
        if total_puertos > 0:
            porcentaje_activos = round((puertos_up / total_puertos) * 100, 1)
            st.metric("Puertos Activos", f"{porcentaje_activos}%")
        else:
            st.metric("Puertos Activos", "0%")
    
    # Estado general de equipos
    st.subheader("Estado de Equipos")
    
    # Contar equipos por estado
    estado_counts = df_resumen['status'].value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Cantidad']
    
    # Crear gráfico de barras para estado de equipos
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
    
    # Distribución de servicios por equipo
    st.subheader("Distribución de Servicios por Equipo")
    
    # Ordenar equipos por cantidad de servicios
    top_servicios = df_resumen.sort_values('total_servicios', ascending=False).head(10)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x='target', y='total_servicios', data=top_servicios, ax=ax)
    ax.set_title('Top 10 Equipos por Cantidad de Servicios')
    ax.set_xlabel('Equipo')
    ax.set_ylabel('Cantidad de Servicios')
    plt.xticks(rotation=45, ha='right')
    
    # Mostrar valores en las barras
    for i, v in enumerate(top_servicios['total_servicios']):
        ax.text(i, v + 0.1, str(v), ha='center')
    
    st.pyplot(fig)
    
    # Distribución de puertos por estado
    st.subheader("Distribución de Puertos por Estado")
    
    # Calcular totales de puertos por estado
    total_up = df_resumen['puertos_up'].sum()
    total_down = df_resumen['puertos_down'].sum()
    total_unused = df_resumen['puertos_unused'].sum()
    
    # Crear DataFrame para el gráfico
    puertos_estado = pd.DataFrame({
        'Estado': ['Activos (Up)', 'Caídos (Down)', 'Sin Usar'],
        'Cantidad': [total_up, total_down, total_unused]
    })
    
    # Crear gráfico de pastel
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Definir colores
    colors = ['green', 'red', 'gray']
    
    # Crear gráfico de pastel
    wedges, texts, autotexts = ax.pie(
        puertos_estado['Cantidad'], 
        labels=puertos_estado['Estado'],
        autopct='%1.1f%%',
        startangle=90,
        colors=colors
    )
    
    # Personalizar texto
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
    
    ax.set_title('Distribución de Puertos por Estado')
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    st.pyplot(fig)
    
    # Tabla de resumen
    st.subheader("Resumen por Equipo")
    
    # Mostrar tabla con información resumida
    st.dataframe(df_resumen[['target', 'ciudad', 'total_servicios', 'total_puertos', 
                            'puertos_up', 'puertos_down', 'timos_version', 'status']])
