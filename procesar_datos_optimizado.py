import re
import pandas as pd
import numpy as np
from io import StringIO
import time
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from parser.extraer_ciudad import extraer_ciudad_desde_nombre_equipo, normalizar_ciudad
from parser.extraer_version import extraer_version_timos, extraer_tipo_equipo_desde_version
from parser.extraer_chassis import extraer_info_chassis
from parser.extraer_tipo_equipo import extraer_tipo_equipo_desde_chassis, extraer_tipo_equipo, validar_tipo_equipo

def procesar_datos(contenido):
    """
    Procesa el contenido de los archivos NSP y extrae la información relevante.
    Versión optimizada para mejor rendimiento con grandes volúmenes de datos.
    Compatible con formatos NSP 19 y NSP 24.
    
    Args:
        contenido (str): Contenido concatenado de todos los archivos
        
    Returns:
        tuple: Tupla con los DataFrames (servicios, puertos, descripciones, chassis, versiones, mda, resumen, equipos_no_leidos)
    """
    # Identificar equipos no leídos por errores de conexión
    from parser.identificar_no_leidos import identificar_equipos_no_leidos, crear_dataframe_equipos_no_leidos
    equipos_no_leidos = identificar_equipos_no_leidos(contenido)
    df_no_leidos = crear_dataframe_equipos_no_leidos(equipos_no_leidos)
    
    # PASO 1: Extraer TODOS los targets únicos del contenido con su fuente
    print("Extrayendo todos los targets únicos con fuente...")
    targets_con_fuente = extraer_todos_los_targets_con_fuente(contenido)
    print(f"Total de targets únicos con fuente encontrados: {len(targets_con_fuente)}")
    
    # Obtener lista de targets únicos para procesamiento
    targets_unicos = [target for target, _ in targets_con_fuente]
    
    # Inicializar DataFrames vacíos con tipos de datos predefinidos para optimizar memoria
    df_servicios = pd.DataFrame()
    df_puertos = pd.DataFrame()
    df_descripciones = pd.DataFrame()
    df_chassis = pd.DataFrame()
    df_versiones = pd.DataFrame()
    df_mda = pd.DataFrame()
    
    # Dividir el contenido por bloques de equipo - Compatible con NSP 19 y NSP 24
    t_inicio = time.time()
    
    # MEJORADO: Patrón más flexible para detectar encabezados de todos los formatos NSP
    patron_bloques = r'#\s*Script Name:[^\n]+\s+Script Version:[^\n]+\s+Target:'
    bloques_equipo = re.split(patron_bloques, contenido)
    
    # Eliminar el primer elemento si está vacío
    if bloques_equipo and not bloques_equipo[0].strip():
        bloques_equipo.pop(0)
    
    print(f"Tiempo de división en bloques: {time.time() - t_inicio:.2f} segundos")
    print(f"Número de bloques a procesar: {len(bloques_equipo)}")
    
    # Listas para almacenar resultados de cada equipo
    servicios_list = []
    puertos_list = []
    descripciones_list = []
    chassis_list = []
    versiones_list = []
    mda_list = []
    
    # Función para procesar un bloque de equipo
    def procesar_bloque(bloque):
        if not bloque.strip():
            return None
        
        # Extraer el nombre del target - Compatible con ambos formatos
        target_match = re.match(r'^([^\s#]+)', bloque)
        if not target_match:
            return None
        
        target = target_match.group(1)
        
        # Procesar cada comando en el bloque
        servicios = extraer_servicios(bloque, target)
        puertos = extraer_puertos(bloque, target)
        descripciones = extraer_descripciones_puertos(bloque, target)
        chassis_info = extraer_chassis(bloque, target)
        version = extraer_version(bloque, target)
        mda_info = extraer_mda(bloque, target)
        
        return {
            'target': target,
            'servicios': servicios,
            'puertos': puertos,
            'descripciones': descripciones,
            'chassis': chassis_info,
            'version': version,
            'mda': mda_info
        }
    
    # Procesar bloques en paralelo para equipos con muchos datos
    if len(bloques_equipo) > 10:
        t_inicio = time.time()
        
        with ThreadPoolExecutor(max_workers=min(10, len(bloques_equipo))) as executor:
            # Enviar bloques a procesar
            futures = {executor.submit(procesar_bloque, bloque): i for i, bloque in enumerate(bloques_equipo)}
            
            # Recoger resultados a medida que se completan
            for future in as_completed(futures):
                resultado = future.result()
                if resultado:
                    if resultado['servicios'] is not None:
                        servicios_list.append(resultado['servicios'])
                    if resultado['puertos'] is not None:
                        puertos_list.append(resultado['puertos'])
                    if resultado['descripciones'] is not None:
                        descripciones_list.append(resultado['descripciones'])
                    if resultado['chassis'] is not None:
                        chassis_list.append(resultado['chassis'])
                    if resultado['version'] is not None:
                        versiones_list.append(resultado['version'])
                    if resultado['mda'] is not None:
                        mda_list.append(resultado['mda'])
        
        print(f"Tiempo de procesamiento paralelo: {time.time() - t_inicio:.2f} segundos")
    else:
        # Procesamiento secuencial para pocos equipos
        t_inicio = time.time()
        
        for bloque in bloques_equipo:
            resultado = procesar_bloque(bloque)
            if resultado:
                if resultado['servicios'] is not None:
                    servicios_list.append(resultado['servicios'])
                if resultado['puertos'] is not None:
                    puertos_list.append(resultado['puertos'])
                if resultado['descripciones'] is not None:
                    descripciones_list.append(resultado['descripciones'])
                if resultado['chassis'] is not None:
                    chassis_list.append(resultado['chassis'])
                if resultado['version'] is not None:
                    versiones_list.append(resultado['version'])
                if resultado['mda'] is not None:
                    mda_list.append(resultado['mda'])
        
        print(f"Tiempo de procesamiento secuencial: {time.time() - t_inicio:.2f} segundos")
    
    # Concatenar resultados en DataFrames
    if servicios_list:
        df_servicios = pd.concat(servicios_list, ignore_index=True)
    if puertos_list:
        df_puertos = pd.concat(puertos_list, ignore_index=True)
    if descripciones_list:
        df_descripciones = pd.concat(descripciones_list, ignore_index=True)
    if chassis_list:
        df_chassis = pd.concat(chassis_list, ignore_index=True)
    if versiones_list:
        df_versiones = pd.concat(versiones_list, ignore_index=True)
    if mda_list:
        df_mda = pd.concat(mda_list, ignore_index=True)
    
    # Generar DataFrame de resumen basado en TODOS los targets con fuente
    t_inicio = time.time()
    df_resumen = generar_resumen_completo_con_fuente(targets_con_fuente, df_servicios, df_puertos, df_chassis, df_versiones, bloques_equipo)
    print(f"Tiempo de generación de resumen: {time.time() - t_inicio:.2f} segundos")
    print(f"Total de equipos en resumen: {len(df_resumen)}")
    
    return df_servicios, df_puertos, df_chassis, df_versiones, df_mda, df_resumen, df_no_leidos

