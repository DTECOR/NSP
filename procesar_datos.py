import re
import pandas as pd
import numpy as np
from io import StringIO

def procesar_datos(contenido):
    """
    Procesa el contenido de los archivos NSP y extrae la información relevante.
    
    Args:
        contenido (str): Contenido concatenado de todos los archivos
        
    Returns:
        tuple: Tupla con los DataFrames (servicios, puertos, descripciones, chassis, versiones, mda, resumen)
    """
    # Inicializar DataFrames vacíos
    df_servicios = pd.DataFrame()
    df_puertos = pd.DataFrame()
    df_descripciones = pd.DataFrame()
    df_chassis = pd.DataFrame()
    df_versiones = pd.DataFrame()
    df_mda = pd.DataFrame()
    df_resumen = pd.DataFrame()
    
    # Dividir el contenido por bloques de equipo
    bloques_equipo = re.split(r'#\s*Script Name:Services_Inventory\s+Script Version:1\s+Target:', contenido)
    
    # Eliminar el primer elemento si está vacío
    if bloques_equipo and not bloques_equipo[0].strip():
        bloques_equipo.pop(0)
    
    # Procesar cada bloque de equipo
    for bloque in bloques_equipo:
        if not bloque.strip():
            continue
        
        # Extraer el nombre del target
        target_match = re.match(r'^([^\s#]+)', bloque)
        if not target_match:
            continue
        
        target = target_match.group(1)
        
        # Procesar cada comando en el bloque
        servicios = extraer_servicios(bloque, target)
        puertos = extraer_puertos(bloque, target)
        descripciones = extraer_descripciones_puertos(bloque, target)
        chassis_info = extraer_chassis(bloque, target)
        version = extraer_version(bloque, target)
        mda_info = extraer_mda(bloque, target)
        
        # Agregar a los DataFrames principales
        if servicios is not None and not servicios.empty:
            df_servicios = pd.concat([df_servicios, servicios], ignore_index=True)
        
        if puertos is not None and not puertos.empty:
            df_puertos = pd.concat([df_puertos, puertos], ignore_index=True)
        
        if descripciones is not None and not descripciones.empty:
            df_descripciones = pd.concat([df_descripciones, descripciones], ignore_index=True)
        
        if chassis_info is not None and not chassis_info.empty:
            df_chassis = pd.concat([df_chassis, chassis_info], ignore_index=True)
        
        if version is not None and not version.empty:
            df_versiones = pd.concat([df_versiones, version], ignore_index=True)
        
        if mda_info is not None and not mda_info.empty:
            df_mda = pd.concat([df_mda, mda_info], ignore_index=True)
    
    # Generar DataFrame de resumen
    df_resumen = generar_resumen(df_servicios, df_puertos, df_chassis, df_versiones)
    
    return df_servicios, df_puertos, df_descripciones, df_chassis, df_versiones, df_mda, df_resumen

def extraer_servicios(bloque, target):
    """
    Extrae la información de servicios del bloque de texto.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de servicios
    """
    # Buscar el bloque de servicios
    servicios_match = re.search(r'show service service-using\s+={10,}[\s\S]+?ServiceId\s+Type\s+Adm\s+Opr\s+CustomerId\s+Service Name\s+-{10,}([\s\S]+?)(?:={10,}|Matching Services)', bloque)
    
    if not servicios_match:
        return None
    
    servicios_texto = servicios_match.group(1).strip()
    
    # Crear un DataFrame con los servicios
    servicios_data = []
    
    for linea in servicios_texto.split('\n'):
        linea = linea.strip()
        if not linea or '-' * 10 in linea:
            continue
        
        # Extraer campos de la línea
        match = re.match(r'(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(.*)', linea)
        if match:
            service_id, tipo, adm, opr, customer_id, service_name = match.groups()
            
            # Eliminar el asterisco de truncamiento si existe
            if service_name.endswith('*'):
                service_name = service_name[:-1]
            
            servicios_data.append({
                'target': target,
                'service_id': int(service_id),
                'type': tipo,
                'admin_state': adm,
                'oper_state': opr,
                'customer_id': int(customer_id),
                'service_name': service_name
            })
    
    if not servicios_data:
        return None
    
    return pd.DataFrame(servicios_data)

