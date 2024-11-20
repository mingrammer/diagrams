import os
from pathlib import Path

import config as cfg


def base_dir() -> Path:
    return Path(os.path.abspath(os.path.dirname(__file__))).parent


def app_root_dir(pvd: str) -> str:
    return os.path.join(base_dir(), cfg.DIR_APP_ROOT, pvd)


def doc_root_dir() -> str:
    return os.path.join(base_dir(), cfg.DIR_DOC_ROOT)


def resource_dir(pvd: str) -> str:
    return os.path.join(base_dir(), cfg.DIR_RESOURCE, pvd)


def template_dir() -> str:
    return os.path.join(base_dir(), cfg.DIR_TEMPLATE)
