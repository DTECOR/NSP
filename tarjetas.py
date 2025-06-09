import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def mostrar_tarjetas(df_mda, df_resumen):
    """
    Muestra el inventario de tarjetas MDA.
    
    Args:
        df_mda (DataFrame): DataFrame con información de tarjetas MDA
        df_resumen (DataFrame): DataFrame con el resumen de equipos
    """
    st.header("Inventario de Tarjetas MDA")
    
    if df_mda.empty:
        st.warning("No se encontraron datos de tarjetas MDA en los equipos analizados.")
        return
    
    # Verificar si hay datos de tarjetas
    if 'provisioned_type' not in df_mda.columns or df_mda['provisioned_type'].isna().all():
        st.warning("No se encontraron datos de tarjetas MDA en los equipos analizados.")
        return
    
    # Agrupar por tipo de tarjeta
    tarjetas_count = df_mda['provisioned_type'].value_counts().reset_index()
    tarjetas_count.columns = ['Tipo de Tarjeta', 'Cantidad']
    
    # Mostrar tabla de tipos de tarjetas
    st.subheader("Distribución de Tipos de Tarjetas MDA")
    st.dataframe(tarjetas_count)
    
    # Gráfico de tipos de tarjetas
    st.subheader("Distribución de Tarjetas MDA por Tipo")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x='Tipo de Tarjeta', y='Cantidad', data=tarjetas_count, ax=ax)
    ax.set_title('Cantidad de Tarjetas MDA por Tipo')
    ax.set_xlabel('Tipo de Tarjeta')
    ax.set_ylabel('Cantidad')
    plt.xticks(rotation=45, ha='right')
    
    # Mostrar valores en las barras
    for i, v in enumerate(tarjetas_count['Cantidad']):
        ax.text(i, v + 0.1, str(v), ha='center')
    
    st.pyplot(fig)
    
    # Verificar inconsistencias entre tipo provisionado y equipado
    st.subheader("Inconsistencias en Tarjetas MDA")
    
    # Filtrar tarjetas con tipo equipado diferente al provisionado
    inconsistencias = df_mda[df_mda['equipped_type'].notna() & 
                            (df_mda['provisioned_type'] != df_mda['equipped_type'])]
    
    if not inconsistencias.empty:
        st.warning(f"Se encontraron {len(inconsistencias)} tarjetas MDA con inconsistencias entre tipo provisionado y equipado.")
        st.dataframe(inconsistencias[['target', 'slot_mda', 'provisioned_type', 'equipped_type', 'admin_state', 'oper_state']])
    else:
        st.success("No se encontraron inconsistencias entre tipos provisionados y equipados.")
    
    # Verificar tarjetas con problemas operativos
    problemas_operativos = df_mda[(df_mda['admin_state'] == 'up') & (df_mda['oper_state'] != 'up')]
    
    if not problemas_operativos.empty:
        st.subheader("Tarjetas MDA con Problemas Operativos")
        st.warning(f"Se encontraron {len(problemas_operativos)} tarjetas MDA con problemas operativos.")
        st.dataframe(problemas_operativos[['target', 'slot_mda', 'provisioned_type', 'admin_state', 'oper_state']])
    
    # Verificar tarjetas con temperatura alta
    tarjetas_temp_alta = []
    for _, row in df_mda.iterrows():
        if row['temperature'] and row['temperature'].endswith('C'):
            try:
                temp = int(row['temperature'][:-1])
                if temp > 60:
                    tarjetas_temp_alta.append(row)
            except (ValueError, AttributeError):
                pass
    
    if tarjetas_temp_alta:
        st.subheader("Tarjetas MDA con Temperatura Alta")
        st.warning(f"Se encontraron {len(tarjetas_temp_alta)} tarjetas MDA con temperatura alta (> 60°C).")
        df_temp_alta = pd.DataFrame(tarjetas_temp_alta)
        st.dataframe(df_temp_alta[['target', 'slot_mda', 'provisioned_type', 'temperature']])
    
    # Mostrar detalle de todas las tarjetas
    st.subheader("Detalle de Tarjetas MDA por Equipo")
    
    # Crear selectbox para elegir equipo
    equipos = sorted(df_mda['target'].unique())
    equipo_seleccionado = st.selectbox("Seleccionar Equipo", equipos)
    
    if equipo_seleccionado:
        # Filtrar tarjetas del equipo seleccionado
        tarjetas_equipo = df_mda[df_mda['target'] == equipo_seleccionado]
        
        # Mostrar tabla de tarjetas
        st.dataframe(tarjetas_equipo[['slot_mda', 'provisioned_type', 'equipped_type', 
                                     'admin_state', 'oper_state', 'max_ports', 'temperature']])