def extraer_puertos(bloque, target):
    """
    Extrae la información de puertos del bloque de texto.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de puertos
    """
    # Buscar los bloques de puertos
    puertos_matches = re.finditer(r'Ports on Slot\s+\S+\s+={10,}[\s\S]+?Port\s+Admin Link Port\s+Cfg\s+Oper LAG/[\s\S]+?Id\s+State\s+State\s+MTU\s+MTU\s+Bndl[\s\S]+?-{10,}([\s\S]+?)(?:={10,}|$)', bloque)
    
    if not puertos_matches:
        return None
    
    puertos_data = []
    
    for match in puertos_matches:
        puertos_texto = match.group(1).strip()
        
        for linea in puertos_texto.split('\n'):
            linea = linea.strip()
            if not linea or '-' * 10 in linea:
                continue
            
            # Extraer campos de la línea
            campos = re.split(r'\s{2,}', linea)
            if len(campos) < 4:  # Necesitamos al menos port_id, admin_state, link y port_state
                continue
            
            port_id = campos[0].strip()
            admin_state = campos[1].strip()
            link = campos[2].strip()
            port_state = campos[3].strip()
            
            # Extraer los demás campos si están disponibles
            cfg_mtu = None
            oper_mtu = None
            lag = None
            port_mode = None
            port_encp = None
            port_type = None
            media_type = None
            
            if len(campos) > 4 and campos[4].strip():
                try:
                    cfg_mtu = int(campos[4].strip())
                except ValueError:
                    cfg_mtu = None
            
            if len(campos) > 5 and campos[5].strip():
                try:
                    oper_mtu = int(campos[5].strip())
                except ValueError:
                    oper_mtu = None
            
            if len(campos) > 6 and campos[6].strip():
                lag = campos[6].strip()
            
            if len(campos) > 7 and campos[7].strip():
                port_mode = campos[7].strip()
            
            if len(campos) > 8 and campos[8].strip():
                port_encp = campos[8].strip()
            
            if len(campos) > 9 and campos[9].strip():
                port_type = campos[9].strip()
            
            if len(campos) > 10 and campos[10].strip():
                media_type = campos[10].strip()
                # Eliminar el asterisco de truncamiento si existe
                if media_type.endswith('*'):
                    media_type = media_type[:-1]
            
            puertos_data.append({
                'target': target,
                'port_id': port_id,
                'admin_state': admin_state,
                'link': link,
                'port_state': port_state,
                'cfg_mtu': cfg_mtu,
                'oper_mtu': oper_mtu,
                'lag': lag,
                'port_mode': port_mode,
                'port_encp': port_encp,
                'port_type': port_type,
                'media_type': media_type
            })
    
    if not puertos_data:
        return None
    
    return pd.DataFrame(puertos_data)

def extraer_descripciones_puertos(bloque, target):
    """
    Extrae las descripciones de puertos del bloque de texto.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con las descripciones de puertos
    """
    # Buscar los bloques de descripciones de puertos
    desc_matches = re.finditer(r'Port Descriptions on Slot\s+\S+\s+={10,}[\s\S]+?Port Id\s+Description\s+-{10,}([\s\S]+?)(?:={10,}|$)', bloque)
    
    if not desc_matches:
        return None
    
    descripciones_data = []
    
    for match in desc_matches:
        desc_texto = match.group(1).strip()
        
        # Procesar líneas de descripción
        port_id = None
        description = ""
        
        for linea in desc_texto.split('\n'):
            linea = linea.strip()
            if not linea or '-' * 10 in linea:
                continue
            
            # Verificar si es una nueva entrada de puerto o continuación de descripción
            if re.match(r'^\S+/\S+(/\S+)?', linea):  # Formato típico de port_id: 1/1/1
                # Si ya teníamos un puerto, guardarlo antes de empezar uno nuevo
                if port_id:
                    descripciones_data.append({
                        'target': target,
                        'port_id': port_id,
                        'description': description.strip()
                    })
                
                # Extraer el nuevo port_id y descripción
                match_port = re.match(r'^(\S+/\S+(/\S+)?)\s+(.*)', linea)
                if match_port:
                    port_id = match_port.group(1)
                    description = match_port.group(3)
                else:
                    port_id = None
                    description = ""
            else:
                # Continuación de la descripción
                if port_id:
                    description += " " + linea
        
        # Guardar el último puerto procesado
        if port_id:
            descripciones_data.append({
                'target': target,
                'port_id': port_id,
                'description': description.strip()
            })
    
    if not descripciones_data:
        return None
    
    return pd.DataFrame(descripciones_data)

