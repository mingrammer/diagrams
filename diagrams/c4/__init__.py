"""
A set of nodes and edges to visualize software architecture using the C4 model.
"""
import html
import textwrap
from typing import Any, Dict

from diagrams import Cluster, Node, Edge


def _format_node_label(name: str, key: str, description: str) -> str:
    """Create a graphviz label string for a C4 node"""
    title = f'<font point-size="12"><b>{html.escape(name)}</b></font><br/>'
    subtitle = f'<font point-size="9">[{html.escape(key)}]<br/></font>' if key else ""
    text = f'<br/><font point-size="10">{_format_description(description)}</font>' if description else ""
    return f"<{title}{subtitle}{text}>"


def _format_description(description: str) -> str:
    """
    Formats the description string so it fits into the C4 nodes.

    It line-breaks the description so it fits onto exactly three lines. If there are more
    than three lines, all further lines are discarded and "..." inserted on the last line to
    indicate that it was shortened. This will also html-escape the description so it can
    safely be included in a HTML label.
    """
    wrapper = textwrap.TextWrapper(width=40, max_lines=3)
    lines = [html.escape(line) for line in wrapper.wrap(description)]
    lines += [""] * (3 - len(lines))  # fill up with empty lines so it is always three
    return "<br/>".join(lines)


def _format_edge_label(description: str) -> str:
    """Create a graphviz label string for a C4 edge"""
    wrapper = textwrap.TextWrapper(width=24, max_lines=3)
    lines = [html.escape(line) for line in wrapper.wrap(description)]
    text = "<br/>".join(lines)
    return f'<<font point-size="10">{text}</font>>'


def C4Node(name: str, technology: str = "", description: str = "", type: str = "Container", **kwargs: Dict[str, Any]) -> Node:
    key = f"{type}: {technology}" if technology else type
    node_attributes: Dict[str, Any] = {
        "label": _format_node_label(name, key, description),
        "labelloc": "c",
        "shape": "rect",
        "width": "2.6",
        "height": "1.6",
        "fixedsize": "true",
        "style": "filled",
        "fillcolor": "dodgerblue3",
        "fontcolor": "white",
    }
    # collapse boxes to a smaller form if they don't have a description
    if not description:
        node_attributes.update({"width": "2", "height": "1"})
    node_attributes.update(kwargs)
    return Node(**node_attributes)


def Container(name: str, technology: str = "", description: str = "", **kwargs: Dict[str, Any]) -> Node:
    container_attributes: Dict[str, Any] = {
        "name": name,
        "technology": technology,
        "description": description,
        "type": "Container",
    }
    container_attributes.update(kwargs)
    return C4Node(**container_attributes)


def Database(name: str, technology: str = "", description: str = "", **kwargs: Dict[str, Any]) -> Node:
    database_attributes: Dict[str, Any] = {
        "name": name,
        "technology": technology,
        "description": description,
        "type": "Database",
        "shape": "cylinder",
        "labelloc": "b",
    }
    database_attributes.update(kwargs)
    return C4Node(**database_attributes)


def System(name: str, description: str = "", external: bool = False, **kwargs: Dict[str, Any]) -> Node:
    system_attributes: Dict[str, Any] = {
        "name": name,
        "description": description,
        "type": "External System" if external else "System",
        "fillcolor": "gray60" if external else "dodgerblue4",
    }
    system_attributes.update(kwargs)
    return C4Node(**system_attributes)


def Person(name: str, description: str = "", external: bool = False, **kwargs: Dict[str, Any]) -> Node:
    person_attributes: Dict[str, Any] = {
        "name": name,
        "description": description,
        "type": "External Person" if external else "Person",
        "fillcolor": "gray60" if external else "dodgerblue4",
        "style": "rounded,filled",
    }
    person_attributes.update(kwargs)
    return C4Node(**person_attributes)


def SystemBoundary(name: str, **kwargs: Dict[str, Any]) -> Cluster:
    graph_attributes: Dict[str, Any] = {
        "label": html.escape(name),
        "bgcolor": "white",
        "margin": "16",
        "style": "dashed",
    }
    graph_attributes.update(kwargs)
    return Cluster(name, graph_attr=graph_attributes)


def Relationship(label: str = "", **kwargs: Dict[str, Any]) -> Edge:
    edge_attributes: Dict[str, Any] = {
        "style": "dashed",
        "color": "gray60",
        "label": _format_edge_label(label) if label else "",
    }
    edge_attributes.update(kwargs)
    return Edge(**edge_attributes)
