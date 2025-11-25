# Mock Server - Configuración de ejemplo
# Este archivo muestra todas las opciones de configuración disponibles con sus valores por defecto

CONFIG = {
    # Configuración del servidor HTTP
    "server": {
        "port": 9090,                    # Puerto donde escuchará el servidor
        "host": "0.0.0.0",               # IP del servidor (0.0.0.0 = todas las interfaces)
        "cors_enabled": True,            # Habilitar CORS
        "cors_origins": "*",             # Orígenes permitidos para CORS (* = todos)
        "reload": True                   # Auto-reload cuando cambian los archivos
    },

    # Configuración de logging
    "logging": {
        "level": "INFO",                                           # Nivel de log: DEBUG, INFO, WARNING, ERROR, CRITICAL
        "format": "%(asctime)s [%(levelname)s] %(message)s",     # Formato de los logs
        "date_format": "%Y-%m-%d %H:%M:%S"                       # Formato de fecha en logs
    },

    # Rutas de directorios (None = usar defaults)
    "paths": {
        "requests_dir": None,     # None = usa {config_dir}/requests
        "responses_dir": None     # None = usa {config_dir}/responses
    },

    # Configuración personalizada (puedes agregar tus propias opciones aquí)
    "custom": {
        # Ejemplo: "api_key": "tu-api-key",
        # Ejemplo: "timeout": 30
    }
}
