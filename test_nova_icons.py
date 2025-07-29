#!/usr/bin/env python3

"""
Test script for new AWS AI/ML service icons
Tests Amazon Nova, AWS App Studio, Amazon CodeWhisperer, and AWS Neuron
"""

from diagrams import Diagram
from diagrams.aws.ml import AmazonNova, AWSAppStudio, AmazonCodewhisperer, AWSNeuron

def test_nova_icons():
    """Test the new Nova and AI service icons"""
    
    with Diagram("New AWS AI/ML Services", show=False, filename="nova_test"):
        # Create instances of the new services
        nova = AmazonNova("Amazon Nova")
        app_studio = AWSAppStudio("AWS App Studio")
        codewhisperer = AmazonCodewhisperer("CodeWhisperer")
        neuron = AWSNeuron("AWS Neuron")
        
        # Create a simple flow
        nova >> app_studio >> codewhisperer >> neuron

    print("✅ Test diagram created successfully!")
    print("📁 Generated file: nova_test.png")
    print("🔍 Please verify the icons render correctly in the diagram")

if __name__ == "__main__":
    test_nova_icons()
