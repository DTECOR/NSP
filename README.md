# NSP Visualizer - Manual de Instalación y Uso

## Introducción

NSP Visualizer es una herramienta avanzada para visualizar, analizar e interpretar datos operativos de equipos de red Nokia. Esta aplicación permite cargar archivos de comandos NSP, procesarlos y presentar visualizaciones interactivas que facilitan el análisis y la toma de decisiones.

Este documento proporciona instrucciones detalladas para instalar y utilizar tanto la versión Estándar como la versión Enterprise de NSP Visualizer.

## Versiones Disponibles

### Versión Estándar
- Almacenamiento basado en archivos
- Instalación local simple
- Todas las funcionalidades básicas y avanzadas de visualización

### Versión Enterprise
- Almacenamiento en base de datos PostgreSQL
- Despliegue en contenedores Docker
- Persistencia de datos mejorada
- Escalabilidad para grandes volúmenes de datos

## Requisitos del Sistema

### Versión Estándar
- Python 3.8 o superior
- Pip (gestor de paquetes de Python)
- 4GB de RAM mínimo (8GB recomendado)
- 1GB de espacio en disco

### Versión Enterprise
- Docker y Docker Compose
- 8GB de RAM mínimo (16GB recomendado)
- 2GB de espacio en disco

## Instalación

### Versión Estándar

1. Descomprima el archivo `NSP_Visualizer_Standard.zip` en la ubicación deseada.

2. Abra una terminal o línea de comandos y navegue hasta el directorio donde descomprimió los archivos:
   ```
   cd ruta/a/NSP_Visualizer_Clean
   ```

3. Instale las dependencias requeridas:
   ```
   pip install -r requirements.txt
   ```

4. Ejecute la aplicación:
   ```
   streamlit run app_standard.py
   ```

5. La aplicación se abrirá automáticamente en su navegador web predeterminado. Si no es así, abra manualmente http://localhost:8501 en su navegador.

### Versión Enterprise

1. Descomprima el archivo `NSP_Visualizer_Enterprise.zip` en la ubicación deseada.

2. Abra una terminal o línea de comandos y navegue hasta el directorio donde descomprimió los archivos:
   ```
   cd ruta/a/NSP_Visualizer_Clean
   ```

3. Inicie los contenedores Docker:
   ```
   docker-compose up -d
   ```

4. La aplicación estará disponible en http://localhost:8501 en su navegador.

## Uso de la Aplicación

### Carga de Datos

1. **Carga Automática**: Coloque sus archivos de comandos NSP en la carpeta `InformeNokia` y seleccione la opción "Automática" en la interfaz.

2. **Carga Manual**: Seleccione la opción "Manual" y arrastre o seleccione los archivos .txt que desea procesar.

3. **Carga de Servicios Totales**: Cargue un archivo Excel o CSV con la información completa de servicios para habilitar la funcionalidad de exportación NOC.

### Navegación por Pestañas

La aplicación está organizada en pestañas para facilitar la navegación:

1. **Dashboard**: Vista general con estadísticas y gráficos principales.
2. **Mapa Geográfico**: Visualización de equipos en un mapa interactivo de Colombia.
3. **Por Ciudad**: Análisis detallado por ciudad.
4. **Servicios**: Información de servicios por equipo.
5. **Exportación NOC**: Generación de reportes para el NOC.
6. **Asistente IA**: Consultas en lenguaje natural sobre los datos.
7. **Filtros Avanzados**: Búsqueda y filtrado detallado de equipos.
8. **Base de Datos** (solo versión Enterprise): Gestión de la base de datos PostgreSQL.

### Funcionalidades Principales

#### Modo Oscuro
Active o desactive el modo oscuro desde la barra lateral para reducir la fatiga visual en entornos con poca luz.

#### Mapa Geográfico Interactivo
Visualice la ubicación de los equipos en un mapa de Colombia con códigos de color según su estado. Haga clic en los marcadores para ver detalles.

#### Filtros Avanzados
Utilice múltiples criterios para filtrar equipos por ciudad, tipo, temperatura, servicios, puertos y más.

#### Exportación NOC
Genere reportes estandarizados para el NOC con información detallada de servicios, incluyendo códigos CI.

#### Asistente IA
Realice consultas en lenguaje natural como "¿Cuáles son los puertos libres en el equipo X?" o "¿Qué equipos tienen temperatura crítica?".

## Solución de Problemas

### Versión Estándar

1. **Error al cargar archivos**: Verifique que los archivos estén en formato .txt y contengan comandos NSP válidos.

2. **Error en el Asistente IA**: Si el chat no funciona correctamente, asegúrese de estar en la pestaña "Asistente IA" al escribir su consulta.

3. **Problemas de rendimiento**: Para grandes volúmenes de datos, considere actualizar a la versión Enterprise con PostgreSQL.

### Versión Enterprise

1. **Error de conexión a la base de datos**: Verifique que los contenedores Docker estén en ejecución con `docker-compose ps`.

2. **Reiniciar la aplicación**: Si encuentra problemas, reinicie los contenedores con:
   ```
   docker-compose down
   docker-compose up -d
   ```

3. **Acceder a los logs**: Para ver los logs de la aplicación:
   ```
   docker-compose logs -f app
   ```

## Contacto y Soporte

Para obtener ayuda adicional o reportar problemas, contacte al equipo de soporte técnico.

---

© 2025 NSP Visualizer - Todos los derechos reservados