def extraer_todos_los_targets_con_fuente(contenido):
    """
    Extrae todos los targets únicos del contenido, preservando la fuente.
    ACTUALIZADO: Ahora detecta la fuente NSP19/NSP24 directamente desde la línea 'Saved Result File Name'.
    
    Args:
        contenido (str): Contenido completo de los archivos
        
    Returns:
        list: Lista de tuplas (target, fuente)
    """
    # Buscar bloques de script con sus targets
    bloques_script = re.findall(r'#\s*Script Name:[^\n]+\s+Script Version:[^\n]+\s+Target:([^\s#\n]+)[\s\S]+?Saved Result File Name:[^\n]*?([^\n]*)', contenido)
    
    # Crear lista de tuplas (target, fuente)
    targets_con_fuente = []
    for target, saved_result in bloques_script:
        # Determinar la fuente basada en la línea 'Saved Result File Name'
        if 'NSP19' in saved_result:
            fuente_normalizada = "NSP19"
        elif 'NSP24' in saved_result:
            fuente_normalizada = "NSP24"
        # Fallback para archivos sin indicación explícita en Saved Result File Name
        elif 'All_Nokia_Devices_NSP19' in contenido:
            fuente_normalizada = "NSP19"
        elif 'All_Nokia_Devices_NSP24' in contenido:
            fuente_normalizada = "NSP24"
        elif 'All Nokia devices' in contenido:
            fuente_normalizada = "NSP24"
        else:
            fuente_normalizada = "NSP19"  # Default a NSP19 si no se puede determinar
        
        targets_con_fuente.append((target, fuente_normalizada))
    
    # Eliminar duplicados exactos (mismo target y misma fuente)
    targets_con_fuente_unicos = []
    targets_vistos = set()
    
    for target, fuente in targets_con_fuente:
        clave = f"{target}_{fuente}"
        if clave not in targets_vistos:
            targets_vistos.add(clave)
            targets_con_fuente_unicos.append((target, fuente))
    
    return sorted(targets_con_fuente_unicos)

