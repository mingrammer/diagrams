import os
import unittest
from unittest.mock import mock_open, patch
from io import StringIO

from diagrams.cli import run

class CliTest(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_diagram.py"
        # dummy content for the test file
        self.test_content_1 = """
from diagrams import Diagram
with Diagram(name="Test", show=False):
    pass
"""
        # content from getting started examples with utf-8
        # only support the installed fonts defined in Dockerfile
        self.test_content_2 = """
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("test_2", show=False, direction="TB"):
    ELB("lb") >> [EC2("ワーカー１"),
                  EC2("작업자 2를"),
                  EC2("робітник 3"),
                  EC2("worker4"),
                  EC2("työntekijä 4")] >> RDS("events")
"""
    def tearDown(self):
        try:
            os.remove("test.png")
        except FileNotFoundError:
            pass

    def test_run_with_valid_file(self):
        # write the test file
        with open(self.test_file, "w") as f:
            f.write(self.test_content_1)
        with patch("sys.argv", ["diagrams", self.test_file]):
            exit_code = run()
            self.assertEqual(exit_code, 0)
        try:
            os.remove(self.test_file)
        except FileNotFoundError:
            pass


    def test_run_with_multiple_files(self):

        multiple_files = ["file1.py", "file2.py"]

        # write the code files
        with open("file1.py", "w") as f:
            f.write(self.test_content_1)
        with open("file2.py", "w") as f:
            f.write(self.test_content_2)

        with patch("sys.argv", ["diagrams"] + multiple_files):
            exit_code = run()
            self.assertEqual(exit_code, 0)

        # cleanup code file
        for one_file in multiple_files:
            try:
                os.remove(one_file)
            except FileNotFoundError:
                pass
        # cleanup generated image
        try:
            os.remove("test_2.png")
        except FileNotFoundError:
            pass

    def test_run_with_no_arguments(self):
        with patch("sys.argv", ["diagrams"]):
            with patch("sys.stderr", new=StringIO()) as fake_stderr:
                with self.assertRaises(SystemExit):
                    run()
                self.assertIn("the following arguments are required: path", fake_stderr.getvalue())

    def test_run_with_nonexistent_file(self):
        with patch("sys.argv", ["diagrams", "nonexistent.py"]):
            with self.assertRaises(FileNotFoundError):
                run()

    def test_run_with_invalid_python_code(self):
        invalid_content = "this is not valid python code"
        with patch("builtins.open", mock_open(read_data=invalid_content)):
            with patch("sys.argv", ["diagrams", self.test_file]):
                with self.assertRaises(SyntaxError):
                    run()
