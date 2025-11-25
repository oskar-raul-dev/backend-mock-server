# Mock Server - Definiciones de endpoints de ejemplo

definitions = [
    # ========================================================================
    # Ejemplo 1: GET /hello con query parameter
    # ========================================================================
    # URL: http://localhost:9090/hello?name=Juan
    # Responde con: {"message": "hello world Juan"}
    {
        "request": {
            "url": r"^/hello$",
            "methods": ["GET"],
            "queryparams": [
                {"name": "name"}  # Requiere el parámetro 'name'
            ]
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"message": "hello world {{ QUERY_PARAMS.name }}"}'
        }
    },

    # ========================================================================
    # Ejemplo 2: POST /hello con body JSON
    # ========================================================================
    # URL: http://localhost:9090/hello
    # Body: {"name": "Juan", "lastname": "Pérez"}
    # Responde con: {"body": {"name": "Juan", "lastname": "Pérez"}}
    {
        "request": {
            "url": r"^/hello$",
            "methods": ["POST"],
            "headers": [
                {"name": "Content-Type", "value": "application/json"}
            ]
            # NOTA: Para validación semántica de JSON (nuevo sistema en Fase 1-2),
            # descomenta el bloque siguiente:
            # "body": {
            #     "type": "json",
            #     "match_strategy": "semantic",  # semantic, exact, regex
            #     "expected": {
            #         "name": ".*",  # Regex: cualquier nombre
            #         "lastname": ".*"  # Regex: cualquier apellido
            #     }
            # }
            # Y cambia {{ BODY }} por {{ BODY_PROCESSED }} en la respuesta
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"received_body": {{ BODY }} }'
        }
    },

    # ========================================================================
    # Ejemplo 3: GET /hello/{name}/{lastname} - Path parameters
    # ========================================================================
    # URL: http://localhost:9090/hello/pedro/perez
    # Responde con: {"msg": "Hola pedro perez"}
    {
        "request": {
            "url": r"^/hello/([^/]+)/([^/]+)$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"msg": "Hola {{ PATH_PARAMS[0] }} {{ PATH_PARAMS[1] }}"}'
        }
    },

    # ========================================================================
    # Ejemplo 4: GET /lorem - Response desde archivo
    # ========================================================================
    # URL: http://localhost:9090/lorem
    # Responde con contenido del archivo lorem_ipsum.txt
    {
        "request": {
            "url": r"^/lorem$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "text/plain"
            },
            "body_file": "lorem_ipsum.txt"
        }
    },

    # ========================================================================
    # Ejemplo 5: Endpoint con múltiples respuestas (cycling)
    # ========================================================================
    # URL: http://localhost:9090/counter
    # Primera llamada: {"count": 1}
    # Segunda llamada: {"count": 2}
    # Tercera llamada: {"count": 3}
    # Cuarta llamada: vuelve a {"count": 1}
    {
        "request": {
            "url": r"^/counter$",
            "methods": ["GET"]
        },
        "response": [
            {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": '{"count": 1}'
            },
            {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": '{"count": 2}'
            },
            {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": '{"count": 3}'
            }
        ]
    },

    # ========================================================================
    # Ejemplo 6: Endpoint con validación de headers
    # ========================================================================
    # URL: http://localhost:9090/api/protected
    # Requiere header: Authorization: Bearer <token>
    {
        "request": {
            "url": r"^/api/protected$",
            "methods": ["GET"],
            "headers": [
                {"name": "Authorization", "value": r"Bearer .+"}
            ]
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"message": "Access granted", "auth": "{{ HEADERS.authorization }}"}'
        }
    },

    # ========================================================================
    # Ejemplo 7: Simulación de error 404
    # ========================================================================
    # URL: http://localhost:9090/not-found
    {
        "request": {
            "url": r"^/not-found$",
            "methods": ["GET"]
        },
        "response": {
            "status": 404,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"error": "Resource not found"}'
        }
    },

    # ========================================================================
    # Ejemplo 8: Simulación de error 500
    # ========================================================================
    # URL: http://localhost:9090/error
    {
        "request": {
            "url": r"^/error$",
            "methods": ["GET"]
        },
        "response": {
            "status": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"error": "Internal server error", "message": "Something went wrong"}'
        }
    }
]
