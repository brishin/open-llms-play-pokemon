#!/usr/bin/env python3
"""
Interactive Pokemon Red script using PyBoy in non-headless mode.
Saves the current state to a temp file when exiting.
"""

import logging
import signal
import sys
import tempfile
from pathlib import Path

import click
from dotenv import load_dotenv

from open_llms_play_pokemon.emulation.game_emulator import GameEmulator

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

    def start(self):
        """Start the interactive session."""
        logger.info("Starting interactive Pokemon Red session...")

        try:
            # Initialize emulator in non-headless mode
            self.emulator = GameEmulator(headless=False)
            logger.info("Game emulator initialized")

            # Load initial state
            self.emulator.load_state(self.state_name)
            logger.info(f"Loaded state: {self.state_name}")

            # Create temp file for saving state
            self.temp_state_file = tempfile.NamedTemporaryFile(
                suffix=".state", delete=False, prefix="pokemon_red_"
            )
            self.temp_state_file.close()

            logger.info("=== INTERACTIVE MODE ===")
            logger.info("Use the game window to play Pokemon Red")
            logger.info("Press Ctrl+C to exit and save state")
            logger.info("========================")

            # Keep the game running until interrupted
            try:
                while True:
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
