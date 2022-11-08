"""
resources.py provides useful tools for resources processing.

There are 2 commands available.
- clean: clean and unify the resources file names with some rules.
- round: generate the rounded images from the original squared images.
"""

import os
import subprocess
import sys

import config as cfg
from . import resource_dir

_usage = "Usage: resource.py <cmd> <pvd>"


def cleaner_onprem(f):
    f = f.replace("_", "-")
    return f.lower()


def cleaner_aws(f):
    f = f.replace("_", "-")
    f = f.replace("@4x", "")
    f = f.replace("@5x", "")
    f = f.replace("2.0", "2-0")
    f = f.replace("-light-bg4x", "")
    f = f.replace("-light-bg", "")
    for p in cfg.FILE_PREFIXES["aws"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_azure(f):
    f = f.replace("_", "-")
    f = f.replace("(", "").replace(")", "")
    f = "-".join(f.split())
    for p in cfg.FILE_PREFIXES["azure"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_gcp(f):
    f = f.replace("_", "-")
    f = "-".join(f.split())
    for p in cfg.FILE_PREFIXES["gcp"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_ibm(f):
    f = f.replace("_", "-")
    f = "-".join(f.split())
    for p in cfg.FILE_PREFIXES["ibm"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_firebase(f):
    f = f.replace("_", "-")
    f = "-".join(f.split())
    for p in cfg.FILE_PREFIXES["firebase"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_k8s(f):
    f = f.replace("-256", "")
    for p in cfg.FILE_PREFIXES["k8s"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()

def cleaner_digitalocean(f):
    f = f.replace("-32", "")
    for p in cfg.FILE_PREFIXES["digitalocean"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_alibabacloud(f):
    for p in cfg.FILE_PREFIXES["alibabacloud"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_oci(f):
    f = f.replace(" ", "-")
    f = f.replace("_", "-")
    for p in cfg.FILE_PREFIXES["oci"]:
        if f.startswith(p):
            f = f[len(p) :]
            break
    return f.lower()


def cleaner_programming(f):
    return f.lower()


def cleaner_generic(f):
    return f.lower()


def cleaner_saas(f):
    return f.lower()


def cleaner_elastic(f):
    return f.lower()


def cleaner_outscale(f):
    return f.lower()


def cleaner_openstack(f):
    return f.lower()


cleaners = {
    "onprem": cleaner_onprem,
    "aws": cleaner_aws,
    "azure": cleaner_azure,
    "digitalocean": cleaner_digitalocean,
    "gcp": cleaner_gcp,
    "ibm": cleaner_ibm,
    "firebase": cleaner_firebase,
    "k8s": cleaner_k8s,
    "alibabacloud": cleaner_alibabacloud,
    "oci": cleaner_oci,
    "programming": cleaner_programming,
    "saas": cleaner_saas,
    "elastic": cleaner_elastic,
    "outscale": cleaner_outscale,
    "generic": cleaner_generic,
    "openstack": cleaner_openstack,
}


def clean_png(pvd: str) -> None:
    """Refine the resources files names."""

    def _rename(base: str, png: str):
        new = cleaners[pvd](png)
        old_path = os.path.join(base, png)
        new_path = os.path.join(base, new)
        os.rename(old_path, new_path)

    for root, _, files in os.walk(resource_dir(pvd)):
        pngs = filter(lambda f: f.endswith(".png"), files)
        [_rename(root, png) for png in pngs]


def round_png(pvd: str) -> None:
    """Round the images."""

    def _round(base: str, path: str):
        path = os.path.join(base, path)
        subprocess.run([cfg.CMD_ROUND, *cfg.CMD_ROUND_OPTS, path])

    for root, _, files in os.walk(resource_dir(pvd)):
        pngs = filter(lambda f: f.endswith(".png"), files)
        paths = filter(lambda f: "rounded" not in f, pngs)
        [_round(root, path) for path in paths]


def svg2png(pvd: str) -> None:
    """Convert the svg into png"""

    def _convert(base: str, path: str):
        path = os.path.join(base, path)
        subprocess.run([cfg.CMD_SVG2PNG, *cfg.CMD_SVG2PNG_OPTS, path])
        subprocess.run(["rm", path])

    for root, _, files in os.walk(resource_dir(pvd)):
        svgs = filter(lambda f: f.endswith(".svg"), files)
        [_convert(root, path) for path in svgs]


def svg2png2(pvd: str) -> None:
    """Convert the svg into png using image magick"""

    def _convert(base: str, path: str):
        path_src = os.path.join(base, path)
        path_dest = path_src.replace(".svg", ".png")
        subprocess.run([cfg.CMD_SVG2PNG_IM, *cfg.CMD_SVG2PNG_IM_OPTS, path_src, path_dest])
        subprocess.run(["rm", path_src])

    for root, _, files in os.walk(resource_dir(pvd)):
        svgs = filter(lambda f: f.endswith(".svg"), files)
        [_convert(root, path) for path in svgs]


# fmt: off
commands = {
    "clean": clean_png,
    "round": round_png,
    "svg2png": svg2png,
    "svg2png2": svg2png2,
}
# fmt: on

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(_usage)
        sys.exit()

    cmd = sys.argv[1]
    pvd = sys.argv[2]
    if cmd not in commands:
        sys.exit()
    if pvd not in cfg.PROVIDERS:
        sys.exit()
    commands[cmd](pvd)
