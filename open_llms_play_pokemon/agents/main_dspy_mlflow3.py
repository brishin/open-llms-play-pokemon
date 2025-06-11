"""
Updated Pokemon Red DSPy Agent with MLFlow 3.0 Integration

This script demonstrates the updated approach using MLFlow 3.0 features
including model logging and improved tracking capabilities.
"""

import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import dspy
import mlflow
from dotenv import load_dotenv
from mlflow.entities import SpanType
from mlflow.models import infer_signature
from PIL import Image

from ..emulation.action_parser import ActionParser, ParsedAction
from ..emulation.game_emulator import GameEmulator

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)


class GameState(NamedTuple):
    """Represents the current game state."""

    screen_base64: str
    context: str = ""


class ReActAgentSignature(dspy.Signature):
    """You are playing Pokemon Red on the Game Boy. Analyze the screenshot and press the appropriate buttons to progress in the game. Remember when moving, the first time you press a direction button, you'll just turn in that direction."""

    screen: dspy.Image = dspy.InputField(type_=dspy.Image)


class PokemonRedDSPyAgent(dspy.Module):
    """Main DSPy agent for playing Pokemon Red using ReAct."""

    def __init__(self, on_buttons_pressed: Callable[[str], Image.Image]):
        super().__init__()
        self.on_buttons_pressed = on_buttons_pressed
        self.react_agent = dspy.ReAct(
            ReActAgentSignature,
            tools=[self.press_buttons],
            max_iters=20,
        )
        self.action_parser = ActionParser()
        self.logger = logging.getLogger(__name__)
        self.screenshot_counter = 0

    def forward(self, game_state: GameState) -> ParsedAction | None:
        try:
            screen_image = dspy.Image(
                url=f"data:image/png;base64,{game_state.screen_base64}"
            )
            self.react_agent(
                screen=screen_image,
            )
        except Exception as e:
            self.logger.error(f"Error in DSPy ReAct agent forward pass: {e}")
            return None

    def press_buttons(self, sequence: str):
        """Press a sequence of buttons on the Game Boy controller.

        Args:
            sequence: Space-separated button sequence (e.g., "a b up down", "a", "right right"). Valid buttons: a, b, start, select, up, down, left, right. Prefer giving up to three buttons at a time.

        Returns:
            Confirmation message
        """
        buttons = sequence.lower().strip().split()
        if not buttons:
            return "Empty button sequence"

        valid_buttons = {"a", "b", "start", "select", "up", "down", "left", "right"}
        invalid_buttons = [btn for btn in buttons if btn.lower() not in valid_buttons]

        if invalid_buttons:
            return f"Invalid buttons found: {invalid_buttons}. Valid buttons: {valid_buttons}"

        new_screenshot = self.on_buttons_pressed(sequence)
        self.screenshot_counter += 1
        mlflow.log_image(new_screenshot, f"screenshot_{self.screenshot_counter}.png")
        return {
            "message": f"Successfully pressed buttons: {buttons}",
            "new_screenshot": dspy.Image.from_PIL(new_screenshot),
        }


class PokemonRedDSPyPlayer:
    def __init__(self, headless: bool = False):
        self.logger = logging.getLogger(__name__)

        # Set up DSPy language model
        model_name = "openrouter/google/gemini-2.5-pro-preview"
        mlflow.set_tag("llm_name", model_name)
        lm = dspy.LM(
            model=model_name,
            api_base="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            max_tokens=1_000,
            temperature=0.7,
        )
        dspy.configure(lm=lm)

        self.emulator = GameEmulator(headless=headless)
        self.agent = PokemonRedDSPyAgent(on_buttons_pressed=self.on_buttons_pressed)
        self.action_parser = ActionParser()

    def on_buttons_pressed(self, buttons: str) -> Image.Image:
        """Callback method that gets called by the agent."""
        parsed_action = self.action_parser.parse_button_action(buttons)
        self.emulator.execute_action(parsed_action)
        return self.emulator.get_screen_image()

    @mlflow.trace(span_type=SpanType.AGENT)
    def start_game(self) -> None:
        try:
            self.emulator.load_state("init.state")

            screen_base64 = self.emulator.get_screen_base64()
            game_state = GameState(
                screen_base64=screen_base64,
                context="You are playing Pokemon Red on the Game Boy. Progress through the game by exploring, catching Pokemon, battling trainers, and completing the main storyline.",
            )

            parsed_action = self.agent.forward(game_state)
            success = self.emulator.execute_action(parsed_action)

            if not success:
                self.logger.warning(
                    "Action parsing/execution failed, falling back to 'a' button"
                )
                self.emulator.fallback_action()

        except Exception as e:
            self.logger.error(f"Error starting game: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up resources."""
        self.emulator.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def log_model_mlflow3():
    """
    Log the DSPy agent model using MLFlow 3.0 features.
    
    This demonstrates the new Models from Code logging approach.
    """
    # Get the path to the model code file
    model_code_path = Path(__file__).parent / "dspy_pokemon_model.py"
    
    # Define input/output examples for signature inference
    input_example = {"action": "start_game", "headless": True}
    output_example = {
        "status": "success",
        "screen_base64": "base64_encoded_screenshot",
        "action_executed": "ParsedAction(...)",
        "success": True
    }
    
    # Infer signature from examples
    signature = infer_signature(input_example, output_example)
    
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
            "description": "DSPy-based ReAct agent for playing Pokemon Red",
            "mlflow_version": "3.0"
        }
    )
    
    # Log additional parameters and tags
    mlflow.log_param("agent_framework", "dspy")
    mlflow.log_param("model_type", "react_agent")
    mlflow.log_param("game_target", "pokemon_red")
    
    mlflow.set_tag("mlflow_version", "3.0")
    mlflow.set_tag("logging_method", "models_from_code")
    
    logging.info(f"Model logged successfully with URI: {model_info.model_uri}")
    return model_info


def demonstrate_model_loading(model_info):
    """Demonstrate loading and using the logged model."""
    logging.info("Demonstrating model loading from MLFlow 3...")
    
    # Load the model using MLFlow 3
    loaded_model = mlflow.pyfunc.load_model(model_info.model_uri)
    
    # The loaded model can now be used for inference
    logging.info(f"Model loaded successfully from: {model_info.model_uri}")
    logging.info(f"Model metadata: {loaded_model.metadata}")
    
    return loaded_model


def main():
    """Main function to run the DSPy-based Pokemon Red player with MLFlow 3."""
    
    # Set up MLFlow 3
    mlflow.set_tracking_uri("http://localhost:8080")
    mlflow.set_experiment("pokemon-agents-mlflow3")

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("pyboy").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)

    # Enable DSPy autologging (if available in MLFlow 3)
    try:
        mlflow.dspy.autolog()  # type: ignore
    except AttributeError:
        logging.warning("DSPy autologging not available in this MLFlow version")

    # Start the main run
    with mlflow.start_run(run_name="dspy-pokemon-gameplay"):
        
        # Log the model using MLFlow 3 approach
        logging.info("Logging model using MLFlow 3.0...")
        model_info = log_model_mlflow3()
        
        # Demonstrate model loading
        loaded_model = demonstrate_model_loading(model_info)
        
        # Run the actual game
        logging.info("Starting Pokemon Red gameplay...")
        with PokemonRedDSPyPlayer() as player:
            player.start_game()


if __name__ == "__main__":
    main()