def extraer_todos_los_targets(contenido):
    """
    Extrae todos los targets únicos del contenido, independientemente del formato.
    
    Args:
        contenido (str): Contenido completo de los archivos
        
    Returns:
        list: Lista de targets únicos
    """
    # Buscar todos los targets usando expresión regular
    targets = re.findall(r'Target:([^\s#\n]+)', contenido)
    
    # Eliminar duplicados y devolver lista ordenada
    targets_unicos = sorted(list(set(targets)))
    
    return targets_unicos

def generar_resumen_completo_con_fuente(targets_con_fuente, df_servicios, df_puertos, df_chassis, df_versiones, bloques_equipo):
    """
    Genera un DataFrame de resumen basado en TODOS los targets con fuente.
    
    Args:
        targets_con_fuente (list): Lista de tuplas (target, fuente)
        df_servicios (DataFrame): DataFrame con información de servicios
        df_puertos (DataFrame): DataFrame con información de puertos
        df_chassis (DataFrame): DataFrame con información del chassis
        df_versiones (DataFrame): DataFrame con información de versiones
        bloques_equipo (list): Lista de bloques de texto por equipo
        
    Returns:
        DataFrame: DataFrame con el resumen de cada equipo
    """
    # Crear DataFrame de resumen
    resumen_data = []
    
    # Crear diccionario para acceder rápidamente a los bloques por target
    bloques_por_target = {}
    for bloque in bloques_equipo:
        if not bloque.strip():
            continue
        
        target_match = re.match(r'^([^\s#]+)', bloque)
        if target_match:
            target = target_match.group(1)
            bloques_por_target[target] = bloque
    
    for target, fuente in targets_con_fuente:
        # Inicializar datos del equipo
        equipo_data = {
            'target': target,
            'fuente': fuente,
            'target_con_fuente': f"{target}_{fuente}",
            'ciudad': None,
            'ciudad_normalizada': None,
            'total_servicios': 0,
            'total_puertos': 0,
            'puertos_up': 0,
            'puertos_down': 0,
            'puertos_unused': 0,
            'puertos_admin_up_oper_down': 0,  # Nueva columna para puertos con Admin UP pero Port State DOWN
            'temperature': None,
            'serial_number': None,
            'timos_version': None,
            'main_version': None,
            'tipo_equipo_nokia': 'No clasificado',
            'estado': 'Sin datos',
            'razon_estado': 'Sin datos suficientes'  # Nueva columna para explicar la razón del estado
        }
        
        # Extraer código de ciudad del nombre del equipo usando la nueva función
        codigo_ciudad = extraer_ciudad_desde_nombre_equipo(target)
        if codigo_ciudad:
            equipo_data['ciudad'] = codigo_ciudad
            # Normalizar el nombre de la ciudad
            ciudad_normalizada = normalizar_ciudad(codigo_ciudad)
            equipo_data['ciudad_normalizada'] = ciudad_normalizada
        
        # Contar servicios
        if df_servicios is not None and not df_servicios.empty and 'target' in df_servicios.columns:
            servicios_equipo = df_servicios[df_servicios['target'] == target]
            equipo_data['total_servicios'] = len(servicios_equipo)
        
        # Contar puertos y su estado
        if df_puertos is not None and not df_puertos.empty and 'target' in df_puertos.columns:
            puertos_equipo = df_puertos[df_puertos['target'] == target]
            equipo_data['total_puertos'] = len(puertos_equipo)
            
            # Contar puertos por estado
            if 'port_state' in puertos_equipo.columns and 'admin_state' in puertos_equipo.columns:
                equipo_data['puertos_up'] = len(puertos_equipo[puertos_equipo['port_state'] == 'Up'])
                equipo_data['puertos_down'] = len(puertos_equipo[puertos_equipo['port_state'] == 'Down'])
                equipo_data['puertos_unused'] = equipo_data['total_puertos'] - equipo_data['puertos_up'] - equipo_data['puertos_down']
                
                # Contar puertos con Admin UP pero Port State DOWN (crítico)
                equipo_data['puertos_admin_up_oper_down'] = len(puertos_equipo[(puertos_equipo['admin_state'] == 'Up') & (puertos_equipo['port_state'] == 'Down')])
        
        # Obtener temperatura y serial
        if df_chassis is not None and not df_chassis.empty and 'target' in df_chassis.columns:
            chassis_equipo = df_chassis[df_chassis['target'] == target]
            if not chassis_equipo.empty:
                if 'temperature' in chassis_equipo.columns:
                    # Convertir temperatura a float si existe
                    temp_value = chassis_equipo['temperature'].iloc[0]
                    if temp_value is not None:
                        try:
                            equipo_data['temperature'] = float(temp_value)
                        except (ValueError, TypeError):
                            # Si no se puede convertir, dejar como None
                            equipo_data['temperature'] = None
                
                if 'serial_number' in chassis_equipo.columns:
                    equipo_data['serial_number'] = chassis_equipo['serial_number'].iloc[0]
                if 'critical_led' in chassis_equipo.columns:
                    equipo_data['critical_led'] = chassis_equipo['critical_led'].iloc[0]
                if 'fan_status' in chassis_equipo.columns:
                    equipo_data['fan_status'] = chassis_equipo['fan_status'].iloc[0]
        
        # Obtener versión TiMOS y tipo de equipo
        if df_versiones is not None and not df_versiones.empty and 'target' in df_versiones.columns:
            version_equipo = df_versiones[df_versiones['target'] == target]
            if not version_equipo.empty:
                if 'timos_version' in version_equipo.columns:
                    equipo_data['timos_version'] = version_equipo['timos_version'].iloc[0]
                if 'main_version' in version_equipo.columns:
                    equipo_data['main_version'] = version_equipo['main_version'].iloc[0]
                if 'tipo_equipo' in version_equipo.columns:
                    tipo_equipo = version_equipo['tipo_equipo'].iloc[0]
                    if validar_tipo_equipo(tipo_equipo):
                        equipo_data['tipo_equipo_nokia'] = tipo_equipo
        
        # Extraer tipo de equipo directamente del bloque 'show chassis'
        if target in bloques_por_target:
            bloque = bloques_por_target[target]
            tipo_equipo_chassis = extraer_tipo_equipo_desde_chassis(bloque)
            if tipo_equipo_chassis:
                equipo_data['tipo_equipo_nokia'] = tipo_equipo_chassis
        
        # Si aún no se ha asignado un tipo de equipo válido, intentar extraerlo del target
        if equipo_data['tipo_equipo_nokia'] == 'No clasificado':
            tipo_equipo_target = extraer_tipo_equipo(target)
            if tipo_equipo_target != 'No clasificado':
                equipo_data['tipo_equipo_nokia'] = tipo_equipo_target
        
        # Determinar estado del equipo con criterios actualizados y agregar razón
        if equipo_data['total_puertos'] > 0:
            # Inicializar variables para la clasificación
            estado = 'OK'
            razon = 'Equipo funcionando correctamente'
            
            # Verificar puertos con Admin UP pero Port State DOWN (crítico)
            if equipo_data['puertos_admin_up_oper_down'] > 0:
                estado = 'Crítico'
                razon = f"Puertos con Admin UP pero Port State DOWN: {equipo_data['puertos_admin_up_oper_down']} puertos"
            
            # Verificar temperatura crítica (>55°C)
            elif equipo_data['temperature'] is not None and isinstance(equipo_data['temperature'], (int, float)) and equipo_data['temperature'] > 55:
                estado = 'Crítico'
                razon = f"Temperatura crítica: {equipo_data['temperature']}°C"
            
            # Verificar LED crítico encendido
            elif 'critical_led' in equipo_data and equipo_data['critical_led'] == 'On':
                estado = 'Crítico'
                razon = "LED crítico encendido"
            
            # Verificar estado de ventiladores
            elif 'fan_status' in equipo_data and equipo_data['fan_status'] == 'Failed':
                estado = 'Crítico'
                razon = "Ventiladores fallidos"
            
            # Verificar porcentaje de puertos caídos (>50% es crítico)
            elif equipo_data['puertos_down'] > 0:
                porcentaje_down = (equipo_data['puertos_down'] / (equipo_data['puertos_up'] + equipo_data['puertos_down'])) * 100
                if porcentaje_down > 50:
                    estado = 'Crítico'
                    razon = f"Más del 50% de puertos caídos: {porcentaje_down:.1f}%"
                elif porcentaje_down > 30:
                    estado = 'Alerta'
                    razon = f"Más del 30% de puertos caídos: {porcentaje_down:.1f}%"
            
            # Verificar temperatura elevada (45-55°C)
            elif equipo_data['temperature'] is not None and isinstance(equipo_data['temperature'], (int, float)) and equipo_data['temperature'] > 45:
                estado = 'Alerta'
                razon = f"Temperatura elevada: {equipo_data['temperature']}°C"
            
            # Asignar estado y razón
            equipo_data['estado'] = estado
            equipo_data['razon_estado'] = razon
        
        resumen_data.append(equipo_data)
    
    # Crear DataFrame de resumen
    df_resumen = pd.DataFrame(resumen_data)
    
    return df_resumen

