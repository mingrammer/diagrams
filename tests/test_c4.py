import os
import random
import string
import unittest

from diagrams import setcluster, setdiagram, Diagram
from diagrams.c4 import Person, Container, Database, System, SystemBoundary, Relationship


class C4Test(unittest.TestCase):
    def setUp(self) -> None:
        self.name: str = "diagram-" + "".join([random.choice(string.hexdigits) for n in range(7)]).lower()

    def tearDown(self) -> None:
        setdiagram(None)
        setcluster(None)
        try:
            os.remove(f"{self.name}.png")
        except FileNotFoundError:
            pass

    def test_nodes(self) -> None:
        with Diagram(name=self.name, show=False):
            person = Person("person", "A person.")
            container = Container("container", "Java application", "The application.")
            database = Database("database", "Oracle database", "Stores information.")

    def test_external_nodes(self) -> None:
        with Diagram(name=self.name, show=False):
            external_person = Person("person", external=True)
            external_system = System("external", external=True)

    def test_systems(self) -> None:
        with Diagram(name=self.name, show=False):
            system = System("system", "The internal system.")
            system_without_description = System("unknown")

    def test_edges(self) -> None:
        with Diagram(name=self.name, show=False):
            c1 = Container("container1")
            c2 = Container("container2")

            c1 >> c2

    def test_edges_with_labels(self) -> None:
        with Diagram(name=self.name, show=False):
            c1 = Container("container1")
            c2 = Container("container2")

            c1 >> Relationship("depends on") >> c2
            c1 << Relationship("is depended on by") << c2

    def test_edge_without_constraint(self) -> None:
        with Diagram(name=self.name, show=False):
            s1 = System("system 1")
            s2 = System("system 2")

            s1 >> Relationship(constraint="False") >> s2 # type: ignore[arg-type]

    def test_cluster(self) -> None:
        with Diagram(name=self.name, show=False):
            with SystemBoundary("System"):
                Container("container", "type", "description")
