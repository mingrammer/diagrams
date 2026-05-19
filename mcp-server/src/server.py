import base64
import contextlib
import os
import sys
import tempfile
from pathlib import Path

# Import our helper
from inspection import get_all_nodes
from mcp.server.fastmcp import FastMCP

from diagrams import Cluster, Diagram, Edge, Node

# Initialize FastMCP
mcp = FastMCP("diagrams-mcp")

# Pre-load nodes for quick access and for the execution context
print("Loading diagram nodes...", file=sys.stderr)
ALL_ICONS, NODE_REGISTRY = get_all_nodes()
print(f"Loaded {len(NODE_REGISTRY)} nodes.", file=sys.stderr)


@mcp.tool()
def list_icons(provider_filter: str = None, service_filter: str = None):
    """
    List available icons from the diagrams package, with optional filtering.

    Args:
        provider_filter: Filter icons by provider name (e.g., "aws", "gcp", "k8s")
        service_filter: Filter icons by service name (e.g., "compute", "database")
    """
    if not provider_filter:
        # Return list of providers
        return {"providers": list(ALL_ICONS.keys())}

    if provider_filter not in ALL_ICONS:
        return {"error": f"Provider '{provider_filter}' not found. Available: {list(ALL_ICONS.keys())}"}

    provider_data = ALL_ICONS[provider_filter]

    if not service_filter:
        # Return all services for this provider
        return provider_data

    if service_filter not in provider_data:
        return {
            "error": f"Service '{service_filter}' not found in '{provider_filter}'. Available: {list(provider_data.keys())}"}

    return {service_filter: provider_data[service_filter]}


@mcp.tool()
def get_diagram_examples(diagram_type: str = "all"):
    """
    Get example code for different types of diagrams.

    Args:
        diagram_type: Type of diagram example to return (aws, k8s, flow, etc. or 'all')
    """
    examples = {
        "aws": """
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Web Service", show=False):
    ELB("lb") >> EC2("web") >> RDS("userdb")
""",
        "k8s": """
from diagrams import Diagram, Cluster
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Ingress, Service

with Diagram("K8s Cluster", show=False):
    ingress = Ingress("domain.com")

    with Cluster("App"):
        svc = Service("svc")
        pods = [Pod("pod1"), Pod("pod2")]

    ingress >> svc >> pods
""",
        "custom": """
from diagrams import Diagram
from diagrams.custom import Custom

with Diagram("Custom", show=False):
    # Ensure you have the icon file locally if using Custom
    Custom("Label", "./my-icon.png")
"""
    }

    if diagram_type == "all":
        return examples

    return {diagram_type: examples.get(diagram_type, "No example found for this type.")}


@mcp.tool()
def generate_diagram(code: str, filename: str = None, timeout: int = 90):
    """
    Generate a diagram from Python code using the diagrams package.

    Args:
        code: Python code using the diagrams package DSL.
        filename: Optional filename to save the diagram to.
        timeout: Execution timeout in seconds.
    """

    # Create a temporary directory for execution
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Prepare the execution context
            # We inject Diagram, Cluster, Edge, and ALL discovered nodes (EC2, Pod, etc.)
            # This allows the user to write code without heavy imports if they choose,
            # though explicit imports are still better for clarity.
            exec_globals = {
                "Diagram": Diagram,
                "Cluster": Cluster,
                "Edge": Edge,
                "Node": Node,
                **NODE_REGISTRY
            }

            # Execute the code
            # We wrap it in a try/except block within the exec to catch runtime errors
            try:
                exec(code, exec_globals)
            except Exception as e:
                return {"status": "error", "message": f"Runtime error: {str(e)}"}

            # Find the generated file
            # Diagrams generates files based on the name passed to Diagram() class
            # We look for any .png file created in the temp dir
            generated_files = list(Path(".").glob("*.png"))

            if not generated_files:
                return {
                    "status": "error",
                    "message": "No diagram image was generated. Did you call with Diagram(..., show=False)?"}

            # Use the most recently modified file or the first one
            generated_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            output_file = generated_files[0]

            # If a filename was requested, we might want to rename it?
            # For now, we return the path.
            # In a real MCP setup, we might copy this to a mounted volume.

            # Copy the generated file back to the original working directory
            # This ensures that if the user mounted their project to the working directory,
            # the file appears in their project.
            import shutil

            target_dir = Path(original_cwd)
            target_filename = filename if filename else output_file.name
            target_path = target_dir / target_filename

            # Ensure extension
            if not target_path.suffix:
                target_path = target_path.with_suffix(".png")

            shutil.copy2(output_file, target_path)
            final_path = str(target_path)

            return {
                "status": "success",
                "path": final_path,
                "filename": target_path.name
            }

        except Exception as e:
            return {"status": "error", "message": f"System error: {str(e)}"}

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    mcp.run()
