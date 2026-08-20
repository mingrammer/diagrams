"""Generate playground build assets from the diagrams package.

Outputs (under --out):
  catalog.json          node classes / aliases / icons / constructor signatures
  icons/**              copy of resources/ for the preview <image> tags
  wheels/*.whl          slim diagrams wheel (resources stripped; not needed at
                        runtime because Node._load_icon only builds path strings)
  wheels/manifest.json  {"wheel": "<filename>"} for the worker to locate it
"""

import argparse
import importlib
import inspect
import json
import pkgutil
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def build_catalog(repo_root: Path) -> dict:
    sys.path.insert(0, str(repo_root))
    import diagrams
    from diagrams import Cluster, Diagram, Edge, Node

    modules = {}
    for info in pkgutil.walk_packages([str(repo_root / "diagrams")], prefix="diagrams."):
        if any(part.startswith("_") for part in info.name.split(".")):
            continue
        mod = importlib.import_module(info.name)
        classes, aliases = {}, {}
        for attr, val in vars(mod).items():
            if attr.startswith("_") or not inspect.isclass(val):
                continue
            if not issubclass(val, Node) or val.__module__ != info.name:
                continue
            if getattr(val, "_icon", None) is None:
                continue
            # Check if icon file exists on disk
            icon_rel = "/".join([*Path(val._icon_dir).parts[1:], val._icon])
            if not (repo_root / "resources" / icon_rel).exists():
                print(
                    f"warning: skipping {info.name}.{val.__name__} — missing icon resources/{icon_rel}", file=sys.stderr
                )
                continue
            if attr == val.__name__:
                classes[attr] = val
            else:  # module-level alias assignment (e.g. ECS = ElasticContainerService)
                aliases.setdefault(val.__name__, []).append(attr)
        if classes:
            modules[info.name] = [
                {
                    "name": name,
                    "aliases": sorted(aliases.get(name, [])),
                    # _icon_dir is "resources/aws/compute" — strip leading segment
                    "icon": "/".join([*Path(cls._icon_dir).parts[1:], cls._icon]),
                }
                for name, cls in sorted(classes.items())
            ]

    def signature_params(fn) -> list:
        return [str(p) for p in list(inspect.signature(fn).parameters.values())[1:]]

    return {
        "modules": modules,
        "signatures": {
            "Diagram": signature_params(Diagram.__init__),
            "Cluster": signature_params(Cluster.__init__),
            "Edge": signature_params(Edge.__init__),
        },
    }


def build_slim_wheel(repo_root: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", tmp, str(repo_root)],
            check=True,
        )
        src = next(Path(tmp).glob("diagrams-*.whl"))
        dst = out_dir / src.name
        with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename.startswith("resources/"):
                    continue
                data = zin.read(item.filename)
                if item.filename.endswith(".dist-info/RECORD"):
                    lines = [l for l in data.decode().splitlines() if not l.startswith("resources/")]
                    data = ("\n".join(lines) + "\n").encode()
                zout.writestr(item, data)
    return dst


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo_root, out = args.repo_root.resolve(), args.out.resolve()

    catalog = build_catalog(repo_root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "catalog.json").write_text(json.dumps(catalog))
    print(f"catalog.json: {sum(len(v) for v in catalog['modules'].values())} classes")

    icons_dir = out / "icons"
    shutil.copytree(repo_root / "resources", icons_dir, dirs_exist_ok=True)
    print(f"icons: copied to {icons_dir}")

    wheel = build_slim_wheel(repo_root, out / "wheels")
    (out / "wheels" / "manifest.json").write_text(json.dumps({"wheel": wheel.name}))
    print(f"wheel: {wheel.name} ({wheel.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
