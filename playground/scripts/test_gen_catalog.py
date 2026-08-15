import importlib.util
import zipfile
from pathlib import Path

# Load the sibling gen_catalog.py by file path rather than a bare
# `from gen_catalog import ...` after a sys.path hack — the latter forces an
# import that isort keeps reordering above the path setup (breaking it) and
# that seed-isort-config misclassifies as third-party.
_spec = importlib.util.spec_from_file_location("gen_catalog", Path(__file__).parent / "gen_catalog.py")
gen_catalog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_catalog)
build_catalog = gen_catalog.build_catalog
build_slim_wheel = gen_catalog.build_slim_wheel

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_catalog_contains_ec2_with_icon():
    catalog = build_catalog(REPO_ROOT)
    compute = catalog["modules"]["diagrams.aws.compute"]
    ec2 = next(c for c in compute if c["name"] == "EC2")
    assert ec2["icon"] == "aws/compute/ec2.png"
    assert (REPO_ROOT / "resources" / ec2["icon"]).exists()


def test_catalog_records_aliases():
    catalog = build_catalog(REPO_ROOT)
    compute = catalog["modules"]["diagrams.aws.compute"]
    ecs = next(c for c in compute if c["name"] == "ElasticContainerService")
    assert "ECS" in ecs["aliases"]


def test_catalog_signatures_have_core_classes():
    catalog = build_catalog(REPO_ROOT)
    assert any(p.startswith("name") for p in catalog["signatures"]["Diagram"])
    assert any(p.startswith("label") for p in catalog["signatures"]["Cluster"])
    assert any(p.startswith("forward") for p in catalog["signatures"]["Edge"])


def test_all_catalog_icons_exist_on_disk():
    catalog = build_catalog(REPO_ROOT)
    missing = [
        c["icon"]
        for classes in catalog["modules"].values()
        for c in classes
        if not (REPO_ROOT / "resources" / c["icon"]).exists()
    ]
    assert missing == []


def test_slim_wheel_has_no_resources(tmp_path):
    wheel = build_slim_wheel(REPO_ROOT, tmp_path)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
        assert not [n for n in names if n.startswith("resources/")]
        assert [n for n in names if n.startswith("diagrams/")]
        record = next(n for n in names if n.endswith(".dist-info/RECORD"))
        record_body = zf.read(record).decode()
        assert "resources/" not in record_body
    assert wheel.stat().st_size < 3_000_000  # confirms the 38MB resources are stripped
