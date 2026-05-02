import os
import unittest

from diagrams import Diagram, setcluster, setdiagram
from diagrams.aws.ml import (
    AgentCore,
    AiAgent,
    AmazonNova,
    AWSAppStudio,
    AWSNeuron,
    BrowserTool,
    CodeInterpreter,
    Evaluations,
    Gateway,
    Identity,
    Memory,
    Observability,
    PolicyEngineAgenticGuardrails,
    Runtime,
    AIAgent,
    DLC,
    OBS,
    PEAG,
)


class AgentcoreIconsTest(unittest.TestCase):
    def setUp(self):
        self.name = "test_agentcore_icons"

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        try:
            os.remove(self.name + ".png")
        except FileNotFoundError:
            pass

    def test_agentcore_diagram(self):
        with Diagram(name=self.name, show=False, filename=self.name):
            agentcore = AgentCore("Agentcore")
            ai_agent = AiAgent("AI Agent")
            runtime = Runtime("Runtime")
            gateway = Gateway("Gateway")
            identity = Identity("Identity")
            policy_engine = PolicyEngineAgenticGuardrails("Policy Engine")
            code_interpreter = CodeInterpreter("Code Interpreter")
            browser_tool = BrowserTool("Browser Tool")
            memory = Memory("Memory")
            observability = Observability("Observability")
            evaluations = Evaluations("Evaluations")

            agentcore >> ai_agent >> runtime
            ai_agent >> [code_interpreter, browser_tool, memory]
            gateway >> identity >> policy_engine
            [runtime, code_interpreter, browser_tool] >> observability
            observability >> evaluations

        self.assertTrue(os.path.exists(self.name + ".png"))


class NovaIconsTest(unittest.TestCase):
    def setUp(self):
        self.name = "test_nova_icons"

    def tearDown(self):
        setdiagram(None)
        setcluster(None)
        try:
            os.remove(self.name + ".png")
        except FileNotFoundError:
            pass

    def test_nova_diagram(self):
        with Diagram(name=self.name, show=False, filename=self.name):
            nova = AmazonNova("Amazon Nova")
            app_studio = AWSAppStudio("AWS App Studio")
            neuron = AWSNeuron("AWS Neuron")

            nova >> app_studio >> neuron

        self.assertTrue(os.path.exists(self.name + ".png"))


class AliasesTest(unittest.TestCase):
    def test_aliases_exist(self):
        self.assertIs(AIAgent, AiAgent)
        self.assertIs(PEAG, PolicyEngineAgenticGuardrails)
        self.assertIs(OBS, Observability)


if __name__ == "__main__":
    unittest.main()
