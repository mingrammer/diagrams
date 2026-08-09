"""Invariants that must hold for an *installed* diagrams distribution.

These are deliberately written against installed metadata and on-disk files
rather than against the source tree, because the source tree is not what users
get. Both #1149 (console script pointing at a module that was never shipped)
and #1099 (wheel built without the resources tree) were invisible to a test
suite that only ever imported from a checkout.

setUpModule skips the whole module unless `import diagrams` actually resolves
to the installed distribution: without that guard, running from a checkout or
an unpacked sdist silently validates the source tree's own resources/ - the
exact shadowing that let #1099 ship - and running without any install at all
errors with PackageNotFoundError instead of explaining itself.
"""

import importlib
import importlib.metadata
import os
import pkgutil
import unittest
import warnings
from pathlib import Path

import diagrams

DIST_NAME = "diagrams"


def setUpModule():
    try:
        dist = importlib.metadata.distribution(DIST_NAME)
    except importlib.metadata.PackageNotFoundError:
        raise unittest.SkipTest(
            "the 'diagrams' distribution is not installed; these invariants apply to an "
            "installed distribution - run `pip install .` (or `poetry install`) first"
        )
    # An editable/development install has no diagrams/__init__.py under
    # site-packages, so the existence check leaves that flow running.
    installed_init = Path(str(dist.locate_file("diagrams/__init__.py")))
    imported_init = Path(diagrams.__file__).resolve()
    if installed_init.exists() and installed_init.resolve() != imported_init:
        raise unittest.SkipTest(
            f"'import diagrams' resolved to {imported_init}, not the installed copy at "
            f"{installed_init}; run these tests from a directory that does not contain the "
            "diagrams source tree so they exercise the installed distribution"
        )


def _iter_node_classes():
    """Yield every Node subclass that declares an icon, across all providers."""
    for module_info in pkgutil.walk_packages(diagrams.__path__, prefix="diagrams."):
        with warnings.catch_warnings():
            # diagrams.gis.cplusplus warns on import by design; keep suite output clean.
            warnings.simplefilter("ignore", DeprecationWarning)
            module = importlib.import_module(module_info.name)
        for obj in vars(module).values():
            if not isinstance(obj, type) or not issubclass(obj, diagrams.Node):
                continue
            # Only look at classes defined in this module, so a class re-exported
            # by several providers is not checked (and reported) many times over.
            if obj.__module__ != module_info.name:
                continue
            if obj._icon and obj._icon_dir:
                yield obj


class ConsoleScriptTest(unittest.TestCase):
    def test_declared_console_scripts_are_importable(self):
        """A declared entry point whose target module does not ship is a broken install.

        Reproduces #1149: 0.24.1-0.24.4 shipped `diagrams=diagrams.cli:main`
        without ever shipping `diagrams/cli.py`, so `diagrams foo.py` raised
        ModuleNotFoundError.
        """
        entry_points = [
            ep for ep in importlib.metadata.distribution(DIST_NAME).entry_points if ep.group == "console_scripts"
        ]
        self.assertTrue(entry_points, "distribution declares no console_scripts entry point")
        for entry_point in entry_points:
            with self.subTest(entry_point=entry_point.name):
                entry_point.load()


class IconResourceTest(unittest.TestCase):
    def test_every_node_icon_file_exists(self):
        """Every node's icon must resolve to a real file in the installed tree.

        Reproduces #1099: the 0.25.0 wheel contained no `resources/` at all.
        Nothing raised - graphviz silently rendered blank nodes and the CLI
        still exited 0 - so only an explicit file-existence check catches it.
        """
        missing = []
        checked = 0
        for node_class in _iter_node_classes():
            # `_load_icon` only reads class attributes, so calling it with the
            # class as `self` exercises the exact resolution the constructor uses.
            icon_path = diagrams.Node._load_icon(node_class)
            checked += 1
            if not os.path.isfile(icon_path):
                missing.append(f"{node_class.__module__}.{node_class.__name__} -> {icon_path}")

        self.assertGreater(checked, 0, "no icon-bearing Node subclasses were discovered")
        self.assertEqual([], missing[:20], f"{len(missing)} of {checked} node icons are missing from the install")


class VersionTest(unittest.TestCase):
    def test_runtime_version_matches_distribution_metadata(self):
        """`diagrams.__version__` must be read back from metadata, not duplicated.

        Related to #1183: every extra place the version is written by hand is
        another place it can drift out of sync with the release tag.
        """
        self.assertEqual(importlib.metadata.version(DIST_NAME), diagrams.__version__)


if __name__ == "__main__":
    unittest.main()
