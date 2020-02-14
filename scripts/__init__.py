import os
from pathlib import Path

import config as cfg


def app_root_dir(pvd: str) -> str:
    basedir = Path(os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(basedir.parent, cfg.DIR_APP_ROOT, pvd)


def doc_root_dir() -> str:
    basedir = Path(os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(basedir.parent, cfg.DIR_DOC_ROOT)


def resource_dir(pvd: str) -> str:
    basedir = Path(os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(basedir.parent, cfg.DIR_RESOURCE, pvd)


def template_dir() -> str:
    basedir = Path(os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(basedir.parent, cfg.DIR_TEMPLATE)
