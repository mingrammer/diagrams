# Project: Diagrams MCP Server

## Overview
This project aims to implement a Model Context Protocol (MCP) server that exposes the capabilities of the [diagrams](https://diagrams.mingrammer.com/) Python library. The server will allow AI agents to dynamically discover available diagram nodes (AWS, Azure, Kubernetes, etc.) and generate architectural diagrams from Python code.

## Architecture
The solution will be containerized to ensure isolation and consistent dependencies (specifically Graphviz).

-   **Runtime**: Python 3.9+
-   **Container**: Docker (Debian-based to support Graphviz)
-   **Communication**: Standard Input/Output (stdio) via the MCP protocol.
-   **Libraries**:
    -   `diagrams`: For generating diagrams.
    -   `mcp`: Official Python SDK for the Model Context Protocol.
    -   `graphviz`: System dependency required by the `diagrams` library.

## File Structure
```text
.
├── Dockerfile
├── requirements.txt
├── server.py
└── src/
    └── inspection.py  # Helper for dynamic node discovery
```

## Implementation Details

### 1. Docker Environment (`Dockerfile`)
The environment must include Graphviz, which is a system-level dependency required for rendering.

*   **Base Image**: `python:3.11-slim`
*   **System Dependencies**: `graphviz` (via `apt-get install -y graphviz`)
*   **Python Dependencies**: `diagrams`, `mcp`

### 2. MCP Server (`server.py`)
The server will define three main tools. It should use the `mcp.server.fastmcp` or `mcp.server` standard library to define the server.

#### Tool 1: `list_icons`
**Purpose**: Dynamically discovers all available diagram nodes across all providers (AWS, Azure, GCP, SaaS, etc.) so the AI knows what classes are available to import.

*   **Logic**:
    1.  Recursively walk the `diagrams` package directory.
    2.  Import modules dynamically.
    3.  Inspect classes in each module.
    4.  Filter classes that inherit from `diagrams.Node` but are not the base `Node` class itself.
    5.  Organize into a hierarchy: `Provider -> Service -> Node`.
    6.  **Optimization**: Cache this result at startup as it won't change.

*   **Parameters**:
    -   `provider_filter` (string, optional): If provided (e.g., "aws"), only return nodes for that provider.

*   **Returns**: JSON structure:
    ```json
    {
      "aws": {
        "compute": ["EC2", "Lambda", ...],
        "database": ["RDS", "DynamoDB", ...]
      },
      "k8s": { ... }
    }
    ```

#### Tool 2: `generate_diagram`
**Purpose**: Executes Python code to generate a diagram image.

*   **Logic**:
    1.  Accepts a string of Python code (DSL).
    2.  **Security**: The code is executed via `exec()`. Since this runs inside a Docker container, it provides a layer of isolation.
    3.  **Execution**:
        -   Set up a temporary directory.
        -   Change the working directory to this temp location.
        -   Execute the code.
        -   Find the generated output file (usually `.png`).
    4.  **Result**: Return the path to the generated image or the base64 encoded content (depending on client capability, but path is preferred if sharing volume). *For this implementation, return the path inside the container and ensure the container mounts a shared volume if persistence is needed.*

*   **Parameters**:
    -   `code` (string, required): The Python code using `diagrams` DSL.
    -   `filename` (string, optional): Desired output filename.

*   **Returns**:
    -   `status`: "success" or "error"
    -   `message`: Path to file or error message.

#### Tool 3: `get_diagram_examples`
**Purpose**: Provides example code snippets to help the AI understand the syntax.

*   **Logic**: Return a dictionary of static examples for common patterns (Basic, Clustered, Cloud-specific).

*   **Parameters**:
    -   `provider` (string, optional): specific provider example (e.g., "aws").

### 3. Dynamic Inspection Helper (`src/inspection.py`)
This module is crucial for `list_icons`. It must robustly handle imports without crashing the server if a specific provider has missing optional dependencies.

*   Use `pkgutil.walk_packages` to iterate over `diagrams`.
*   Use `importlib.import_module` to load found modules.
*   Use `inspect.getmembers` to find classes.
*   Check `issubclass(obj, diagrams.Node)`.

## Execution & Testing
To run the server:
```bash
# Build
docker build -t diagrams-mcp .

# Run (connected to stdin/stdout for MCP)
docker run -i --rm -v $(pwd)/output:/app/output diagrams-mcp
```

## Security Considerations
*   **Arbitrary Code Execution**: The `generate_diagram` tool executes arbitrary Python code. This is by design but dangerous. The Docker container MUST be treated as untrusted and ephemeral. Do not mount sensitive host directories into the container.
