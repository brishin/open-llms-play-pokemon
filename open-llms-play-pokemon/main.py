import base64
import io
import os

from dotenv import load_dotenv
from openai import OpenAI
from pyboy import PyBoy

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)


class PokemonRedPlayer:
    def __init__(
        self,
        headless: bool = False,
        model_name: str = "ByteDance-Seed/UI-TARS-1.5-7B",
    ):
        self.game_dir = os.path.join(os.path.dirname(__file__), "..", "game")
        self.game_path = os.path.join(self.game_dir, "Pokemon Red.gb")
        self.symbols_path = os.path.join(self.game_dir, "pokered.sym")
        self.headless = headless
        self.model_name = model_name
        self.action_history = []

        self.oai = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            api_key=os.getenv("OPENAI_API_KEY"),
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
        prompt = """You are a GameBoy agent playing Pokemon Red. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
```
Thought: ...
Action: ...
```

## Action Space

buttons(sequence='') # Press GameBoy buttons in sequence. Use space-separated button names from this exact list: 'a', 'b', 'start', 'select', 'up', 'down', 'left', 'right'. Only use these exact button names. Examples: 'a', 'up up a', 'left b', 'start down a'

## Note
- Use English in `Thought` part.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.

## User Instruction
Play Pokemon Red effectively. Progress through the game by exploring, catching Pokemon, battling trainers, and completing the main storyline. Make strategic decisions based on the current game state shown in the screenshot.

## Current Screenshot
The current game screen is provided as an image. Analyze what's happening on screen and choose the most appropriate next action."""

        completion = self.oai.chat.completions.create(
            model=self.model_name,
            max_completion_tokens=200,
            top_p=None,
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screen_base64}"
                            },
                        },
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
                print(ai_response.choices[0].message.content)

                # For now, just add the response to action history without parsing
                self.action_history.append(ai_response.choices[0].message.content)

                # Temporary: press a random button to keep the game moving
                # This should be replaced with actual action parsing
                self.pyboy.button("a")
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