def extraer_chassis(bloque, target):
    """
    Extrae la información del chasis del bloque de texto.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información del chasis
    """
    # Buscar el bloque de información del chasis
    chassis_match = re.search(r'show chassis\s+={10,}[\s\S]+?Chassis Information\s+={10,}([\s\S]+?)(?:Environment Information|={10,})', bloque)
    
    if not chassis_match:
        return None
    
    chassis_texto = chassis_match.group(1).strip()
    
    # Extraer campos específicos
    name_match = re.search(r'Name\s+:\s+(.+)', chassis_texto)
    type_match = re.search(r'Type\s+:\s+(.+)', chassis_texto)
    location_match = re.search(r'Location\s+:\s+(.+)', chassis_texto)
    temperature_match = re.search(r'Temperature\s+:\s+(.+)', chassis_texto)
    critical_led_match = re.search(r'Critical LED state\s+:\s+(.+)', chassis_texto)
    major_led_match = re.search(r'Major LED state\s+:\s+(.+)', chassis_texto)
    over_temp_match = re.search(r'Over Temperature state\s+:\s+(.+)', chassis_texto)
    
    # Buscar información de ventiladores
    fan_match = re.search(r'Fan tray number\s+:\s+\d+\s+Speed\s+:\s+.+\s+Status\s+:\s+(.+)', bloque)
    
    chassis_data = {
        'target': target,
        'name': name_match.group(1).strip() if name_match else None,
        'type': type_match.group(1).strip() if type_match else None,
        'location': location_match.group(1).strip() if location_match else None,
        'temperature': temperature_match.group(1).strip() if temperature_match else None,
        'critical_led': critical_led_match.group(1).strip() if critical_led_match else None,
        'major_led': major_led_match.group(1).strip() if major_led_match else None,
        'over_temp': over_temp_match.group(1).strip() if over_temp_match else None,
        'fan_status': fan_match.group(1).strip() if fan_match else None
    }
    
    return pd.DataFrame([chassis_data])

def extraer_version(bloque, target):
    """
    Extrae la información de versión del bloque de texto.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de versión
    """
    # Buscar la línea de versión
    version_match = re.search(r'show version\s+(TiMOS-[^\s]+\s+[^\s]+\s+[^\s]+\s+[^\s]+\s+[^\s]+)', bloque)
    
    if not version_match:
        return None
    
    version_completa = version_match.group(1).strip()
    
    # Extraer la versión principal
    main_version_match = re.search(r'TiMOS-[A-Z]-([0-9]+\.[0-9]+\.[A-Z][0-9]+)', version_completa)
    main_version = main_version_match.group(1) if main_version_match else None
    
    version_data = {
        'target': target,
        'timos_version': version_completa,
        'main_version': main_version
    }
    
    return pd.DataFrame([version_data])

def extraer_mda(bloque, target):
    """
    Extrae la información de las tarjetas MDA del bloque de texto.
    
    Args:
        bloque (str): Bloque de texto del equipo
        target (str): Nombre del equipo
        
    Returns:
        DataFrame: DataFrame con la información de las tarjetas MDA
    """
    # Buscar los bloques de MDA
    mda_matches = re.finditer(r'MDA\s+(\S+)\s+detail\s+={10,}[\s\S]+?Slot\s+Mda\s+Provisioned Type\s+Admin\s+Operational[\s\S]+?-{10,}([\s\S]+?)(?:MDA Specific Data|={10,})', bloque)
    
    if not mda_matches:
        return None
    
    mda_data = []
    
    for match in mda_matches:
        slot_mda = match.group(1).strip()
        mda_texto = match.group(2).strip()
        
        # Extraer tipo provisionado, tipo equipado y estados
        mda_line_match = re.search(r'(\S+)\s+(\S+)\s+(\S+[^(]*?)(?:\s+\(([^)]+)\))?\s+(\S+)\s+(\S+)', mda_texto)
        
        if not mda_line_match:
            continue
        
        # Extraer el número máximo de puertos
        max_ports_match = re.search(r'Maximum port count\s+:\s+(\d+)', bloque)
        max_ports = int(max_ports_match.group(1)) if max_ports_match else None
        
        # Extraer temperatura
        temp_match = re.search(r'Temperature\s+:\s+(\S+)', bloque)
        temperature = temp_match.group(1) if temp_match else None
        
        # Determinar si hay grupos
        if len(mda_line_match.groups()) >= 6:
            slot, mda, provisioned_type, equipped_type, admin_state, oper_state = mda_line_match.groups()
        else:
            slot, mda, provisioned_type = mda_line_match.groups()[:3]
            equipped_type = None
            admin_state, oper_state = mda_line_match.groups()[3:5] if len(mda_line_match.groups()) >= 5 else (None, None)
        
        mda_data.append({
            'target': target,
            'slot_mda': slot_mda,
            'provisioned_type': provisioned_type.strip(),
            'equipped_type': equipped_type.strip() if equipped_type else None,
            'admin_state': admin_state.strip() if admin_state else None,
            'oper_state': oper_state.strip() if oper_state else None,
            'max_ports': max_ports,
            'temperature': temperature
        })
    
    if not mda_data:
        return None
    
    return pd.DataFrame(mda_data)

