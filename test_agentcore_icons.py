#!/usr/bin/env python3

"""
Test script for AWS Agentcore Bedrock icons
Validates that all 11 new Agentcore icons can be imported and used correctly.
"""

from diagrams import Diagram
from diagrams.aws.ml import (
    Agentcore,
    AiAgent, 
    Runtime,
    Gateway,
    Identity,
    CodeInterpreter,
    Observability,
    BrowserTool,
    Memory,
    Evaluations,
    PolicyEngineAgenticGuardrails
)

def test_agentcore_icons():
    """Test all Agentcore icons in a sample diagram"""
    
    with Diagram("AWS Agentcore Bedrock Icons Test", show=False, filename="agentcore_test"):
        # Core Agentcore components
        agentcore = Agentcore("Agentcore")
        ai_agent = AiAgent("AI Agent")
        runtime = Runtime("Runtime")
        gateway = Gateway("Gateway")
        
        # Identity and security
        identity = Identity("Identity")
        policy_engine = PolicyEngineAgenticGuardrails("Policy Engine")
        
        # Tools and capabilities
        code_interpreter = CodeInterpreter("Code Interpreter")
        browser_tool = BrowserTool("Browser Tool")
        memory = Memory("Memory")
        
        # Monitoring and evaluation
        observability = Observability("Observability")
        evaluations = Evaluations("Evaluations")
        
        # Create a flow showing the relationships
        agentcore >> ai_agent >> runtime
        ai_agent >> [code_interpreter, browser_tool, memory]
        gateway >> identity >> policy_engine
        [runtime, code_interpreter, browser_tool] >> observability
        observability >> evaluations
        
    print("✅ Test diagram created successfully!")
    print("📁 Generated file: agentcore_test.png")
    print("🔍 Please verify the icons render correctly in the diagram")

if __name__ == "__main__":
    test_agentcore_icons()
