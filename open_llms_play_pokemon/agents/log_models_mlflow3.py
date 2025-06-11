#!/usr/bin/env python3
"""
MLFlow 3.0 Model Logging Example for Pokemon Red Agents

This script demonstrates how to log models using MLFlow 3's new 
`mlflow.pyfunc.log_model` API with the "Models from Code" approach.
"""

import logging
import os
from pathlib import Path

import mlflow
from mlflow.models import infer_signature


def setup_mlflow():
    """Set up MLFlow tracking."""
    mlflow.set_tracking_uri("http://localhost:8080")
    mlflow.set_experiment("pokemon-agents-mlflow3")
    logging.basicConfig(level=logging.INFO)


def log_dspy_agent_model():
    """Log the DSPy-based Pokemon agent model using MLFlow 3."""
    
    # Get the path to the model code file
    model_code_path = Path(__file__).parent / "dspy_pokemon_model.py"
    
    # Define input/output examples for signature inference
    input_example = {"action": "start_game", "headless": True}
    
    # Since we can't easily run the model to get an output example in this context,
    # we'll define the expected output structure
    output_example = {
        "status": "success",
        "screen_base64": "base64_encoded_screenshot",
        "action_executed": "ParsedAction(...)",
        "success": True
    }
    
    # Infer signature from examples
    signature = infer_signature(input_example, output_example)
    
    with mlflow.start_run(run_name="dspy-pokemon-agent"):
        # Log model using MLFlow 3's new API
        model_info = mlflow.pyfunc.log_model(
            name="dspy_pokemon_agent",  # MLFlow 3 uses 'name' instead of 'artifact_path'
            python_model=str(model_code_path),  # Path to the model code file
            signature=signature,
            input_example=input_example,
            pip_requirements=[
                "dspy-ai>=2.6.27",
                "openai>=1.82.0",  
                "pillow>=11.2.1",
                "pyboy>=2.6.0",
                "python-dotenv>=0.9.9",
            ],
            metadata={
                "agent_type": "dspy_react",
                "game": "pokemon_red",
                "description": "DSPy-based ReAct agent for playing Pokemon Red"
            }
        )
        
        # Log additional parameters and tags
        mlflow.log_param("agent_framework", "dspy")
        mlflow.log_param("model_type", "react_agent")
        mlflow.log_param("game_target", "pokemon_red")
        
        mlflow.set_tag("mlflow_version", "3.0")
        mlflow.set_tag("logging_method", "models_from_code")
        
        logging.info(f"DSPy agent model logged successfully!")
        logging.info(f"Model URI: {model_info.model_uri}")
        logging.info(f"Model ID: {model_info.model_id}")
        
        return model_info


def log_openai_agent_model():
    """Log the OpenAI-based Pokemon agent model using MLFlow 3."""
    
    # Get the path to the model code file
    model_code_path = Path(__file__).parent / "openai_pokemon_model.py"
    
    # Define input/output examples for signature inference
    input_example = {"action": "start_game", "headless": True}
    
    output_example = {
        "status": "success",
        "screen_base64": "base64_encoded_screenshot",
        "ai_response": "Thought: ... Action: ...",
        "action_executed": "ParsedAction(...)",
        "success": True
    }
    
    # Infer signature from examples
    signature = infer_signature(input_example, output_example)
    
    with mlflow.start_run(run_name="openai-pokemon-agent"):
        # Log model using MLFlow 3's new API
        model_info = mlflow.pyfunc.log_model(
            name="openai_pokemon_agent",  # MLFlow 3 uses 'name' instead of 'artifact_path'
            python_model=str(model_code_path),  # Path to the model code file
            signature=signature,
            input_example=input_example,
            pip_requirements=[
                "openai>=1.82.0",
                "pillow>=11.2.1",
                "pyboy>=2.6.0", 
                "python-dotenv>=0.9.9",
            ],
            metadata={
                "agent_type": "openai_chat",
                "game": "pokemon_red",
                "description": "OpenAI Chat-based agent for playing Pokemon Red"
            }
        )
        
        # Log additional parameters and tags
        mlflow.log_param("agent_framework", "openai")
        mlflow.log_param("model_type", "chat_agent")
        mlflow.log_param("game_target", "pokemon_red")
        
        mlflow.set_tag("mlflow_version", "3.0")
        mlflow.set_tag("logging_method", "models_from_code")
        
        logging.info(f"OpenAI agent model logged successfully!")
        logging.info(f"Model URI: {model_info.model_uri}")
        logging.info(f"Model ID: {model_info.model_id}")
        
        return model_info


def demonstrate_model_loading_and_inference(model_info):
    """Demonstrate how to load and use the logged model."""
    
    logging.info(f"Loading model from URI: {model_info.model_uri}")
    
    # Load the model using MLFlow 3
    loaded_model = mlflow.pyfunc.load_model(model_info.model_uri)
    
    # Test inference (this would normally connect to the actual game)
    test_input = {"action": "start_game", "headless": True}
    
    try:
        # Note: This will fail without proper environment setup, but demonstrates the API
        result = loaded_model.predict(test_input)
        logging.info(f"Model inference result: {result}")
    except Exception as e:
        logging.warning(f"Model inference failed (expected in this demo): {e}")
        logging.info("This is normal - the model requires game emulator setup")


def main():
    """Main function to demonstrate MLFlow 3 model logging."""
    
    setup_mlflow()
    
    logging.info("Starting MLFlow 3.0 model logging demonstration...")
    
    # Log both agent models
    logging.info("Logging DSPy agent model...")
    dspy_model_info = log_dspy_agent_model()
    
    logging.info("Logging OpenAI agent model...")
    openai_model_info = log_openai_agent_model()
    
    # Demonstrate model loading
    logging.info("Demonstrating model loading...")
    demonstrate_model_loading_and_inference(dspy_model_info)
    
    logging.info("MLFlow 3.0 model logging demonstration completed!")
    
    # Print summary
    print("\n" + "="*60)
    print("MLFlow 3.0 Model Logging Summary")
    print("="*60)
    print(f"DSPy Agent Model URI: {dspy_model_info.model_uri}")
    print(f"OpenAI Agent Model URI: {openai_model_info.model_uri}")
    print("\nKey MLFlow 3.0 Features Used:")
    print("- Models from Code logging with python_model parameter")
    print("- New 'name' parameter instead of 'artifact_path'")
    print("- Model artifacts stored under models/ instead of runs/")
    print("- Automatic signature inference from examples")
    print("- Enhanced metadata and tagging capabilities")


if __name__ == "__main__":
    main()