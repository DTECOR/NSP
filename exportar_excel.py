import pandas as pd
import io

def exportar_excel(dfs, filename=None):
    """
    Exporta múltiples DataFrames a un archivo Excel.
    
    Args:
        dfs (dict): Diccionario con nombres de hojas y DataFrames
        filename (str, optional): Nombre del archivo Excel. Si es None, se devuelve el contenido en memoria.
        
    Returns:
        bytes: Contenido del archivo Excel en memoria si filename es None
        bool: True si se guardó correctamente en disco
    """
    # Crear un objeto BytesIO para guardar el Excel en memoria
    output = io.BytesIO()
    
    # Crear un escritor de Excel
    with pd.ExcelWriter(output, engine=\'openpyxl\') as writer:
        # Escribir cada DataFrame en una hoja separada
        for sheet_name, df in dfs.items():
            # Asegurarse de que df sea un DataFrame y no None
            if df is None:
                df = pd.DataFrame() # Convertir None a un DataFrame vacío
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Si se especificó un nombre de archivo, guardar en disco
    if filename:
        with open(filename, \'wb\') as f:
            f.write(output.getvalue())
        return True
    
    # Si no se especificó un nombre de archivo, devolver el contenido en memoria
    output.seek(0)
    return output.getvalue()

def exportar_todo(df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda, df_resumen, filename=None):
    """
    Exporta todos los DataFrames a un archivo Excel.
    
    Args:
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
        df_descripciones (DataFrame): DataFrame con información de descripciones de puertos
        df_chassis (DataFrame): DataFrame con información de chasis
        df_versiones (DataFrame): DataFrame con información de versiones
        df_mda (DataFrame): DataFrame con información de tarjetas MDA
        df_resumen (DataFrame): DataFrame con el resumen de equipos
        filename (str, optional): Nombre del archivo Excel. Si es None, se devuelve el contenido en memoria.
        
    Returns:
        bytes: Contenido del archivo Excel en memoria si filename es None
        bool: True si se guardó correctamente en disco
    """
    # Crear un diccionario con los DataFrames a exportar
    dfs = {
        \'Resumen\': df_resumen,
        \'Servicios\': df_servicios,
        \'Puertos\': df_puertos,
        \'Descripciones\': df_descripciones,
        \'Chasis\': df_chassis,
        \'Versiones\': df_versiones,
        \'MDA\': df_mda
    }
    
    # Exportar a Excel
    return exportar_excel(dfs, filename)


