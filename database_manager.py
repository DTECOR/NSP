import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import json
from sqlalchemy import create_engine
from contextlib import contextmanager

class DatabaseManager:
    """
    Clase para gestionar la conexión y operaciones con la base de datos PostgreSQL.
    """
    
    def __init__(self, config_file=None, connection_string=None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            config_file (str, optional): Ruta al archivo de configuración JSON.
            connection_string (str, optional): Cadena de conexión directa a PostgreSQL.
        """
        self.connection_params = None
        self.engine = None
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.connection_params = json.load(f)
        elif connection_string:
            self.connection_string = connection_string
        else:
            # Valores por defecto para desarrollo local
            self.connection_params = {
                'dbname': 'nsp_visualizer',
                'user': 'postgres',
                'password': 'postgres',
                'host': 'localhost',
                'port': '5432'
            }
    
    @contextmanager
    def get_connection(self):
        """
        Contexto para obtener una conexión a la base de datos.
        
        Yields:
            connection: Conexión a la base de datos PostgreSQL.
        """
        connection = None
        try:
            if hasattr(self, 'connection_string'):
                connection = psycopg2.connect(self.connection_string)
            else:
                connection = psycopg2.connect(**self.connection_params)
            yield connection
        finally:
            if connection:
                connection.close()
    
    def get_engine(self):
        """
        Obtiene o crea un motor SQLAlchemy para la base de datos.
        
        Returns:
            engine: Motor SQLAlchemy para la base de datos.
        """
        if self.engine is None:
            if hasattr(self, 'connection_string'):
                self.engine = create_engine(self.connection_string)
            else:
                conn_str = f"postgresql://{self.connection_params['user']}:{self.connection_params['password']}@{self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['dbname']}"
                self.engine = create_engine(conn_str)
        return self.engine
    
    def initialize_database(self):
        """
        Inicializa la estructura de la base de datos creando las tablas necesarias.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Crear tablas
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipos (
                    id SERIAL PRIMARY KEY,
                    target VARCHAR(100) UNIQUE NOT NULL,
                    type VARCHAR(100),
                    temperature FLOAT,
                    critical_led VARCHAR(50),
                    major_led VARCHAR(50),
                    over_temp VARCHAR(50),
                    fan_status VARCHAR(50),
                    serial_number VARCHAR(100),
                    estado VARCHAR(50),
                    ciudad VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS servicios (
                    id SERIAL PRIMARY KEY,
                    target VARCHAR(100) REFERENCES equipos(target),
                    service_id INTEGER NOT NULL,
                    type VARCHAR(50),
                    admin_state VARCHAR(20),
                    oper_state VARCHAR(20),
                    customer_id INTEGER,
                    service_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(target, service_id)
                )
                """)
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS puertos (
                    id SERIAL PRIMARY KEY,
                    target VARCHAR(100) REFERENCES equipos(target),
                    port_id VARCHAR(50) NOT NULL,
                    admin_state VARCHAR(20),
                    link VARCHAR(20),
                    port_state VARCHAR(20),
                    cfg_mtu INTEGER,
                    oper_mtu INTEGER,
                    lag VARCHAR(50),
                    port_mode VARCHAR(50),
                    port_encp VARCHAR(50),
                    port_type VARCHAR(50),
                    media_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(target, port_id)
                )
                """)
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS descripciones_puertos (
                    id SERIAL PRIMARY KEY,
                    target VARCHAR(100) REFERENCES equipos(target),
                    port_id VARCHAR(50) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(target, port_id)
                )
                """)
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS versiones (
                    id SERIAL PRIMARY KEY,
                    target VARCHAR(100) REFERENCES equipos(target),
                    timos_version TEXT,
                    main_version VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(target)
                )
                """)
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS mda (
                    id SERIAL PRIMARY KEY,
                    target VARCHAR(100) REFERENCES equipos(target),
                    slot_mda VARCHAR(50) NOT NULL,
                    provisioned_type TEXT,
                    equipped_type TEXT,
                    admin_state VARCHAR(20),
                    oper_state VARCHAR(20),
                    max_ports INTEGER,
                    temperature VARCHAR(20),
                    mda_type VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(target, slot_mda)
                )
                """)
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS servicios_totales (
                    id SERIAL PRIMARY KEY,
                    service_id INTEGER NOT NULL,
                    service_name TEXT,
                    description TEXT,
                    customer_name VARCHAR(100),
                    ci_code VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service_id)
                )
                """)
                
                # Crear índices para mejorar el rendimiento
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipos_target ON equipos(target)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_servicios_target ON servicios(target)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_puertos_target ON puertos(target)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_servicios_totales_service_id ON servicios_totales(service_id)")
                
                conn.commit()
    
    def guardar_dataframe(self, df, tabla):
        """
        Guarda un DataFrame en la tabla especificada.
        
        Args:
            df (DataFrame): DataFrame a guardar.
            tabla (str): Nombre de la tabla.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df is None or df.empty:
            return False
        
        try:
            engine = self.get_engine()
            df.to_sql(tabla, engine, if_exists='append', index=False)
            return True
        except Exception as e:
            print(f"Error al guardar DataFrame en tabla {tabla}: {str(e)}")
            return False
    
    def guardar_equipos(self, df_resumen):
        """
        Guarda la información de equipos en la base de datos.
        
        Args:
            df_resumen (DataFrame): DataFrame con información resumida de equipos.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df_resumen is None or df_resumen.empty:
            return False
        
        # Seleccionar solo las columnas relevantes para la tabla equipos
        columnas = ['target', 'type', 'temperature', 'critical_led', 'major_led', 
                    'over_temp', 'fan_status', 'serial_number', 'estado', 'ciudad']
        
        # Filtrar columnas existentes en el DataFrame
        columnas_existentes = [col for col in columnas if col in df_resumen.columns]
        df_equipos = df_resumen[columnas_existentes].copy()
        
        return self.guardar_dataframe(df_equipos, 'equipos')
    
    def guardar_servicios(self, df_servicios):
        """
        Guarda la información de servicios en la base de datos.
        
        Args:
            df_servicios (DataFrame): DataFrame con información de servicios.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df_servicios is None or df_servicios.empty:
            return False
        
        # Seleccionar solo las columnas relevantes para la tabla servicios
        columnas = ['target', 'service_id', 'type', 'admin_state', 'oper_state', 
                    'customer_id', 'service_name']
        
        # Filtrar columnas existentes en el DataFrame
        columnas_existentes = [col for col in columnas if col in df_servicios.columns]
        df_servicios_filtrado = df_servicios[columnas_existentes].copy()
        
        return self.guardar_dataframe(df_servicios_filtrado, 'servicios')
    
    def guardar_puertos(self, df_puertos):
        """
        Guarda la información de puertos en la base de datos.
        
        Args:
            df_puertos (DataFrame): DataFrame con información de puertos.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df_puertos is None or df_puertos.empty:
            return False
        
        # Seleccionar solo las columnas relevantes para la tabla puertos
        columnas = ['target', 'port_id', 'admin_state', 'link', 'port_state', 
                    'cfg_mtu', 'oper_mtu', 'lag', 'port_mode', 'port_encp', 
                    'port_type', 'media_type']
        
        # Filtrar columnas existentes en el DataFrame
        columnas_existentes = [col for col in columnas if col in df_puertos.columns]
        df_puertos_filtrado = df_puertos[columnas_existentes].copy()
        
        return self.guardar_dataframe(df_puertos_filtrado, 'puertos')
    
    def guardar_descripciones_puertos(self, df_descripciones):
        """
        Guarda la información de descripciones de puertos en la base de datos.
        
        Args:
            df_descripciones (DataFrame): DataFrame con información de descripciones de puertos.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df_descripciones is None or df_descripciones.empty:
            return False
        
        # Seleccionar solo las columnas relevantes para la tabla descripciones_puertos
        columnas = ['target', 'port_id', 'description']
        
        # Filtrar columnas existentes en el DataFrame
        columnas_existentes = [col for col in columnas if col in df_descripciones.columns]
        df_descripciones_filtrado = df_descripciones[columnas_existentes].copy()
        
        return self.guardar_dataframe(df_descripciones_filtrado, 'descripciones_puertos')
    
    def guardar_versiones(self, df_versiones):
        """
        Guarda la información de versiones en la base de datos.
        
        Args:
            df_versiones (DataFrame): DataFrame con información de versiones.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df_versiones is None or df_versiones.empty:
            return False
        
        # Seleccionar solo las columnas relevantes para la tabla versiones
        columnas = ['target', 'timos_version', 'main_version']
        
        # Filtrar columnas existentes en el DataFrame
        columnas_existentes = [col for col in columnas if col in df_versiones.columns]
        df_versiones_filtrado = df_versiones[columnas_existentes].copy()
        
        return self.guardar_dataframe(df_versiones_filtrado, 'versiones')
    
    def guardar_mda(self, df_mda):
        """
        Guarda la información de MDA en la base de datos.
        
        Args:
            df_mda (DataFrame): DataFrame con información de MDA.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df_mda is None or df_mda.empty:
            return False
        
        # Seleccionar solo las columnas relevantes para la tabla mda
        columnas = ['target', 'slot_mda', 'provisioned_type', 'equipped_type', 
                    'admin_state', 'oper_state', 'max_ports', 'temperature', 'mda_type']
        
        # Filtrar columnas existentes en el DataFrame
        columnas_existentes = [col for col in columnas if col in df_mda.columns]
        df_mda_filtrado = df_mda[columnas_existentes].copy()
        
        return self.guardar_dataframe(df_mda_filtrado, 'mda')
    
    def guardar_servicios_totales(self, df_servicios_totales):
        """
        Guarda la información de servicios totales en la base de datos.
        
        Args:
            df_servicios_totales (DataFrame): DataFrame con información de servicios totales.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        if df_servicios_totales is None or df_servicios_totales.empty:
            return False
        
        # Determinar las columnas según el formato del DataFrame
        if 'Service ID' in df_servicios_totales.columns:
            # Formato CSV
            df_servicios_totales = df_servicios_totales.rename(columns={
                'Service ID': 'service_id',
                'Service Name': 'service_name',
                'Description': 'description',
                'Customer': 'customer_name'
            })
        
        # Extraer código CI si existe
        if 'description' in df_servicios_totales.columns:
            df_servicios_totales['ci_code'] = df_servicios_totales['description'].apply(
                lambda x: self._extraer_ci_code(x) if pd.notna(x) else None
            )
        elif 'service_name' in df_servicios_totales.columns:
            df_servicios_totales['ci_code'] = df_servicios_totales['service_name'].apply(
                lambda x: self._extraer_ci_code(x) if pd.notna(x) else None
            )
        
        # Seleccionar solo las columnas relevantes para la tabla servicios_totales
        columnas = ['service_id', 'service_name', 'description', 'customer_name', 'ci_code']
        
        # Filtrar columnas existentes en el DataFrame
        columnas_existentes = [col for col in columnas if col in df_servicios_totales.columns]
        df_filtrado = df_servicios_totales[columnas_existentes].copy()
        
        return self.guardar_dataframe(df_filtrado, 'servicios_totales')
    
    def _extraer_ci_code(self, texto):
        """
        Extrae el código CI de un texto.
        
        Args:
            texto (str): Texto del que extraer el código CI.
            
        Returns:
            str: Código CI extraído o None si no se encuentra.
        """
        if not texto or not isinstance(texto, str):
            return None
        
        # Buscar patrón CI seguido de números
        import re
        ci_match = re.search(r'CI\d+', texto)
        if ci_match:
            return ci_match.group(0)
        
        # Buscar patrón xxx.CO
        co_match = re.search(r'\d+\.CO', texto)
        if co_match:
            return co_match.group(0)
        
        return None
    
    def obtener_equipos(self):
        """
        Obtiene todos los equipos de la base de datos.
        
        Returns:
            DataFrame: DataFrame con la información de equipos.
        """
        with self.get_connection() as conn:
            return pd.read_sql("SELECT * FROM equipos", conn)
    
    def obtener_servicios(self, target=None):
        """
        Obtiene los servicios de la base de datos, opcionalmente filtrados por equipo.
        
        Args:
            target (str, optional): Nombre del equipo para filtrar.
            
        Returns:
            DataFrame: DataFrame con la información de servicios.
        """
        with self.get_connection() as conn:
            if target:
                return pd.read_sql("SELECT * FROM servicios WHERE target = %s", conn, params=(target,))
            else:
                return pd.read_sql("SELECT * FROM servicios", conn)
    
    def obtener_puertos(self, target=None):
        """
        Obtiene los puertos de la base de datos, opcionalmente filtrados por equipo.
        
        Args:
            target (str, optional): Nombre del equipo para filtrar.
            
        Returns:
            DataFrame: DataFrame con la información de puertos.
        """
        with self.get_connection() as conn:
            if target:
                return pd.read_sql("SELECT * FROM puertos WHERE target = %s", conn, params=(target,))
            else:
                return pd.read_sql("SELECT * FROM puertos", conn)
    
    def obtener_descripciones_puertos(self, target=None):
        """
        Obtiene las descripciones de puertos de la base de datos, opcionalmente filtradas por equipo.
        
        Args:
            target (str, optional): Nombre del equipo para filtrar.
            
        Returns:
            DataFrame: DataFrame con la información de descripciones de puertos.
        """
        with self.get_connection() as conn:
            if target:
                return pd.read_sql("SELECT * FROM descripciones_puertos WHERE target = %s", conn, params=(target,))
            else:
                return pd.read_sql("SELECT * FROM descripciones_puertos", conn)
    
    def obtener_versiones(self, target=None):
        """
        Obtiene las versiones de la base de datos, opcionalmente filtradas por equipo.
        
        Args:
            target (str, optional): Nombre del equipo para filtrar.
            
        Returns:
            DataFrame: DataFrame con la información de versiones.
        """
        with self.get_connection() as conn:
            if target:
                return pd.read_sql("SELECT * FROM versiones WHERE target = %s", conn, params=(target,))
            else:
                return pd.read_sql("SELECT * FROM versiones", conn)
    
    def obtener_mda(self, target=None):
        """
        Obtiene la información de MDA de la base de datos, opcionalmente filtrada por equipo.
        
        Args:
            target (str, optional): Nombre del equipo para filtrar.
            
        Returns:
            DataFrame: DataFrame con la información de MDA.
        """
        with self.get_connection() as conn:
            if target:
                return pd.read_sql("SELECT * FROM mda WHERE target = %s", conn, params=(target,))
            else:
                return pd.read_sql("SELECT * FROM mda", conn)
    
    def obtener_servicios_totales(self, service_id=None):
        """
        Obtiene la información de servicios totales de la base de datos, opcionalmente filtrada por ID de servicio.
        
        Args:
            service_id (int, optional): ID del servicio para filtrar.
            
        Returns:
            DataFrame: DataFrame con la información de servicios totales.
        """
        with self.get_connection() as conn:
            if service_id:
                return pd.read_sql("SELECT * FROM servicios_totales WHERE service_id = %s", conn, params=(service_id,))
            else:
                return pd.read_sql("SELECT * FROM servicios_totales", conn)
    
    def generar_resumen(self):
        """
        Genera un DataFrame de resumen con información consolidada desde la base de datos.
        
        Returns:
            DataFrame: DataFrame de resumen.
        """
        with self.get_connection() as conn:
            # Consulta SQL para generar el resumen
            query = """
            SELECT 
                e.target,
                e.type,
                e.temperature,
                e.critical_led,
                e.major_led,
                e.over_temp,
                e.fan_status,
                e.serial_number,
                e.estado,
                e.ciudad,
                v.timos_version,
                v.main_version,
                COUNT(DISTINCT s.service_id) AS total_servicios,
                SUM(CASE WHEN s.admin_state = 'Up' AND s.oper_state = 'Up' THEN 1 ELSE 0 END) AS servicios_up,
                SUM(CASE WHEN s.admin_state = 'Up' AND s.oper_state = 'Down' THEN 1 ELSE 0 END) AS servicios_down,
                COUNT(DISTINCT p.port_id) AS total_puertos,
                SUM(CASE WHEN p.admin_state = 'Up' AND p.port_state = 'Up' THEN 1 ELSE 0 END) AS puertos_up,
                SUM(CASE WHEN p.admin_state = 'Up' AND p.port_state = 'Down' THEN 1 ELSE 0 END) AS puertos_down
            FROM 
                equipos e
            LEFT JOIN 
                versiones v ON e.target = v.target
            LEFT JOIN 
                servicios s ON e.target = s.target
            LEFT JOIN 
                puertos p ON e.target = p.target
            GROUP BY 
                e.target, e.type, e.temperature, e.critical_led, e.major_led, 
                e.over_temp, e.fan_status, e.serial_number, e.estado, e.ciudad,
                v.timos_version, v.main_version
            """
            
            return pd.read_sql(query, conn)
    
    def limpiar_datos(self):
        """
        Limpia todos los datos de la base de datos.
        
        Returns:
            bool: True si se limpió correctamente, False en caso contrario.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Desactivar restricciones de clave foránea temporalmente
                    cursor.execute("SET CONSTRAINTS ALL DEFERRED")
                    
                    # Limpiar todas las tablas
                    cursor.execute("TRUNCATE TABLE servicios, puertos, descripciones_puertos, versiones, mda, equipos, servicios_totales RESTART IDENTITY CASCADE")
                    
                    # Reactivar restricciones de clave foránea
                    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                    
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error al limpiar datos: {str(e)}")
            return False
