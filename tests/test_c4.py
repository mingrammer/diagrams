import os
import random
import string
import unittest

from diagrams import Diagram
from diagrams import setcluster, setdiagram
from diagrams.c4 import Person, Container, Database, System, SystemBoundary, Dependency


class C4Test(unittest.TestCase):
    def setUp(self):
        self.name = "diagram-" + "".join([random.choice(string.hexdigits) for n in range(7)])

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

            person >> container >> database

    def test_systems(self):
        with Diagram(name=self.name, show=False):
            system = System("system", "The internal system.")
            system_without_description = System("unknown")
            external_system = System("external", "The external system.", external=True)

            system >> system_without_description >> external_system

    def test_edges(self):
        with Diagram(name=self.name, show=False):
            c1 = Container("container1", "type", "description")
            c2 = Container("container2", "type", "description")

            c1 >> Dependency("depends on") >> c2
            c1 << Dependency("is dependend on") << c2

    def test_cluster(self):
        with Diagram(name=self.name, show=False):
            with SystemBoundary("System"):
                Container("container", "type", "description")
