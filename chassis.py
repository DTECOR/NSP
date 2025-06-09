import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def mostrar_chassis(df_chassis, df_resumen):
    """
    Muestra el inventario de chasis por equipo.
    
    Args:
        df_chassis (DataFrame): DataFrame con información de chasis
        df_resumen (DataFrame): DataFrame con el resumen de equipos
    """
    st.header("Inventario de Chasis")
    
    if df_chassis.empty:
        st.warning("No se encontraron datos de chasis en los equipos analizados.")
        return
    
    # Verificar si hay datos de tipo de chasis
    if 'type' not in df_chassis.columns or df_chassis['type'].isna().all():
        st.warning("No se encontraron datos de tipo de chasis en los equipos analizados.")
        return
    
    # Agrupar por tipo de chasis
    chassis_count = df_chassis['type'].value_counts().reset_index()
    chassis_count.columns = ['Tipo de Chasis', 'Cantidad']
    
    # Mostrar tabla de tipos de chasis
    st.subheader("Distribución de Tipos de Chasis")
    st.dataframe(chassis_count)
    
    # Gráfico de tipos de chasis
    st.subheader("Distribución de Chasis por Tipo")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x='Tipo de Chasis', y='Cantidad', data=chassis_count, ax=ax)
    ax.set_title('Cantidad de Chasis por Tipo')
    ax.set_xlabel('Tipo de Chasis')
    ax.set_ylabel('Cantidad')
    plt.xticks(rotation=45, ha='right')
    
    # Mostrar valores en las barras
    for i, v in enumerate(chassis_count['Cantidad']):
        ax.text(i, v + 0.1, str(v), ha='center')
    
    st.pyplot(fig)
    
    # Análisis de temperatura
    st.subheader("Análisis de Temperatura de Chasis")
    
    # Extraer temperaturas numéricas
    temperaturas = []
    for _, row in df_chassis.iterrows():
        if row['temperature'] and row['temperature'].endswith('C'):
            try:
                temp = int(row['temperature'][:-1])
                temperaturas.append({
                    'target': row['target'],
                    'temperatura': temp,
                    'tipo': row['type']
                })
            except (ValueError, AttributeError):
                pass
    
    if temperaturas:
        df_temp = pd.DataFrame(temperaturas)
        
        # Gráfico de temperatura por equipo
        st.subheader("Temperatura por Equipo")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Ordenar por temperatura
        df_temp_sorted = df_temp.sort_values('temperatura', ascending=False)
        
        # Definir colores según temperatura
        colors = []
        for temp in df_temp_sorted['temperatura']:
            if temp > 60:
                colors.append('red')
            elif temp > 45:
                colors.append('orange')
            else:
                colors.append('green')
        
        # Crear gráfico de barras
        bars = sns.barplot(x='target', y='temperatura', data=df_temp_sorted.head(20), palette=colors, ax=ax)
        ax.set_title('Top 20 Equipos por Temperatura')
        ax.set_xlabel('Equipo')
        ax.set_ylabel('Temperatura (°C)')
        plt.xticks(rotation=45, ha='right')
        
        # Añadir línea de temperatura crítica
        ax.axhline(y=60, color='red', linestyle='--', label='Temperatura Crítica (60°C)')
        ax.axhline(y=45, color='orange', linestyle='--', label='Temperatura Alta (45°C)')
        ax.legend()
        
        # Mostrar valores en las barras
        for i, v in enumerate(df_temp_sorted.head(20)['temperatura']):
            ax.text(i, v + 1, f"{v}°C", ha='center')
        
        st.pyplot(fig)
        
        # Equipos con temperatura crítica
        temp_critica = df_temp[df_temp['temperatura'] > 60]
        if not temp_critica.empty:
            st.warning(f"Se encontraron {len(temp_critica)} equipos con temperatura crítica (> 60°C).")
            
            # Unir con información de resumen
            temp_critica_info = pd.merge(temp_critica, 
                                        df_resumen[['target', 'ciudad', 'status']], 
                                        on='target', how='left')
            
            st.dataframe(temp_critica_info[['target', 'ciudad', 'tipo', 'temperatura', 'status']])
    else:
        st.info("No se pudieron extraer datos de temperatura para análisis.")
    
    # Análisis de estado de ventiladores
    st.subheader("Estado de Ventiladores")
    
    if 'fan_status' in df_chassis.columns:
        fan_status_count = df_chassis['fan_status'].value_counts().reset_index()
        fan_status_count.columns = ['Estado', 'Cantidad']
        
        if not fan_status_count.empty:
            # Gráfico de estado de ventiladores
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Definir colores según estado
            colors = []
            for estado in fan_status_count['Estado']:
                if estado and estado.lower() == 'up':
                    colors.append('green')
                elif estado and estado.lower() == 'failed':
                    colors.append('red')
                else:
                    colors.append('gray')
            
            # Crear gráfico de barras
            sns.barplot(x='Estado', y='Cantidad', data=fan_status_count, palette=colors, ax=ax)
            ax.set_title('Estado de Ventiladores')
            ax.set_xlabel('Estado')
            ax.set_ylabel('Cantidad de Equipos')
            
            # Mostrar valores en las barras
            for i, v in enumerate(fan_status_count['Cantidad']):
                ax.text(i, v + 0.1, str(v), ha='center')
            
            st.pyplot(fig)
            
            # Equipos con ventiladores fallidos
            # Versión corregida para evitar el error de ambigüedad
            ventiladores_fallidos = df_chassis[df_chassis['fan_status'].notna() & df_chassis['fan_status'].str.lower().eq('failed')]
            
            if not ventiladores_fallidos.empty:
                st.warning(f"Se encontraron {len(ventiladores_fallidos)} equipos con ventiladores fallidos.")
                
                # Unir con información de resumen
                ventiladores_fallidos_info = pd.merge(ventiladores_fallidos[['target', 'type', 'fan_status']], 
                                                    df_resumen[['target', 'ciudad', 'status']], 
                                                    on='target', how='left')
                
                st.dataframe(ventiladores_fallidos_info[['target', 'ciudad', 'type', 'fan_status', 'status']])
    
    # Mostrar detalle de todos los chasis
    st.subheader("Detalle de Chasis por Equipo")
    
    # Crear selectbox para elegir equipo
    equipos = sorted(df_chassis['target'].unique())
    equipo_seleccionado = st.selectbox("Seleccionar Equipo", equipos, key="chassis_equipo_select")
    
    if equipo_seleccionado:
        # Filtrar chasis del equipo seleccionado
        chassis_equipo = df_chassis[df_chassis['target'] == equipo_seleccionado]
        
        # Mostrar tabla de chasis
        st.dataframe(chassis_equipo[['name', 'type', 'location', 'temperature', 
                                    'critical_led', 'major_led', 'over_temp', 'fan_status']])
