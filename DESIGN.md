# Compiler Explorer LLM Bridge - System Design Document

## 1. Overview

The Compiler Explorer LLM Bridge (CE-LLM) is a server application that connects the Compiler Explorer API with Large Language Models using the Model Context Protocol. This bridge enables LLMs to compile, execute, and analyze code through Compiler Explorer while maintaining a standardized communication protocol.

## 2. System Architecture

### 2.1 High-Level Components

```
┌──────────────────┐     ┌─────────────────┐     ┌────────────────┐
│   LLM Clients    │────▶│  CE-LLM Bridge  │────▶│    Compiler    │
│ (MCP Compatible) │◀────│     Server      │◀────│    Explorer    │
└──────────────────┘     └─────────────────┘     └────────────────┘
```

### 2.2 Core Components

1. **MCP Protocol Handler**
   - Implements Model Context Protocol specifications
   - Handles tool registration and invocation
   - Manages context and state for LLM interactions

2. **Compiler Explorer Client**
   - Manages API communication with compiler-explorer.com
   - Handles compilation requests and responses
   - Supports multiple languages and compilers

3. **Bridge Server**
   - FastAPI-based HTTP server
   - WebSocket support for real-time compilation
   - Request/Response validation and error handling

4. **Tool Registry**
   - Dynamic tool registration system
   - Compiler-specific tool implementations
   - Extensible tool interface

## 3. Technical Specifications

### 3.1 Technology Stack

- **Language:** Python 3.12+
- **Package Management:** uv
- **Web Framework:** FastAPI
- **API Client:** httpx
- **WebSocket:** websockets
- **Schema Validation:** Pydantic v2

### 3.2 Core Dependencies

```toml
[project]
name = "compiler-explorer-mcp"
version = "0.1.0"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
    "httpx>=0.27.0",
    "websockets>=12.0",
    "pydantic>=2.6.0",
    "python-dotenv>=1.0.0"
]
```

## 4. API Design

### 4.1 MCP Tool Definitions

```python
COMPILER_TOOLS = {
    "list_languages": {
        "description": "Get a list of supported programming languages",
        "parameters": {}
    },
    "list_compilers": {
        "description": "Get available compilers for a language",
        "parameters": {
            "language": "string?"
        }
    },
    "list_libraries": {
        "description": "Get available libraries for a language",
        "parameters": {
            "language": "string"
        }
    },
    "compile_code": {
        "description": "Compile source code using specified compiler and options",
        "parameters": {
            "source": "string",
            "language": "string",
            "compiler": "string",
            "options": "string?",
            "filters": {
                "type": "object",
                "properties": {
                    "binary": "boolean?",
                    "binaryObject": "boolean?",
                    "commentOnly": "boolean?",
                    "demangle": "boolean?",
                    "directives": "boolean?",
                    "execute": "boolean?",
                    "intel": "boolean?",
                    "labels": "boolean?",
                    "libraryCode": "boolean?",
                    "trim": "boolean?"
                }
            },
            "libraries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": "string",
                        "version": "string"
                    }
                }
            }
        }
    },
    "execute_code": {
        "description": "Compile and execute code with optional input",
        "parameters": {
            "source": "string",
            "language": "string",
            "compiler": "string",
            "input": "string?",
            "options": "string?",
            "args": {
                "type": "array",
                "items": "string"
            },
            "env": {
                "type": "object",
                "additionalProperties": "string"
            }
        }
    },
    "format_code": {
        "description": "Format source code using available formatters",
        "parameters": {
            "source": "string",
            "language": "string",
            "style": "string?",
            "useSpaces": "boolean?",
            "tabWidth": "integer?"
        }
    },
    "get_asm_docs": {
        "description": "Get documentation for an assembly opcode",
        "parameters": {
            "opcode": "string",
            "instructionSet": "string"
        }
    },
    "create_shortlink": {
        "description": "Create a permanent shortlink for code and compiler configuration",
        "parameters": {
            "source": "string",
            "language": "string",
            "compiler": "string",
            "options": "string?"
        }
    }
}
```

### 4.2 Endpoints

1. **MCP Protocol Endpoints**
   - `POST /v1/tools/register` - Register available tools
   - `POST /v1/tools/invoke` - Invoke a specific tool
   - `GET /v1/tools/list` - List available tools

2. **Core API Endpoints**
   - `GET /api/languages` - List supported languages
   - `GET /api/compilers` - List available compilers
   - `GET /api/libraries/{language}` - List libraries for language
   - `POST /api/compiler/{compiler}/compile` - Compile code
   - `POST /api/compiler/{compiler}/format` - Format code
   - `GET /api/asm/{opcode}` - Get assembly documentation
   - `POST /api/shortener` - Create short links
   - `GET /api/health` - Service health check

3. **WebSocket Endpoints**
   - `WS /v1/ws/compile` - Real-time compilation updates
   - `WS /v1/ws/execute` - Real-time execution updates
   - `WS /v1/ws/format` - Real-time code formatting updates

4. **Administrative Endpoints**
   - `GET /metrics` - Prometheus metrics
   - `GET /healthcheck` - Detailed service health status

## 5. Data Flow

1. **Compilation Flow**
```
LLM Client → MCP Request → Tool Registry → CE Client → 
Compiler Explorer API → CE Client → Response Transform → LLM Client
```

2. **Tool Registration Flow**
```
Server Start → Load Tool Definitions → Register with MCP → 
Validate Tools → Ready for Invocation
```

## 6. Security Considerations

1. **Input Validation**
   - Strict validation of all code inputs
   - Size limits on source code
   - Compiler option whitelisting

2. **Rate Limiting**
   - Per-client request limits
   - Compiler Explorer API quota management
   - Concurrent compilation limits

3. **Error Handling**
   - Graceful failure modes
   - Detailed error reporting
   - Timeout management

## 7. Implementation Plan

### Phase 1: Core Infrastructure
1. Set up FastAPI server structure
2. Implement MCP protocol handlers
3. Create Compiler Explorer API client

### Phase 2: Tool Implementation
1. Implement basic compilation tools
2. Add compiler listing functionality
3. Develop execution capabilities

### Phase 3: WebSocket Support
1. Add real-time compilation updates
2. Implement execution streaming
3. Add connection management

### Phase 4: Testing & Documentation
1. Unit test coverage
2. Integration tests
3. API documentation
4. Usage examples

## 8. Directory Structure

```
compiler-explorer-mcp/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   └── websockets/
│   ├── core/
│   │   ├── compiler.py
│   │   ├── mcp.py
│   │   └── tools.py
│   ├── models/
│   └── services/
├── tests/
├── docs/
├── main.py
└── pyproject.toml
```

## 9. Monitoring and Logging

1. **Metrics**
   - Compilation times
   - Error rates
   - Tool usage statistics
   - API latency

2. **Logging**
   - Structured JSON logging
   - Request/Response tracking
   - Error tracing
   - Performance monitoring

## 10. Future Enhancements

1. **Caching Layer**
   - Compilation result caching
   - Compiler information caching
   - Response optimization

2. **Advanced Features**
   - AST analysis tools
   - Code optimization suggestions
   - Multi-file project support
   - Custom compiler configurations 