def extraer_servicios(bloque, target):
    """
    Extrae la información de servicios del bloque de texto.
    MEJORADO: Compatible con todos los formatos NSP 19 y NSP 24.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de servicios
    """
    # MEJORADO: Patrón más flexible para detectar bloques de servicios en todos los formatos
    servicios_match = re.search(r'show service service-using\s+={3,}[\s\S]+?ServiceId\s+Type\s+Adm\s+Opr\s+CustomerId\s+Service Name[\s\S]+?-{3,}([\s\S]+?)(?:={3,}|\Z)', bloque)
    
    if not servicios_match:
        return None
    
    servicios_text = servicios_match.group(1)
    
    # Extraer líneas de servicios
    lineas = servicios_text.strip().split('\n')
    
    # Filtrar líneas vacías y líneas de separación
    lineas = [linea for linea in lineas if linea.strip() and not linea.strip().startswith('-')]
    
    # Eliminar líneas de resumen al final
    lineas = [linea for linea in lineas if not 'Matching Services' in linea]
    
    # Extraer datos de servicios
    servicios = []
    
    for linea in lineas:
        # Ignorar líneas que no contienen datos de servicios
        if not linea.strip() or 'ServiceId' in linea or 'Matching Services' in linea or '---------' in linea:
            continue
        
        # Extraer campos usando posiciones fijas - Compatible con ambos formatos
        try:
            # Dividir la línea en campos
            campos = linea.split()
            
            if len(campos) >= 5:  # Asegurar que hay suficientes campos
                service_id = campos[0]
                service_type = campos[1]
                admin_state = campos[2]
                oper_state = campos[3]
                customer_id = campos[4]
                
                # El nombre del servicio puede contener espacios, unir el resto de campos
                service_name = ' '.join(campos[5:]) if len(campos) > 5 else ''
                
                # Eliminar asterisco al final si existe (indica truncamiento)
                if service_name.endswith('*'):
                    service_name = service_name[:-1]
                
                # Crear diccionario de servicio
                servicio = {
                    'target': target,
                    'service_id': service_id,
                    'type': service_type,
                    'admin_state': admin_state,
                    'oper_state': oper_state,
                    'customer_id': customer_id,
                    'service_name': service_name
                }
                
                servicios.append(servicio)
        except Exception as e:
            print(f"Error al procesar línea de servicio: {linea} - {str(e)}")
    
    # Crear DataFrame
    if servicios:
        df = pd.DataFrame(servicios)
        
        # Convertir columnas numéricas
        for col in ['service_id', 'customer_id']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    else:
        return None

