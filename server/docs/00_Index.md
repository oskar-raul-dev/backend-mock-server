# MockServer Documentation

Welcome to the MockServer documentation! This flexible HTTP mock server provides semantic body matching, custom validators, and dynamic response generation for API development and testing.

---

## 📚 Table of Contents

### Getting Started

1. **[Quickstart Guide](01_Quickstart_Guide.md)**
   - Installation and setup
   - Your first "Hello World" mock
   - Complete example with validator and processor
   - Testing with curl

### Configuration & Setup

2. **[Server Startup Options](02_Server_Startup_Options.md)**
   - Command-line interface (CLI) options
   - Configuration file (`config.py`)
   - Environment-specific configurations
   - Auto-reload configuration
   - Logging setup

### Core Concepts

3. **[Request Configuration](03_Request_Configuration.md)**
   - URL matching (exact and regex)
   - HTTP methods
   - Query parameters
   - Headers
   - Body matching (JSON, XML, plain text)
   - Custom validators (in-depth)
   - Custom processors (in-depth)
   - Multiple responses (round-robin)

4. **[Response Templates](04_Response_Templates.md)**
   - Response structure
   - Status codes and headers
   - Body formats (JSON, XML, HTML, text, binary)
   - Template variables
   - Jinja2 templating
   - Dynamic responses
   - Response from file

5. **[Body Matching](05_Body_Matching.md)**
   - What is semantic matching?
   - XML semantic matching
   - JSON semantic matching
   - Matching modes (semantic, partial, strict)
   - Format detection
   - Troubleshooting matching issues

6. **[Validators and Processors](06_Validators_And_Processors.md)**
   - Validators: business rule validation
   - Processors: data extraction and transformation
   - XML validation and processing
   - JSON validation and processing
   - Plain text and binary handling
   - Best practices
   - Complete examples

### Examples & Reference

7. **[Advanced Examples](07_Advanced_Examples.md)**
   - XML examples with validators/processors
   - JSON examples with partial matching
   - Real-world use cases
   - User creation, orders, payments
   - Product management, search, checkout

### Internals & Troubleshooting

8. **[Internals & Architecture](08_Internals_Architecture.md)**
   - System architecture
   - Component overview
   - Request flow
   - Matching algorithm
   - Response generation
   - Design patterns
   - Extensibility points

9. **[Troubleshooting](09_Troubleshooting.md)**
   - Common issues and solutions
   - Debugging techniques
   - Error messages explained
   - Performance tips
   - FAQ

---

## 🚀 Quick Links

### Testing Tools

- **[cURL Examples](sample_curls/)**
  - [Basic Examples](sample_curls/endpoints.curl.txt)
  - [Advanced Examples](sample_curls/endpoints_advanced_examples.curl.txt)

- **[Postman Collections](sample_postman/)**
  - [Basic Collection](sample_postman/endpoints.postman.collection.json)
  - [Advanced Collection](sample_postman/endpoints_advanced_examples.postman.collection.json)

### Configuration

- **[Configuration Reference](../config/README.md)** - Config directory documentation
- **[Main README](../README.md)** - Project overview and quick setup

---

## 🎯 Quick Start

If you're new to MockServer, start here:

1. **[Quickstart Guide](01_Quickstart_Guide.md)** - Get up and running in 5 minutes
2. **[Request Configuration](03_Request_Configuration.md)** - Learn how to define mocks
3. **[Response Templates](04_Response_Templates.md)** - Create dynamic responses
4. **[Advanced Examples](07_Advanced_Examples.md)** - See real-world examples

---

## 📖 Learning Paths

### For API Developers

1. Start with [Quickstart Guide](01_Quickstart_Guide.md)
2. Learn [Request Configuration](03_Request_Configuration.md)
3. Master [Response Templates](04_Response_Templates.md)
4. Explore [Advanced Examples](07_Advanced_Examples.md)

### For QA/Test Engineers

1. Read [Quickstart Guide](01_Quickstart_Guide.md)
2. Understand [Body Matching](05_Body_Matching.md)
3. Learn [Validators and Processors](06_Validators_And_Processors.md)
4. Practice with [Advanced Examples](07_Advanced_Examples.md)

### For DevOps/Infrastructure

1. Review [Server Startup Options](02_Server_Startup_Options.md)
2. Understand [Internals & Architecture](08_Internals_Architecture.md)
3. Check [Troubleshooting](09_Troubleshooting.md)

---

## 🔍 Find What You Need

### By Feature

