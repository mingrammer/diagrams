import os
import unittest

from diagrams import Cluster, Diagram, Node
from diagrams import getcluster, getdiagram, setcluster, setdiagram


class DiagramTest(unittest.TestCase):
    def setUp(self):
        self.name = "test"

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        # Only some tests generate the image file.
        try:
            os.remove(self.name + ".png")
        except FileNotFoundError:
            pass

    def test_validate_direction(self):
        # Normal directions.
        for dir in ("TB", "BT", "LR", "RL"):
            Diagram(direction=dir)

        # Invalid directions.
        for dir in ("BR", "TL", "Unknown"):
            with self.assertRaises(ValueError):
                Diagram(direction=dir)

    def test_validate_outformat(self):
        # Normal output formats.
        for fmt in ("png", "jpg", "svg", "pdf"):
            Diagram(outformat=fmt)

        # Invalid output formats.
        for fmt in ("pnp", "jpe", "unknown"):
            with self.assertRaises(ValueError):
                Diagram(outformat=fmt)

    def test_with_global_context(self):
        self.assertIsNone(getdiagram())
        with Diagram(name=self.name, show=False):
            self.assertIsNotNone(getdiagram())
        self.assertIsNone(getdiagram())

    def test_node_not_in_diagram(self):
        # Node must be belong to a diagrams.
        with self.assertRaises(EnvironmentError):
            Node("node")

    def test_node_to_node(self):
        with Diagram(name=self.name, show=False):
            node1 = Node("node1")
            node2 = Node("node2")
            self.assertEqual(node1 - node2, node2)
            self.assertEqual(node1 >> node2, node2)
            self.assertEqual(node1 << node2, node2)

    def test_node_to_nodes(self):
        with Diagram(name=self.name, show=False):
            node1 = Node("node1")
            nodes = [Node("node2"), Node("node3")]
            self.assertEqual(node1 - nodes, nodes)
            self.assertEqual(node1 >> nodes, nodes)
            self.assertEqual(node1 << nodes, nodes)

    def test_nodes_to_node(self):
        with Diagram(name=self.name, show=False):
            node1 = Node("node1")
            nodes = [Node("node2"), Node("node3")]
            self.assertEqual(nodes - node1, node1)
            self.assertEqual(nodes >> node1, node1)
            self.assertEqual(nodes << node1, node1)


class ClusterTest(unittest.TestCase):
    def setUp(self):
        self.name = "test"

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        # Only some tests generate the image file.
        try:
            os.remove(self.name + ".png")
        except FileNotFoundError:
            pass

    def test_validate_direction(self):
        # Normal directions.
        for dir in ("TB", "BT", "LR", "RL"):
            with Diagram(name=self.name, show=False):
                Cluster(direction=dir)

        # Invalid directions.
        for dir in ("BR", "TL", "Unknown"):
            with self.assertRaises(ValueError):
                with Diagram(name=self.name, show=False):
                    Cluster(direction=dir)

    def test_with_global_context(self):
        with Diagram(name=self.name, show=False):
            self.assertIsNone(getcluster())
            with Cluster():
                self.assertIsNotNone(getcluster())
            self.assertIsNone(getcluster())

    def test_with_nested_cluster(self):
        with Diagram(name=self.name, show=False):
            self.assertIsNone(getcluster())
            with Cluster() as c1:
                self.assertEqual(c1, getcluster())
                with Cluster() as c2:
                    self.assertEqual(c2, getcluster())
                self.assertEqual(c1, getcluster())
            self.assertIsNone(getcluster())

    def test_node_not_in_diagram(self):
        # Node must be belong to a diagrams.
        with self.assertRaises(EnvironmentError):
            Node("node")

    def test_node_to_node(self):
        with Diagram(name=self.name, show=False):
            with Cluster():
                node1 = Node("node1")
                node2 = Node("node2")
                self.assertEqual(node1 - node2, node2)
                self.assertEqual(node1 >> node2, node2)
                self.assertEqual(node1 << node2, node2)

    def test_node_to_nodes(self):
        with Diagram(name=self.name, show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(node1 - nodes, nodes)
                self.assertEqual(node1 >> nodes, nodes)
                self.assertEqual(node1 << nodes, nodes)

    def test_nodes_to_node(self):
        with Diagram(name=self.name, show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(nodes - node1, node1)
                self.assertEqual(nodes >> node1, node1)
                self.assertEqual(nodes << node1, node1)