def extraer_puertos(bloque, target):
    """
    Extrae la información de puertos del bloque de texto.
    MEJORADO: Compatible con todos los formatos NSP 19 y NSP 24.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de puertos
    """
    # MEJORADO: Patrón más flexible para detectar bloques de puertos en todos los formatos
    puertos_match = re.search(r'show port\s+={3,}[\s\S]+?Port\s+Admin\s+Link\s+Port\s+[\s\S]+?-{3,}([\s\S]+?)(?:={3,}|\Z)', bloque)
    
    if not puertos_match:
        return None
    
    puertos_text = puertos_match.group(1)
    
    # Extraer líneas de puertos
    lineas = puertos_text.strip().split('\n')
    
    # Filtrar líneas vacías y líneas de separación
    lineas = [linea for linea in lineas if linea.strip() and not linea.strip().startswith('-')]
    
    # Extraer datos de puertos
    puertos = []
    
    for linea in lineas:
        # Ignorar líneas que no contienen datos de puertos
        if not linea.strip() or 'Port' in linea or '---------' in linea:
            continue
        
        # Extraer campos usando expresiones regulares para mayor flexibilidad
        try:
            # Patrón para extraer ID del puerto
            port_id_match = re.match(r'(\S+)', linea)
            if port_id_match:
                port_id = port_id_match.group(1)
                
                # Extraer estados administrativo y operativo
                admin_state = None
                link = None
                port_state = None
                
                # Buscar estados en la línea
                admin_match = re.search(r'\s+(Up|Down)\s+', linea)
                if admin_match:
                    admin_state = admin_match.group(1)
                
                link_match = re.search(r'\s+(Yes|No)\s+', linea)
                if link_match:
                    link = link_match.group(1)
                
                state_match = re.search(r'\s+(Up|Down)\s+', linea[linea.find(admin_state) + len(admin_state) if admin_state else 0:])
                if state_match:
                    port_state = state_match.group(1)
                
                # Extraer MTU configurado y operativo
                cfg_mtu = None
                oper_mtu = None
                
                mtu_match = re.search(r'\s+(\d+)\s+(\d+)\s+', linea)
                if mtu_match:
                    cfg_mtu = mtu_match.group(1)
                    oper_mtu = mtu_match.group(2)
                
                # Crear diccionario de puerto
                puerto = {
                    'target': target,
                    'port_id': port_id,
                    'admin_state': admin_state,
                    'link': link,
                    'port_state': port_state,
                    'cfg_mtu': cfg_mtu,
                    'oper_mtu': oper_mtu
                }
                
                puertos.append(puerto)
        except Exception as e:
            print(f"Error al procesar línea de puerto: {linea} - {str(e)}")
    
    # Crear DataFrame
    if puertos:
        df = pd.DataFrame(puertos)
        
        # Convertir columnas numéricas
        for col in ['cfg_mtu', 'oper_mtu']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    else:
        return None