- **Query Parameters**: [Request Configuration](03_Request_Configuration.md#query-parameters)
- **Path Parameters**: [Request Configuration](03_Request_Configuration.md#url-matching)
- **Header Validation**: [Request Configuration](03_Request_Configuration.md#headers)
- **JSON Matching**: [Body Matching](05_Body_Matching.md#json-semantic-matching)
- **XML Matching**: [Body Matching](05_Body_Matching.md#xml-semantic-matching)
- **Custom Validation**: [Validators and Processors](06_Validators_And_Processors.md#validators)
- **Data Processing**: [Validators and Processors](06_Validators_And_Processors.md#processors)
- **Template Variables**: [Response Templates](04_Response_Templates.md#template-variables)
- **Round-Robin**: [Request Configuration](03_Request_Configuration.md#multiple-responses)
- **CORS**: [Server Startup Options](02_Server_Startup_Options.md#cors-configuration)
- **Auto-Reload**: [Server Startup Options](02_Server_Startup_Options.md#auto-reload)

### By Use Case

- **Mocking REST APIs**: [Advanced Examples](07_Advanced_Examples.md)
- **Simulating Errors**: [Request Configuration](03_Request_Configuration.md#error-responses)
- **Testing Edge Cases**: [Validators and Processors](06_Validators_And_Processors.md)
- **Frontend Development**: [Response Templates](04_Response_Templates.md)
- **Integration Testing**: [Body Matching](05_Body_Matching.md)

---

## 💡 Key Concepts

### Semantic Matching

Unlike simple string matching, MockServer understands the structure of XML and JSON:

```xml
<!-- These are semantically equivalent: -->
<user><name>John</name><age>30</age></user>
<user><age>30</age><name>John</name></user>
```

Learn more: [Body Matching](05_Body_Matching.md)

### Validators

Custom functions that validate request data and enforce business rules:

```python
def validate_email(body):
    data = json.loads(body)
    if "@" not in data.get("email", ""):
        raise ValueError("Invalid email format")
```

Learn more: [Validators and Processors](06_Validators_And_Processors.md#validators)

### Processors

Functions that extract and transform data from requests for use in responses:

```python
def process_user(body):
    data = json.loads(body)
    return {
        "user_id": generate_id(),
        "full_name": f"{data['first_name']} {data['last_name']}"
    }
```

Learn more: [Validators and Processors](06_Validators_And_Processors.md#processors)

### Template Variables

Dynamic response generation using data from requests:

```python
"body": '{"greeting": "Hello {{ QUERY_PARAMS.name }}!"}'
"body": '{"user_id": "{{ BODY_PROCESSED.user_id }}"}'
```

Learn more: [Response Templates](04_Response_Templates.md#template-variables)

---

## 🛠️ Example Configurations

The `config/` directory contains two sets of examples:

### Basic Examples (`endpoints.py`)

- Simple query parameters
- Path parameter extraction
- Header validation
- JSON body handling
- File-based responses
- Round-robin responses
- Error simulation (404, 500)

**8 endpoints** demonstrating core features.

### Advanced Examples (`endpoints_advanced_examples.py`)

- **XML Examples**: User creation, order updates, payment processing
- **JSON Examples**: Product creation, search, checkout

**6 endpoints** with validators, processors, and semantic matching.

See: [Advanced Examples](07_Advanced_Examples.md)

---

## 📦 What's Included

```
mockserver/
├── README.md                    # Project overview
├── main.py                      # Server entry point
├── config/                      # Example configurations
│   ├── README.md
│   ├── config.py
│   ├── endpoints.py
│   ├── endpoints_advanced_examples.py
│   ├── requests/
│   └── responses/
├── docs/                        # Documentation (you are here)
│   ├── 00_Index.md              # This file
│   ├── 01_Quickstart_Guide.md
│   ├── 02_Server_Startup_Options.md
│   ├── 03_Request_Configuration.md
│   ├── 04_Response_Templates.md
│   ├── 05_Body_Matching.md
│   ├── 06_Validators_And_Processors.md
│   ├── 07_Advanced_Examples.md
│   ├── 08_Internals_Architecture.md
│   ├── 09_Troubleshooting.md
│   ├── sample_curls/
│   └── sample_postman/
└── mockserver/                  # Source code
    ├── core/
    ├── server/
    ├── config/
    ├── body_matching/
    ├── cli/
    └── log_setup/
```

---

## 🤝 Getting Help

- **Documentation**: You're reading it! Check the table of contents above
- **Examples**: See `config/` directory for working examples
- **Issues**: Report bugs or request features
- **Troubleshooting**: [Common Issues](09_Troubleshooting.md)

---

## 📝 Contributing

Contributions are welcome! See:

- [Internals & Architecture](08_Internals_Architecture.md) - Understand the codebase
- Code is documented with comprehensive docstrings
- All modules follow consistent patterns

---

## 🔖 Document Conventions

Throughout this documentation:

- **Code blocks**: Include syntax highlighting and line numbers when helpful
- **Examples**: Show both the configuration and the curl command to test it
- **Cross-references**: Links to related sections for deeper understanding
- **Platform-specific**: Commands for both Linux/macOS and Windows where applicable

---

**Ready to get started?** Begin with the [Quickstart Guide](01_Quickstart_Guide.md)!
