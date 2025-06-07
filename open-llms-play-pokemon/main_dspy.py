import logging
import os
from collections.abc import Callable
from typing import NamedTuple

import dspy
import mlflow
from dotenv import load_dotenv
from mlflow.entities import SpanType
from PIL import Image

from .action_parser import ActionParser, ParsedAction
from .game_emulator import GameEmulator

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
            sequence: Space-separated button sequence (e.g., "a b up down", "a", "right right"). Valid buttons: a, b, start, select, up, down, left, right.

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
            "new_screenshot": new_screenshot,
        }


class PokemonRedDSPyPlayer:
    def __init__(self, headless: bool = False):
        self.logger = logging.getLogger(__name__)

        # Set up DSPy language model
        lm = dspy.LM(
            model="openrouter/google/gemini-2.5-pro-preview",
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


def main():
    mlflow.dspy.autolog()  # type: ignore
    mlflow.set_tracking_uri("http://localhost:8080")
    mlflow.set_experiment("open-llms-play-pokemon")

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("pyboy").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)

    """Main function to run the DSPy-based Pokemon Red player."""
    with PokemonRedDSPyPlayer() as player:
        player.start_game()


if __name__ == "__main__":
    main()
