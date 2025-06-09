import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def mostrar_por_equipo(df_resumen, df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda):
    """
    Muestra la vista unificada por equipo, con exportación individual.
    
    Args:
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
        df_descripciones (DataFrame): DataFrame con información de descripciones de puertos
        df_chassis (DataFrame): DataFrame con información de chasis
        df_versiones (DataFrame): DataFrame con información de versiones
        df_mda (DataFrame): DataFrame con información de tarjetas MDA
    """
    st.header("Vista por Equipo")
    
    if df_resumen.empty:
        st.warning("No hay datos de equipos para mostrar.")
        return
    
    # Crear selectbox para elegir equipo
    equipos = sorted(df_resumen['target'].unique())
    equipo_seleccionado = st.selectbox("Seleccionar Equipo", equipos)
    
    if not equipo_seleccionado:
        st.info("Seleccione un equipo para ver sus detalles.")
        return
    
    # Filtrar datos del equipo seleccionado
    resumen_equipo = df_resumen[df_resumen['target'] == equipo_seleccionado].iloc[0] if not df_resumen[df_resumen['target'] == equipo_seleccionado].empty else None
    servicios_equipo = df_servicios[df_servicios['target'] == equipo_seleccionado] if not df_servicios.empty else pd.DataFrame()
    puertos_equipo = df_puertos[df_puertos['target'] == equipo_seleccionado] if not df_puertos.empty else pd.DataFrame()
    descripciones_equipo = df_descripciones[df_descripciones['target'] == equipo_seleccionado] if not df_descripciones.empty else pd.DataFrame()
    chassis_equipo = df_chassis[df_chassis['target'] == equipo_seleccionado].iloc[0] if not df_chassis[df_chassis['target'] == equipo_seleccionado].empty else None
    version_equipo = df_versiones[df_versiones['target'] == equipo_seleccionado].iloc[0] if not df_versiones[df_versiones['target'] == equipo_seleccionado].empty else None
    mda_equipo = df_mda[df_mda['target'] == equipo_seleccionado] if not df_mda.empty else pd.DataFrame()
    
    # Mostrar información general del equipo
    st.subheader(f"Información General: {equipo_seleccionado}")
    
    # Crear columnas para métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if resumen_equipo is not None:
            st.metric("Total Servicios", resumen_equipo['total_servicios'])
    
    with col2:
        if resumen_equipo is not None:
            st.metric("Total Puertos", resumen_equipo['total_puertos'])
    
    with col3:
        if resumen_equipo is not None:
            st.metric("Puertos Activos", resumen_equipo['puertos_up'])
    
    with col4:
        if resumen_equipo is not None:
            st.metric("Estado", resumen_equipo['status'])
    
    # Crear tabs para diferentes secciones
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Chasis", "Servicios", "Puertos", "Tarjetas MDA", "Exportar"])
    
    with tab1:
        st.write("### Información de Chasis")
        
        if chassis_equipo is not None:
            # Crear columnas para información de chasis
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Nombre:** {chassis_equipo['name']}")
                st.write(f"**Tipo:** {chassis_equipo['type']}")
                st.write(f"**Ubicación:** {chassis_equipo['location']}")
                st.write(f"**Temperatura:** {chassis_equipo['temperature']}")
            
            with col2:
                st.write(f"**LED Crítico:** {chassis_equipo['critical_led']}")
                st.write(f"**LED Mayor:** {chassis_equipo['major_led']}")
                st.write(f"**Estado Temperatura Alta:** {chassis_equipo['over_temp']}")
                st.write(f"**Estado Ventiladores:** {chassis_equipo['fan_status']}")
            
            # Mostrar versión TiMOS
            if version_equipo is not None:
                st.write("### Información de Versión")
                st.write(f"**Versión TiMOS:** {version_equipo['timos_version']}")
                st.write(f"**Versión Principal:** {version_equipo['main_version']}")
        else:
            st.info("No hay información de chasis disponible para este equipo.")
    
    with tab2:
        st.write("### Servicios")
        
        if not servicios_equipo.empty:
            # Mostrar tabla de servicios
            st.dataframe(servicios_equipo[['service_id', 'type', 'admin_state', 'oper_state', 'customer_id', 'service_name']])
            
            # Gráfico de tipos de servicios
            st.write("#### Distribución de Tipos de Servicios")
            
            # Contar servicios por tipo
            servicios_por_tipo = servicios_equipo['type'].value_counts().reset_index()
            servicios_por_tipo.columns = ['Tipo', 'Cantidad']
            
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(x='Tipo', y='Cantidad', data=servicios_por_tipo, ax=ax)
            ax.set_title(f'Tipos de Servicios en {equipo_seleccionado}')
            ax.set_xlabel('Tipo de Servicio')
            ax.set_ylabel('Cantidad')
            
            # Mostrar valores en las barras
            for i, v in enumerate(servicios_por_tipo['Cantidad']):
                ax.text(i, v + 0.1, str(v), ha='center')
            
            st.pyplot(fig)
        else:
            st.info("No hay información de servicios disponible para este equipo.")
    
    with tab3:
        st.write("### Puertos")
        
        if not puertos_equipo.empty:
            # Mostrar tabla de puertos
            st.dataframe(puertos_equipo[['port_id', 'admin_state', 'link', 'port_state', 'port_mode', 'port_encp', 'port_type', 'media_type']])
            
            # Unir con descripciones si están disponibles
            if not descripciones_equipo.empty:
                st.write("#### Descripciones de Puertos")
                st.dataframe(descripciones_equipo[['port_id', 'description']])
            
            # Gráfico de estado de puertos
            st.write("#### Estado de Puertos")
            
            # Contar puertos por estado
            puertos_up = len(puertos_equipo[puertos_equipo['port_state'] == 'Up'])
            puertos_down = len(puertos_equipo[puertos_equipo['port_state'] == 'Down'])
            puertos_ghost = len(puertos_equipo[puertos_equipo['port_state'] == 'Ghost'])
            puertos_otros = len(puertos_equipo) - puertos_up - puertos_down - puertos_ghost
            
            # Crear DataFrame para el gráfico
            estado_puertos = pd.DataFrame({
                'Estado': ['Up', 'Down', 'Ghost', 'Otros'],
                'Cantidad': [puertos_up, puertos_down, puertos_ghost, puertos_otros]
            })
            
            # Filtrar estados con cantidad > 0
            estado_puertos = estado_puertos[estado_puertos['Cantidad'] > 0]
            
            if not estado_puertos.empty:
                fig, ax = plt.subplots(figsize=(8, 5))
                
                # Definir colores según estado
                colors = {'Up': 'green', 'Down': 'red', 'Ghost': 'orange', 'Otros': 'gray'}
                bar_colors = [colors.get(estado, 'blue') for estado in estado_puertos['Estado']]
                
                sns.barplot(x='Estado', y='Cantidad', data=estado_puertos, palette=bar_colors, ax=ax)
                ax.set_title(f'Estado de Puertos en {equipo_seleccionado}')
                ax.set_xlabel('Estado')
                ax.set_ylabel('Cantidad')
                
                # Mostrar valores en las barras
                for i, v in enumerate(estado_puertos['Cantidad']):
                    ax.text(i, v + 0.1, str(v), ha='center')
                
                st.pyplot(fig)
        else:
            st.info("No hay información de puertos disponible para este equipo.")
    
    with tab4:
        st.write("### Tarjetas MDA")
        
        if not mda_equipo.empty:
            # Mostrar tabla de tarjetas MDA
            st.dataframe(mda_equipo[['slot_mda', 'provisioned_type', 'equipped_type', 'admin_state', 'oper_state', 'max_ports', 'temperature']])
        else:
            st.info("No hay información de tarjetas MDA disponible para este equipo.")
    
    with tab5:
        st.write("### Exportar Información del Equipo")
        
        # Botón para exportar información del equipo
        if st.button(f"Exportar datos de {equipo_seleccionado}"):
            # Crear un diccionario con los DataFrames a exportar
            dfs_to_export = {
                'Resumen': pd.DataFrame([resumen_equipo]) if resumen_equipo is not None else pd.DataFrame(),
                'Servicios': servicios_equipo,
                'Puertos': puertos_equipo,
                'Descripciones': descripciones_equipo,
                'Chasis': pd.DataFrame([chassis_equipo]) if chassis_equipo is not None else pd.DataFrame(),
                'Version': pd.DataFrame([version_equipo]) if version_equipo is not None else pd.DataFrame(),
                'MDA': mda_equipo
            }
            
            # Llamar a la función de exportación (implementada en utils/exportar_excel.py)
            from utils.exportar_excel import exportar_excel
            
            # Exportar a Excel
            excel_file = exportar_excel(dfs_to_export, f"{equipo_seleccionado}_datos.xlsx")
            
            # Mostrar enlace de descarga
            st.success(f"Datos de {equipo_seleccionado} exportados correctamente.")
            st.download_button(
                label="Descargar Excel",
                data=excel_file,
                file_name=f"{equipo_seleccionado}_datos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
