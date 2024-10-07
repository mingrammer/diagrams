import os
import random
import string
import unittest

from diagrams import Diagram
from diagrams import setcluster, setdiagram
from diagrams.camunda.logo import Dark, Light, Orange
from diagrams.camunda.design import Modeler, Connector, Integration
from diagrams.camunda.automate import Workflow, Decision, Forms, Operate, Tasklist
from diagrams.camunda.monitor import Optimize


class CamundaTest(unittest.TestCase):
    def setUp(self):
        self.name = "diagram-" + "".join([random.choice(string.hexdigits) for n in range(7)]).lower()

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        try:
            os.remove(self.name + ".png")
        except FileNotFoundError:
            pass

    def test_icons(self):
        with Diagram(name=self.name, show=False):
            dark = Dark("dark")
            light = Light("light")
            orange = Orange("orange")
            workflow = Workflow("workflow")
            decision = Decision("decision")
            forms = Forms("forms")
            operate = Operate("operate")
            tasklist = Tasklist("tasklist")
            modeler = Modeler("modeler")
            connector = Connector("connector")
            integration = Integration("integration")
            optimize = Optimize("optimize")
