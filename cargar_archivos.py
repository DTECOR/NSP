import os
import glob
import streamlit as st

def cargar_archivos_automaticamente(directorio="InformeNokia"):
    """
    Carga automáticamente todos los archivos .txt del directorio especificado.
    
    Args:
        directorio (str): Ruta al directorio que contiene los archivos .txt
        
    Returns:
        str: Contenido concatenado de todos los archivos
    """
    # Obtener la ruta absoluta del directorio
    ruta_absoluta = os.path.abspath(directorio)
    
    # Buscar todos los archivos .txt en el directorio
    archivos = glob.glob(os.path.join(ruta_absoluta, "*.txt"))
    
    if not archivos:
        return None
    
    # Leer y concatenar el contenido de todos los archivos
    contenido_total = ""
    for archivo in archivos:
        try:
            with open(archivo, 'r', encoding='utf-8', errors='ignore') as f:
                contenido = f.read()
                contenido_total += contenido + "\n\n"
        except Exception as e:
            st.error(f"Error al leer el archivo {os.path.basename(archivo)}: {str(e)}")
    
    return contenido_total

def cargar_archivos_manual(archivos_subidos):
    """
    Procesa los archivos subidos manualmente por el usuario.
    
    Args:
        archivos_subidos (list): Lista de archivos subidos a través de st.file_uploader
        
    Returns:
        str: Contenido concatenado de todos los archivos
    """
    if not archivos_subidos:
        return None
    
    # Leer y concatenar el contenido de todos los archivos subidos
    contenido_total = ""
    for archivo in archivos_subidos:
        try:
            contenido = archivo.getvalue().decode('utf-8', errors='ignore')
            contenido_total += contenido + "\n\n"
        except Exception as e:
            st.error(f"Error al leer el archivo {archivo.name}: {str(e)}")
    
    return contenido_total
