import logging
import os
from collections.abc import Callable
from datetime import datetime
from typing import NamedTuple

import click
import dspy
from dotenv import load_dotenv
from PIL import Image

import mlflow
from mlflow.entities import SpanType

from ..emulation.action_parser import ActionParser, ParsedAction
from ..emulation.game_emulator import GameEmulator
from ..game_state.memory_reader import PokemonRedMemoryReader
from .re_act import ReAct

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)


class GameState(NamedTuple):
    """Game state with comprehensive tile and memory data."""

    screen_base64: str
    context: str = ""
    comprehensive_data: dict | None = None
    game_analysis: dict | None = None


class ReActAgentSignature(dspy.Signature):
    """You are playing Pokemon Red on the Game Boy. Analyze the screenshot and press the appropriate buttons to progress in the game. Remember when moving, the first time you press a direction button, you'll just turn in that direction."""

    screen: dspy.Image = dspy.InputField()


class PokemonRedDSPyAgent(dspy.Module):
    """Main DSPy agent for playing Pokemon Red using ReAct."""

    def __init__(
        self,
        on_buttons_pressed: Callable[[str], Image.Image],
        on_step_complete: Callable[[int], None] | None = None,
    ):
        super().__init__()
        self.on_buttons_pressed = on_buttons_pressed
        self.react_agent = ReAct(
            ReActAgentSignature,
            tools=[self.press_buttons],
            max_iters=20,
        )
        self.action_parser = ActionParser()
        self.logger = logging.getLogger(__name__)
        self.screenshot_counter = 0
        self.on_step_complete = on_step_complete

    def forward(self, game_state: GameState) -> ParsedAction | None:
        """
        Forward method that utilizes comprehensive game data for better decisions.

        Args:
            game_state: Game state with tile and memory data

        Returns:
            Parsed action or None if failed
        """
        try:
            screen_image = dspy.Image(
                url=f"data:image/png;base64,{game_state.screen_base64}"
            )
            # Use the ReAct agent with comprehensive logging context
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

        # Call step completion callback if provided
        if self.on_step_complete:
            try:
                self.on_step_complete(self.screenshot_counter)
            except Exception as e:
                self.logger.warning(f"Step completion callback failed: {e}")

        return {
            "message": f"Successfully pressed buttons: {buttons}",
            "new_screenshot": dspy.Image.from_PIL(new_screenshot),
        }


class PokemonRedDSPyPlayer:
    def __init__(
        self,
        headless: bool = False,
        model: str = "openrouter/google/gemma-3-4b-it",
        max_steps: int = 100,
    ):
        self.logger = logging.getLogger(__name__)
        self.max_steps = max_steps
        self.current_step = 0

        # Set up DSPy language model
        mlflow.set_tag("llm_name", model)
        mlflow.set_tag("max_steps", max_steps)
        lm = dspy.LM(
            model=model,
            api_base="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            max_tokens=2_000,
            temperature=0.7,
        )
        dspy.configure(lm=lm)

        self.emulator = GameEmulator(headless=headless)
        self.memory_reader = PokemonRedMemoryReader(self.emulator.pyboy)
        self.agent = PokemonRedDSPyAgent(
            on_buttons_pressed=self.on_buttons_pressed,
            on_step_complete=self.on_step_complete,
        )
        self.action_parser = ActionParser()

    def on_buttons_pressed(self, buttons: str) -> Image.Image:
        """Callback method that gets called by the agent."""
        parsed_action = self.action_parser.parse_button_action(buttons)
        self.emulator.execute_action(parsed_action)
        return self.emulator.get_screen_image()

    def on_step_complete(self, step_counter: int) -> None:
        """
        Callback method called after each step completion for consolidated logging.

        Args:
            step_counter: Current step/screenshot counter
        """
        try:
            # Log comprehensive game state data every 5 steps
            if step_counter % 5 == 0:
                memory_view = self.emulator.pyboy.memory

                # Get all data in one optimized call
                consolidated_state = self.memory_reader.get_consolidated_game_state(
                    memory_view,
                    step_counter=step_counter,
                    timestamp=datetime.now().isoformat(),
                )

                # Convert to dict (automatically excludes event_flags)
                game_data = consolidated_state.to_dict()

                # Log the data
                mlflow.log_dict(game_data, f"game_state_step_{step_counter}.json")

                # Log key metrics for easier tracking
                mlflow.log_metrics(
                    {
                        "badges": consolidated_state.badges_obtained,
                        "party_count": consolidated_state.party_count,
                        "current_map": consolidated_state.current_map,
                        "is_in_battle": int(consolidated_state.is_in_battle),
                    }
                )

        except Exception as e:
            self.logger.warning(
                f"Consolidated logging failed at step {step_counter}: {e}"
            )

    @mlflow.trace(span_type=SpanType.AGENT)
    def start_game(self) -> None:
        try:
            self.emulator.load_state("init.state")

            while self.current_step < self.max_steps:
                # Get all game data using unified consolidated method
                memory_view = self.emulator.pyboy.memory
                consolidated_state = self.memory_reader.get_consolidated_game_state(
                    memory_view
                )

                screen_base64 = self.emulator.get_screen_base64()

                # Create game state with consolidated data
                game_state = GameState(
                    screen_base64=screen_base64,
                    context="You are playing Pokemon Red on the Game Boy. Progress through the game by exploring, catching Pokemon, battling trainers, and completing the main storyline.",
                    comprehensive_data=consolidated_state.to_dict(),
                    game_analysis=None,  # All data is now in comprehensive_data
                )

                parsed_action = self.agent.forward(game_state)
                success = self.emulator.execute_action(parsed_action)

                if not success:
                    self.logger.warning(
                        "Action parsing/execution failed, falling back to 'a' button"
                    )
                    self.emulator.fallback_action()

                self.current_step += 1

        except Exception as e:
            self.logger.error(f"Error starting game: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up resources."""
        self.emulator.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):  # noqa: ARG002
        self.cleanup()


@click.command()
@click.option("--steps", default=5, help="Maximum number of steps to run")
@click.option(
    "--model",
    default="openrouter/google/gemma-3-4b-it",
    help="Model to use for the agent",
)
@click.option("--headless", is_flag=True, help="Run in headless mode")
def main(steps: int, model: str, headless: bool):
    """Run the DSPy-based Pokemon Red player."""
    mlflow.dspy.autolog()  # type: ignore
    mlflow.set_tracking_uri("http://localhost:8080")
    mlflow.set_experiment("open-llms-play-pokemon")

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("pyboy").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)

    with (
        mlflow.start_run(),
        PokemonRedDSPyPlayer(headless=headless, model=model, max_steps=steps) as player,
    ):
        player.start_game()


if __name__ == "__main__":
    main()  # type: ignore