def extraer_descripciones_puertos(bloque, target):
    """
    Extrae las descripciones de los puertos del bloque de texto.
    MEJORADO: Compatible con todos los formatos NSP 19 y NSP 24.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con las descripciones de los puertos
    """
    # MEJORADO: Patrón más flexible para detectar bloques de descripciones en todos los formatos
    descripciones_match = re.search(r'show port description\s+={3,}[\s\S]+?Port\s+Description[\s\S]+?-{3,}([\s\S]+?)(?:={3,}|\Z)', bloque)
    
    if not descripciones_match:
        return None
    
    descripciones_text = descripciones_match.group(1)
    
    # Extraer líneas de descripciones
    lineas = descripciones_text.strip().split('\n')
    
    # Filtrar líneas vacías y líneas de separación
    lineas = [linea for linea in lineas if linea.strip() and not linea.strip().startswith('-')]
    
    # Extraer datos de descripciones
    descripciones = []
    
    for linea in lineas:
        # Ignorar líneas que no contienen datos de descripciones
        if not linea.strip() or 'Port' in linea or '---------' in linea:
            continue
        
        # Extraer campos usando expresiones regulares para mayor flexibilidad
        try:
            # Patrón para extraer ID del puerto y descripción
            desc_match = re.match(r'(\S+)\s+(.*)', linea)
            if desc_match:
                port_id = desc_match.group(1)
                description = desc_match.group(2).strip()
                
                # Crear diccionario de descripción
                descripcion = {
                    'target': target,
                    'port_id': port_id,
                    'description': description
                }
                
                descripciones.append(descripcion)
        except Exception as e:
            print(f"Error al procesar línea de descripción: {linea} - {str(e)}")
    
    # Crear DataFrame
    if descripciones:
        df = pd.DataFrame(descripciones)
        return df
    else:
        return None

def extraer_chassis(bloque, target):
    """
    Extrae la información del chassis del bloque de texto.
    MEJORADO: Compatible con todos los formatos NSP 19 y NSP 24.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información del chassis
    """
    # Usar la función especializada para extraer información del chassis
    # Corregido: Ahora solo pasamos el bloque, no el target
    chassis_info = extraer_info_chassis(bloque)
    
    if chassis_info:
        # Añadir el target al diccionario de información del chassis
        chassis_info['target'] = target
        
        # Convertir temperatura a float si existe
        if 'temperature' in chassis_info and chassis_info['temperature'] is not None:
            try:
                chassis_info['temperature'] = float(chassis_info['temperature'])
            except (ValueError, TypeError):
                # Si no se puede convertir, dejar como None
                chassis_info['temperature'] = None
        
        # Crear DataFrame con la información del chassis
        df = pd.DataFrame([chassis_info])
        return df
    else:
        return None

