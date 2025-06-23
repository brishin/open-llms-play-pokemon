#!/usr/bin/env python3
"""
Interactive Pokemon Red script using PyBoy in non-headless mode.
Saves the current state to a temp file when exiting.
"""

import logging
import signal
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import click
import sdl2
import sdl2.keyboard
import sdl2.scancode
from dotenv import load_dotenv

from open_llms_play_pokemon.emulation.game_emulator import GameEmulator
from open_llms_play_pokemon.game_state.memory_reader import PokemonRedMemoryReader

# Load environment variables
load_dotenv(Path(__file__).parent / ".env", override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InteractiveRunner:
    """Handles interactive Pokemon Red session with state saving."""

    def __init__(self, state_name: str = "init.state"):
        self.state_name = state_name
        self.emulator = None
        self.temp_state_file = None
        self.memory_reader = None
        self.step_counter = 0
        self.captures_dir = Path("captures")
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.cleanup()
        sys.exit(0)

    def save_capture(self):
        """Save screenshot and game state when a key is pressed."""
        if not self.emulator:
            return

        try:
            # Create captures directory if it doesn't exist
            self.captures_dir.mkdir(exist_ok=True)

            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save screenshot
            screenshot_path = self.captures_dir / f"screenshot_{timestamp}.png"
            screenshot = self.emulator.get_screen_image()
            screenshot.save(screenshot_path)

            # Save game state (.state file)
            gamestate_path = self.captures_dir / f"gamestate_{timestamp}.state"
            with open(gamestate_path, "wb") as f:
                self.emulator.pyboy.save_state(f)

            logger.info(
                f"Saved capture: {screenshot_path.name} and {gamestate_path.name}"
            )
            self.step_counter += 1

        except Exception as e:
            logger.error(f"Error saving capture: {e}")

    def start(self):
        """Start the interactive session."""
        logger.info("Starting interactive Pokemon Red session...")

        try:
            self.emulator = GameEmulator(headless=False)
            self.memory_reader = PokemonRedMemoryReader(self.emulator.pyboy)

            self.emulator.load_state(self.state_name)
            logger.info(f"Loaded state: {self.state_name}")

            self.temp_state_file = tempfile.NamedTemporaryFile(
                suffix=".state", delete=False, prefix="pokemon_red_"
            )
            self.temp_state_file.close()

            logger.info("=== INTERACTIVE MODE ===")
            logger.info("Use the game window to play Pokemon Red")
            logger.info("Press 'Q' key to save screenshot and game state")
            logger.info("Press Ctrl+C to exit and save state")
            logger.info("========================")

            # Keep the game running until interrupted
            q_key_was_pressed = False
            try:
                while True:
                    keyboard_state = sdl2.keyboard.SDL_GetKeyboardState(None)
                    q_key_pressed = keyboard_state[sdl2.scancode.SDL_SCANCODE_Q]
                    if q_key_pressed and not q_key_was_pressed:
                        logger.info("Q key pressed - saving capture")
                        self.save_capture()
                    q_key_was_pressed = q_key_pressed

                    self.emulator.pyboy.tick()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")

        except Exception as e:
            logger.error(f"Error during interactive session: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources and save state."""
        if self.emulator and self.temp_state_file:
            try:
                # Save current state
                with open(self.temp_state_file.name, "wb") as f:
                    self.emulator.pyboy.save_state(f)
                logger.info(f"State saved to: {self.temp_state_file.name}")
                print(f"\nState saved to: {self.temp_state_file.name}")

            except Exception as e:
                logger.error(f"Error saving state: {e}")

        if self.emulator:
            try:
                self.emulator.cleanup()
                logger.info("Emulator cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up emulator: {e}")


@click.command()
@click.option(
    "--state",
    default="init.state",
    help="Initial state file to load (default: init.state)",
)
def main(state: str):
    """Run Pokemon Red interactively and save state on exit."""
    runner = InteractiveRunner(state)

    try:
        runner.start()
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
