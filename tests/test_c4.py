import os
import random
import string
import unittest

from diagrams import Diagram
from diagrams import setcluster, setdiagram
from diagrams.c4 import Person, Container, Database, System, SystemBoundary, Relationship


class C4Test(unittest.TestCase):
    def setUp(self):
        self.name = "diagram-" + "".join([random.choice(string.hexdigits) for n in range(7)]).lower()

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        try:
            os.remove(self.name + ".png")
        except FileNotFoundError:
            pass

    def test_nodes(self):
        with Diagram(name=self.name, show=False):
            person = Person("person", "A person.")
            container = Container("container", "Java application", "The application.")
            database = Database("database", "Oracle database", "Stores information.")

    def test_external_nodes(self):
        with Diagram(name=self.name, show=False):
            external_person = Person("person", external=True)
            external_system = System("external", external=True)

    def test_systems(self):
        with Diagram(name=self.name, show=False):
            system = System("system", "The internal system.")
            system_without_description = System("unknown")

    def test_edges(self):
        with Diagram(name=self.name, show=False):
            c1 = Container("container1")
            c2 = Container("container2")

            c1 >> c2

    def test_edges_with_labels(self):
        with Diagram(name=self.name, show=False):
            c1 = Container("container1")
            c2 = Container("container2")

            c1 >> Relationship("depends on") >> c2
            c1 << Relationship("is depended on by") << c2

    def test_edge_without_constraint(self):
        with Diagram(name=self.name, show=False):
            s1 = System("system 1")
            s2 = System("system 2")

            s1 >> Relationship(constraint="False") >> s2

    def test_cluster(self):
        with Diagram(name=self.name, show=False):
            with SystemBoundary("System"):
                Container("container", "type", "description")
