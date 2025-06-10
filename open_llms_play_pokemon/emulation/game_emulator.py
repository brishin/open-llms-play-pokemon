import base64
import io
import logging
import os

from PIL import Image
from pyboy import PyBoy

from .action_parser import ParsedAction


class GameEmulator:
    """Game emulator wrapper for Pokemon Red using PyBoy."""

    def __init__(self, headless: bool = False):
        self.game_dir = os.path.join(os.path.dirname(__file__), "..", "game")
        self.game_path = os.path.join(self.game_dir, "Pokemon Red.gb")
        self.symbols_path = os.path.join(self.game_dir, "pokered.sym")
        self.headless = headless
        self.logger = logging.getLogger(__name__)

        self.pyboy = PyBoy(
            self.game_path,
            debug=False,
            no_input=False,
            window="null" if self.headless else "SDL2",
            log_level="CRITICAL",
            symbols=self.symbols_path,
            sound_emulated=False,
        )
        self.pyboy.set_emulation_speed(0)

    def load_state(self, state_name: str = "init.state") -> None:
        """Load a game state file."""
        with open(os.path.join(self.game_dir, state_name), "rb") as f:
            self.pyboy.load_state(f)

    def get_screen_image(self) -> Image.Image:
        """Get the current PyBoy screen as a PIL Image."""
        image = self.pyboy.screen.image
        if not isinstance(image, Image.Image):
            raise RuntimeError(f"Failed to capture screen: {image}")
        return image

    def get_screen_base64(self) -> str:
        """Capture the current PyBoy screen and return it as a base64 encoded string."""
        image = self.get_screen_image()

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return image_base64

    def execute_action(self, parsed_action: ParsedAction | None) -> bool:
        """Execute a parsed action on the emulator."""
        if parsed_action is None:
            self.logger.warning("No action given, skipping")
            return False

        if not parsed_action.button_sequence:
            return True

        try:
            for i, button in enumerate(parsed_action.button_sequence):
                if button not in {
                    "a",
                    "b",
                    "start",
                    "select",
                    "up",
                    "down",
                    "left",
                    "right",
                }:
                    continue

                self.pyboy.button(button)

                # Add ticks between buttons except for the last one
                if i < len(parsed_action.button_sequence) - 1:
                    self.pyboy.tick(60, render=True)

            # Final tick after button sequence
            self.pyboy.tick(60, render=True)
            return True

        except Exception as e:
            self.logger.exception("Error executing action", e)
            return False

    def fallback_action(self) -> None:
        """Execute fallback action when parsing fails."""
        self.pyboy.button("a")
        self.pyboy.tick(400, render=True)

    def cleanup(self) -> None:
        """Clean up resources."""
        self.pyboy.stop()
