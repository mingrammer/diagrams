import sys
import unittest

from scripts.check_release_version import ReleaseCheckError, check_tag, project_version


class CheckTagTest(unittest.TestCase):
    def test_accepts_tag_matching_the_project_version(self):
        check_tag("v0.24.4", "0.24.4")

    def test_accepts_tag_without_the_v_prefix(self):
        check_tag("0.24.4", "0.24.4")

    def test_rejects_tag_ahead_of_the_project_version(self):
        """Reproduces #1183: tag v0.24.4 landed on a commit whose pyproject.toml still said 0.24.3."""
        with self.assertRaises(ReleaseCheckError) as ctx:
            check_tag("v0.24.4", "0.24.3")
        self.assertIn("0.24.4", str(ctx.exception))
        self.assertIn("0.24.3", str(ctx.exception))

    def test_rejects_tag_that_is_not_a_version(self):
        with self.assertRaises(ReleaseCheckError):
            check_tag("release-candidate", "0.24.3")


@unittest.skipIf(sys.version_info < (3, 11), "project_version needs tomllib; the release workflow runs on 3.12")
class ProjectVersionTest(unittest.TestCase):
    def test_reads_the_version_out_of_pyproject_toml(self):
        version = project_version()
        self.assertRegex(version, r"^\d+\.\d+")

    def test_tolerates_toml_the_stdlib_parser_accepts(self):
        """A trailing comment on the version line is valid TOML and must not break the gate."""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('[project]\nname = "diagrams"\nversion = "0.26.0"  # bumped by release bot\n')
        self.assertEqual("0.26.0", project_version(Path(f.name)))

    def test_reports_a_missing_version_as_a_check_error_not_a_traceback(self):
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('[project]\nname = "diagrams"\n')
        with self.assertRaises(ReleaseCheckError):
            project_version(Path(f.name))


if __name__ == "__main__":
    unittest.main()
