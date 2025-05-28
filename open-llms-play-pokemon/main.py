import base64
import io
import os

from dotenv import load_dotenv
from openai import OpenAI
from pyboy import PyBoy
from tools import ALL_GB_BUTTONS, tool_to_pyboy_button

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


class PokemonRedPlayer:
    def __init__(
        self,
        headless: bool = False,
        model_name: str = "ARPO_UITARS1.5_7B",
    ):
        self.game_dir = os.path.join(os.path.dirname(__file__), "..", "game")
        self.game_path = os.path.join(self.game_dir, "Pokemon Red.gb")
        self.symbols_path = os.path.join(self.game_dir, "pokered.sym")
        self.headless = headless
        self.model_name = model_name

        self.oai = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY")
        )
        self.pyboy = PyBoy(
            self.game_path,
            debug=False,
            no_input=False,
            window="null" if self.headless else "SDL2",
            log_level="CRITICAL",
            symbols=self.symbols_path,
            sound_emulated=False,
        )
        self.pyboy.set_emulation_speed(6)

    def _skip_intro(self) -> None:
        """Skip the game intro sequence."""
        self.pyboy.tick(2_000, render=False)
        self.pyboy.button("start")
        self.pyboy.tick(200, render=False)
        self.pyboy.button("start")
        self.pyboy.tick(6)

    def get_screen_base64(self) -> str:
        """
        Capture the current PyBoy screen and return it as a base64 encoded string.

        Returns:
            Base64 encoded PNG image of the current screen
        """
        if not self.pyboy:
            raise RuntimeError("PyBoy not initialized")

        image = self.pyboy.screen.image
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return image_base64

    def get_ai_response(self, screen_base64: str) -> str:
        completion = self.oai.chat.completions.create(
            model=self.model_name,
            tools=ALL_GB_BUTTONS,
            max_completion_tokens=100,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": "You are a game player playing Pokemon Red. Interact with the game using the provided tools to beat the game.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Here is the current game screen. What should I do next?",
                        },
                        # {
                        #     "type": "image_url",
                        #     "image_url": {
                        #         "url": f"data:image/png;base64,{screen_base64}"
                        #     },
                        # },
                    ],
                },
            ],
        )
        return completion

    def start_game(self) -> None:
        """Start the Pokemon Red game and get initial AI response."""
        try:
            self._skip_intro()

            while True:
                screen_base64 = self.get_screen_base64()
                ai_response = self.get_ai_response(screen_base64)
                print(ai_response.choices[0].message.tool_calls[0].function.name)
                self.pyboy.button(
                    tool_to_pyboy_button(
                        ai_response.choices[0].message.tool_calls[0].function.name
                    )
                )
                self.pyboy.tick(400, render=True)

        except Exception as e:
            print(f"Error starting game: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.pyboy:
            self.pyboy.stop()
            self.pyboy = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()


def main():
    """Main function to run the Pokemon Red player."""
    with PokemonRedPlayer() as player:
        player.start_game()


if __name__ == "__main__":
    main()
