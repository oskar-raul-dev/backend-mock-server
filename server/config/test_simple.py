# Simple test to debug semantic matching

definitions = [
    {
        "request": {
            "url": r"^/test/json$",
            "methods": ["POST"],
            "body": {
                "value": '{"name": "Test", "age": 30}',
                "format": "json",
                "matching_mode": "semantic"
            }
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"success": true}'
        }
    }
]
