import os
import sys
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, Template

import config as cfg
from . import app_root_dir, resource_dir, template_dir

_usage = "Usage: generate.py <aws|gcp|azure>"


def load_tmpl(tmpl: str) -> Template:
    env = Environment(loader=FileSystemLoader(template_dir()))
    env.filters["up_or_title"] = up_or_title
    return env.get_template(tmpl)


def up_or_title(pvd: str, s: str) -> str:
    return s.upper() if s in cfg.UPPER_WORDS[pvd] else s.title()


def gen_classes(pvd: str, typ: str, paths: Iterable[str]) -> str:
    """Generate all service node classes based on resources paths with class templates."""
    tmpl = load_tmpl(cfg.TMPL_MODULE)

    def _gen_class_meta(path: str) -> dict:
        base = os.path.splitext(path)[0]
        name = "".join([up_or_title(pvd, s) for s in base.split("-")])
        return {"name": name, "icon": path}

    metas = map(_gen_class_meta, paths)
    aliases = cfg.ALIASES[pvd][typ] if typ in cfg.ALIASES[pvd] else {}
    return tmpl.render(pvd=pvd, typ=typ, metas=metas, aliases=aliases)


def make_module(pvd: str, typ: str, classes: str) -> None:
    """Create a module file"""
    mod_path = os.path.join(app_root_dir(pvd), f"{typ}.py")
    with open(mod_path, "w+") as f:
        f.write(classes)


def generate(pvd: str) -> None:
    """Generates a service node classes."""
    for root, _, files in os.walk(resource_dir(pvd)):
        # Extract the names and paths from resources.
        files.sort()
        pngs = filter(lambda f: f.endswith(".png"), files)
        paths = filter(lambda f: "rounded" not in f, pngs)

        # Skip the top-root directory.
        typ = os.path.basename(root)
        if typ == pvd:
            continue

        classes = gen_classes(pvd, typ, paths)
        make_module(pvd, typ, classes)


if __name__ == "__main__":
    pvd = sys.argv[1]
    if pvd not in cfg.PROVIDERS:
        sys.exit()
    generate(pvd)