def generar_resumen(df_servicios, df_puertos, df_chassis, df_versiones):
    """
    Genera un DataFrame de resumen con información consolidada.
    
    Args:
        df_servicios (DataFrame): DataFrame de servicios
        df_puertos (DataFrame): DataFrame de puertos
        df_chassis (DataFrame): DataFrame de chasis
        df_versiones (DataFrame): DataFrame de versiones
        
    Returns:
        DataFrame: DataFrame de resumen
    """
    # Obtener lista única de targets
    targets = set()
    
    if df_servicios is not None and not df_servicios.empty:
        targets.update(df_servicios['target'].unique())
    
    if df_puertos is not None and not df_puertos.empty:
        targets.update(df_puertos['target'].unique())
    
    if df_chassis is not None and not df_chassis.empty:
        targets.update(df_chassis['target'].unique())
    
    if df_versiones is not None and not df_versiones.empty:
        targets.update(df_versiones['target'].unique())
    
    # Crear DataFrame de resumen
    resumen_data = []
    
    for target in targets:
        # Contar servicios
        total_servicios = 0
        if df_servicios is not None and not df_servicios.empty:
            servicios_target = df_servicios[df_servicios['target'] == target]
            total_servicios = len(servicios_target)
        
        # Contar puertos y estados
        total_puertos = 0
        puertos_up = 0
        puertos_down = 0
        puertos_unused = 0
        
        if df_puertos is not None and not df_puertos.empty:
            puertos_target = df_puertos[df_puertos['target'] == target]
            total_puertos = len(puertos_target)
            
            # Contar por estado
            if 'port_state' in puertos_target.columns:
                puertos_up = len(puertos_target[puertos_target['port_state'] == 'Up'])
                puertos_down = len(puertos_target[puertos_target['port_state'] == 'Down'])
                puertos_unused = total_puertos - puertos_up - puertos_down
        
        # Obtener versión TiMOS
        timos_version = None
        if df_versiones is not None and not df_versiones.empty:
            version_target = df_versiones[df_versiones['target'] == target]
            if not version_target.empty and 'main_version' in version_target.columns:
                timos_version = version_target.iloc[0]['main_version']
        
        # Obtener tipo de chasis y temperatura
        chassis_type = None
        temperature = None
        fan_status = None
        
        if df_chassis is not None and not df_chassis.empty:
            chassis_target = df_chassis[df_chassis['target'] == target]
            if not chassis_target.empty:
                if 'type' in chassis_target.columns:
                    chassis_type = chassis_target.iloc[0]['type']
                if 'temperature' in chassis_target.columns:
                    temperature = chassis_target.iloc[0]['temperature']
                if 'fan_status' in chassis_target.columns:
                    fan_status = chassis_target.iloc[0]['fan_status']
        
        # Determinar estado general
        status = "OK"
        
        # Verificar temperatura
        if temperature and temperature.endswith('C'):
            try:
                temp_value = int(temperature[:-1])
                if temp_value > 60:
                    status = "Crítico"
            except ValueError:
                pass
        
        # Verificar puertos sin uso
        if total_puertos > 0:
            unused_percent = (puertos_unused / total_puertos) * 100
            if unused_percent > 50:
                status = "Alerta" if status == "OK" else status
        
        # Verificar versión TiMOS
        if timos_version:
            try:
                version_major = float(timos_version.split('.')[0])
                if version_major < 8.0:
                    status = "Alerta" if status == "OK" else status
            except ValueError:
                pass
        
        # Verificar estado de ventiladores
        if fan_status and fan_status.lower() == "failed":
            status = "Crítico"
        
        # Extraer prefijo de ciudad
        ciudad = None
        if target:
            ciudad_match = re.match(r'^([A-Z]{3})_', target)
            if ciudad_match:
                ciudad = ciudad_match.group(1)
        
        resumen_data.append({
            'target': target,
            'ciudad': ciudad,
            'total_servicios': total_servicios,
            'total_puertos': total_puertos,
            'puertos_up': puertos_up,
            'puertos_down': puertos_down,
            'puertos_unused': puertos_unused,
            'timos_version': timos_version,
            'chassis_type': chassis_type,
            'temperature': temperature,
            'status': status
        })
    
    return pd.DataFrame(resumen_data)
