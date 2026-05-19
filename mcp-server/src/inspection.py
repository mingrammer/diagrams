import importlib
import inspect
import pkgutil
import sys
from collections import defaultdict

import diagrams
from diagrams import Node


def get_all_nodes():
    """
    Dynamically inspects the diagrams package and returns a dictionary of all available Nodes.

    Returns:
        dict: A nested dictionary structure:
              {
                  "provider": {
                      "service": ["NodeName1", "NodeName2", ...]
                  }
              }
    """
    # Initialize the structure
    icons = defaultdict(lambda: defaultdict(list))

    # We also keep a flat map for the execution context: Name -> Class
    # This handles potential name collisions by favoring the last seen or explicit logic if needed.
    node_registry = {}

    # Iterate through all subpackages in diagrams (e.g., aws, azure, k8s)
    # We look at the path of the diagrams package
    path = diagrams.__path__
    prefix = diagrams.__name__ + "."

    for _, provider_name, ispkg in pkgutil.iter_modules(path, prefix):
        if not ispkg:
            continue

        # e.g., provider_name = "diagrams.aws"
        short_provider = provider_name.split(".")[-1]

        # Skip internal modules if any (base, etc are actually useful, but we focus on providers)
        if short_provider in ['base', 'custom']:
            # 'custom' and 'base' might be treated differently, but for now we scan them
            pass

        try:
            provider_module = importlib.import_module(provider_name)
        except ImportError:
            # Skip providers that might have missing system deps or issues
            continue

        # Now iterate modules within the provider (e.g., diagrams.aws.compute)
        if hasattr(provider_module, "__path__"):
            for _, service_name, _ in pkgutil.iter_modules(provider_module.__path__, provider_name + "."):
                try:
                    service_module = importlib.import_module(service_name)
                    short_service = service_name.split(".")[-1]

                    # Inspect classes in this service module
                    for name, obj in inspect.getmembers(service_module, inspect.isclass):
                        # Must inherit from Node
                        if issubclass(obj, Node) and obj is not Node:
                            # Verify it belongs to this module (to avoid re-export noise)
                            # or at least is defined in the diagrams package
                            if obj.__module__.startswith("diagrams"):
                                # Ensure the object actually belongs to this service (or a submodule of it)
                                # This prevents listing imported classes from other services (e.g. Trace
                                # in operations vs devtools)
                                if not obj.__module__.startswith(service_name):
                                    continue

                                icons[short_provider][short_service].append(name)
                                node_registry[name] = obj

                except ImportError:
                    continue
                except Exception:
                    continue

    return icons, node_registry