def extraer_version(bloque, target):
    """
    Extrae la información de versión del bloque de texto.
    MEJORADO: Compatible con todos los formatos NSP 19 y NSP 24.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de versión
    """
    # Extraer versión TiMOS usando la función especializada
    timos_version, main_version = extraer_version_timos(bloque)
    
    # Extraer tipo de equipo desde la versión
    tipo_equipo = extraer_tipo_equipo_desde_version(bloque)
    
    if timos_version or tipo_equipo:
        # Crear diccionario con la información de versión
        version_info = {
            'target': target,
            'timos_version': timos_version,
            'main_version': main_version,
            'tipo_equipo': tipo_equipo
        }
        
        # Crear DataFrame con la información de versión
        df = pd.DataFrame([version_info])
        return df
    else:
        return None

def extraer_mda(bloque, target):
    """
    Extrae la información de MDA del bloque de texto.
    MEJORADO: Compatible con todos los formatos NSP 19 y NSP 24.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de MDA
    """
    # MEJORADO: Patrón más flexible para detectar bloques de MDA en todos los formatos
    mda_match = re.search(r'show card detail\s+={3,}[\s\S]+?Slot\s+Provisioned\s+Equipped[\s\S]+?-{3,}([\s\S]+?)(?:={3,}|\Z)', bloque)
    
    if not mda_match:
        # Intentar con otro formato
        mda_match = re.search(r'show mda\s+={3,}[\s\S]+?Slot\s+Mda\s+Admin\s+Operational[\s\S]+?-{3,}([\s\S]+?)(?:={3,}|\Z)', bloque)
        
        if not mda_match:
            return None
    
    mda_text = mda_match.group(1)
    
    # Extraer líneas de MDA
    lineas = mda_text.strip().split('\n')
    
    # Filtrar líneas vacías y líneas de separación
    lineas = [linea for linea in lineas if linea.strip() and not linea.strip().startswith('-')]
    
    # Extraer datos de MDA
    mdas = []
    
    for linea in lineas:
        # Ignorar líneas que no contienen datos de MDA
        if not linea.strip() or 'Slot' in linea or '---------' in linea:
            continue
        
        # Extraer campos usando expresiones regulares para mayor flexibilidad
        try:
            # Dividir la línea en campos
            campos = linea.split()
            
            if len(campos) >= 3:  # Asegurar que hay suficientes campos
                slot = campos[0]
                
                # Determinar el tipo de MDA según el formato
                mda_type = None
                provisioned_type = None
                equipped_type = None
                admin_state = None
                oper_state = None
                
                if len(campos) >= 4 and ('up' in campos[2].lower() or 'down' in campos[2].lower()):
                    # Formato show mda
                    mda_type = campos[1]
                    admin_state = campos[2]
                    oper_state = campos[3]
                else:
                    # Formato show card detail
                    provisioned_type = campos[1]
                    equipped_type = campos[2]
                
                # Extraer información de puertos si está disponible
                ports_up = 0
                ports_down = 0
                ports_unused = 0
                
                # Buscar información de puertos en la línea
                ports_match = re.search(r'(\d+)/(\d+)/(\d+)', linea)
                if ports_match:
                    ports_up = int(ports_match.group(1))
                    ports_down = int(ports_match.group(2))
                    ports_unused = int(ports_match.group(3))
                
                # Crear diccionario de MDA
                mda = {
                    'target': target,
                    'slot': slot,
                    'mda_type': mda_type,
                    'provisioned_type': provisioned_type,
                    'equipped_type': equipped_type,
                    'admin_state': admin_state,
                    'oper_state': oper_state,
                    'ports_up': ports_up,
                    'ports_down': ports_down,
                    'ports_unused': ports_unused
                }
                
                mdas.append(mda)
        except Exception as e:
            print(f"Error al procesar línea de MDA: {linea} - {str(e)}")
    
    # Crear DataFrame
    if mdas:
        df = pd.DataFrame(mdas)
        return df
    else:
        return None
