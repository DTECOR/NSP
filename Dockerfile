FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements_enterprise.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements_enterprise.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto para Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app_enterprise.py", "--server.port=8501", "--server.address=0.0.0.0"]
