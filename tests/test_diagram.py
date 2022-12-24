import os
import shutil
import unittest
import pathlib

from diagrams import Cluster, Diagram, Edge, Node
from diagrams import getcluster, getdiagram, setcluster, setdiagram


class DiagramTest(unittest.TestCase):
    def setUp(self):
        self.name = "diagram_test"

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        # Only some tests generate the image file.
        try:
            shutil.rmtree(self.name)
        except OSError:
            # Consider it file
            try:
                os.remove(self.name + ".png")
            except FileNotFoundError:
                pass

    def test_validate_direction(self):
        # Normal directions.
        for dir in ("TB", "BT", "LR", "RL", "tb"):
            Diagram(direction=dir)

        # Invalid directions.
        for dir in ("BR", "TL", "Unknown"):
            with self.assertRaises(ValueError):
                Diagram(direction=dir)

    def test_validate_curvestyle(self):
        # Normal directions.
        for cvs in ("ortho", "curved", "CURVED"):
            Diagram(curvestyle=cvs)

        # Invalid directions.
        for cvs in ("tangent", "unknown"):
            with self.assertRaises(ValueError):
                Diagram(curvestyle=cvs)

    def test_validate_outformat(self):
        # Normal output formats.
        for fmt in ("png", "jpg", "svg", "pdf", "PNG", "dot"):
            Diagram(outformat=fmt)

        # Invalid output formats.
        for fmt in ("pnp", "jpe", "unknown"):
            with self.assertRaises(ValueError):
                Diagram(outformat=fmt)

    def test_with_global_context(self):
        self.assertIsNone(getdiagram())
        with Diagram(name=os.path.join(self.name, "with_global_context"), show=False):
            self.assertIsNotNone(getdiagram())
        self.assertIsNone(getdiagram())

    def test_node_not_in_diagram(self):
        # Node must be belong to a diagrams.
        with self.assertRaises(EnvironmentError):
            Node("node")

    def test_node_to_node(self):
        with Diagram(name=os.path.join(self.name, "node_to_node"), show=False):
            node1 = Node("node1")
            node2 = Node("node2")
            self.assertEqual(node1 - node2, node2)
            self.assertEqual(node1 >> node2, node2)
            self.assertEqual(node1 << node2, node2)

    def test_node_to_nodes(self):
        with Diagram(name=os.path.join(self.name, "node_to_nodes"), show=False):
            node1 = Node("node1")
            nodes = [Node("node2"), Node("node3")]
            self.assertEqual(node1 - nodes, nodes)
            self.assertEqual(node1 >> nodes, nodes)
            self.assertEqual(node1 << nodes, nodes)

    def test_nodes_to_node(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node"), show=False):
            node1 = Node("node1")
            nodes = [Node("node2"), Node("node3")]
            self.assertEqual(nodes - node1, node1)
            self.assertEqual(nodes >> node1, node1)
            self.assertEqual(nodes << node1, node1)

    def test_default_filename(self):
        self.name = "example_1"
        with Diagram(name="Example 1", show=False):
            Node("node1")
        self.assertTrue(os.path.exists(f"{self.name}.png"))

    def test_custom_filename(self):
        self.name = "my_custom_name"
        with Diagram(name="Example 1", filename=self.name, show=False):
            Node("node1")
        self.assertTrue(os.path.exists(f"{self.name}.png"))

    def test_empty_name(self):
        """Check that providing an empty name don't crash, but save in a diagrams_image.xxx file."""
        self.name = 'diagrams_image'
        with Diagram(show=False):
            Node("node1")
        self.assertTrue(os.path.exists(f"{self.name}.png"))
    
    def test_autolabel(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node"), show=False):
            node1 = Node("node1")
            self.assertTrue(node1.label,"Node\nnode1")


    def test_outformat_list(self):
        """Check that outformat render all the files from the list."""
        self.name = 'diagrams_image'
        with Diagram(show=False, outformat=["dot", "png"]):
            Node("node1")
        # both files must exist
        self.assertTrue(os.path.exists(f"{self.name}.png"))
        self.assertTrue(os.path.exists(f"{self.name}.dot"))

        # clean the dot file as it only generated here
        os.remove(self.name + ".dot")


class ClusterTest(unittest.TestCase):
    def setUp(self):
        self.name = "cluster_test"

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        # Only some tests generate the image file.
        try:
            shutil.rmtree(self.name)
        except OSError:
            pass

    def test_validate_direction(self):
        # Normal directions.
        for dir in ("TB", "BT", "LR", "RL"):
            with Diagram(name=os.path.join(self.name, "validate_direction"), show=False):
                Cluster(direction=dir)

        # Invalid directions.
        for dir in ("BR", "TL", "Unknown"):
            with self.assertRaises(ValueError):
                with Diagram(name=os.path.join(self.name, "validate_direction"), show=False):
                    Cluster(direction=dir)

    def test_with_global_context(self):
        with Diagram(name=os.path.join(self.name, "with_global_context"), show=False):
            self.assertIsNone(getcluster())
            with Cluster():
                self.assertIsNotNone(getcluster())
            self.assertIsNone(getcluster())

    def test_with_nested_cluster(self):
        with Diagram(name=os.path.join(self.name, "with_nested_cluster"), show=False):
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
        with Diagram(name=os.path.join(self.name, "node_to_node"), show=False):
            with Cluster():
                node1 = Node("node1")
                node2 = Node("node2")
                self.assertEqual(node1 - node2, node2)
                self.assertEqual(node1 >> node2, node2)
                self.assertEqual(node1 << node2, node2)

    def test_node_to_nodes(self):
        with Diagram(name=os.path.join(self.name, "node_to_nodes"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(node1 - nodes, nodes)
                self.assertEqual(node1 >> nodes, nodes)
                self.assertEqual(node1 << nodes, nodes)

    def test_nodes_to_node(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(nodes - node1, node1)
                self.assertEqual(nodes >> node1, node1)
                self.assertEqual(nodes << node1, node1)


class EdgeTest(unittest.TestCase):
    def setUp(self):
        self.name = "edge_test"

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        # Only some tests generate the image file.
        try:
            shutil.rmtree(self.name)
        except OSError:
            pass

    def test_node_to_node(self):
        with Diagram(name=os.path.join(self.name, "node_to_node"), show=False):
            node1 = Node("node1")
            node2 = Node("node2")
            self.assertEqual(node1 - Edge(color="red") - node2, node2)

    def test_node_to_nodes(self):
        with Diagram(name=os.path.join(self.name, "node_to_nodes"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(node1 - Edge(color="red") - nodes, nodes)

    def test_nodes_to_node(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(nodes - Edge(color="red") - node1, node1)

    def test_nodes_to_node_with_additional_attributes(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node_with_additional_attributes"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(nodes - Edge(color="red") - Edge(color="green") - node1, node1)

    def test_node_to_node_with_attributes(self):
        with Diagram(name=os.path.join(self.name, "node_to_node_with_attributes"), show=False):
            with Cluster():
                node1 = Node("node1")
                node2 = Node("node2")
                self.assertEqual(node1 << Edge(color="red", label="1.1") << node2, node2)
                self.assertEqual(node1 >> Edge(color="green", label="1.2") >> node2, node2)
                self.assertEqual(node1 << Edge(color="blue", label="1.3") >> node2, node2)

    def test_node_to_node_with_additional_attributes(self):
        with Diagram(name=os.path.join(self.name, "node_to_node_with_additional_attributes"), show=False):
            with Cluster():
                node1 = Node("node1")
                node2 = Node("node2")
                self.assertEqual(node1 << Edge(color="red", label="2.1") << Edge(color="blue") << node2, node2)
                self.assertEqual(node1 >> Edge(color="green", label="2.2") >> Edge(color="red") >> node2, node2)
                self.assertEqual(node1 << Edge(color="blue", label="2.3") >> Edge(color="black") >> node2, node2)

    def test_nodes_to_node_with_attributes_loop(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node_with_attributes_loop"), show=False):
            with Cluster():
                node = Node("node")
                self.assertEqual(node >> Edge(color="red", label="3.1") >> node, node)
                self.assertEqual(node << Edge(color="green", label="3.2") << node, node)
                self.assertEqual(node >> Edge(color="blue", label="3.3") << node, node)
                self.assertEqual(node << Edge(color="pink", label="3.4") >> node, node)

    def test_nodes_to_node_with_attributes_bothdirectional(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node_with_attributes_bothdirectional"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(nodes << Edge(color="green", label="4") >> node1, node1)

    def test_nodes_to_node_with_attributes_bidirectional(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node_with_attributes_bidirectional"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(nodes << Edge(color="blue", label="5") >> node1, node1)

    def test_nodes_to_node_with_attributes_onedirectional(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node_with_attributes_onedirectional"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(nodes >> Edge(color="red", label="6.1") >> node1, node1)
                self.assertEqual(nodes << Edge(color="green", label="6.2") << node1, node1)

    def test_nodes_to_node_with_additional_attributes_directional(self):
        with Diagram(name=os.path.join(self.name, "nodes_to_node_with_additional_attributes_directional"), show=False):
            with Cluster():
                node1 = Node("node1")
                nodes = [Node("node2"), Node("node3")]
                self.assertEqual(
                    nodes >> Edge(color="red", label="6.1") >> Edge(color="blue", label="6.2") >> node1, node1
                )
                self.assertEqual(
                    nodes << Edge(color="green", label="6.3") << Edge(color="pink", label="6.4") << node1, node1
                )


class ResourcesTest(unittest.TestCase):
    def test_folder_depth(self):
        """
        The code currently only handles resource folders up to a dir depth of 2
        i.e. resources/<provider>/<type>/<image>, so check that this depth isn't
        exceeded.
        """
        resources_dir = pathlib.Path(__file__).parent.parent / 'resources'
        max_depth = max(os.path.relpath(d, resources_dir).count(os.sep) + 1
                        for d, _, _ in os.walk(resources_dir))
        self.assertLessEqual(max_depth, 2)
