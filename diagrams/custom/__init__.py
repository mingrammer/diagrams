"""
Custom provides the possibility of load an image to be presented as a node.
"""

from typing import Any, Dict, Optional, override

from diagrams import Node


class Custom(Node):
    _provider = "custom"
    _type = "custom"
    _icon_dir = None

    fontcolor = "#ffffff"

    @override
    def _load_icon(self) -> Optional[str]:
        return self._icon

    @override
    def __init__(self, label: str, icon_path: Optional[str], *, nodeid: Optional[str] = None, **attrs: Dict[Any, Any]):
        self._icon: Optional[str] = icon_path
        super().__init__(label, nodeid=nodeid, **attrs)
