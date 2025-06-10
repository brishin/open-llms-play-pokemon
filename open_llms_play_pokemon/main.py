import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

from .action_parser import ActionParser, ParsedAction
from .game_emulator import GameEmulator

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)


class OpenAIAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.message_history = []
        self.action_parser = ActionParser()

        self.oai = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    def run_step(self, screen_base64: str) -> str:
        """Run a single step of AI decision making and return the response text."""
        prompt = """You are a GameBoy agent playing Pokemon Red. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
```
Thought: ...
Action: ...
```

## Action Space

buttons() # Press GameBoy buttons in sequence. Use space-separated button names from this exact list: 'a', 'b', 'start', 'select', 'up', 'down', 'left', 'right'. Only use these exact button names.
Examples: buttons('a'), buttons('up up a'), buttons('left b'), buttons('start down a')

## Note
- Use English in `Thought` part.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.

## User Instruction
Play Pokemon Red effectively. Progress through the game by exploring, catching Pokemon, battling trainers, and completing the main storyline. Make strategic decisions based on the current game state shown in the screenshot.

## Current Screenshot
The current game screen is provided as an image. Analyze what's happening on screen and choose the most appropriate next action."""

        messages = []
        recent_history = self.message_history[-10:]
        for msg in recent_history:
            if msg["role"] == "user":
                filtered_content = []
                for content_item in msg["content"]:
                    if content_item["type"] == "text":
                        filtered_content.append(content_item)
                filtered_msg = {"role": "user", "content": filtered_content}
                messages.append(filtered_msg)
            else:
                messages.append(msg)

        current_user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screen_base64}"},
                },
            ],
        }
        messages.append(current_user_message)

        print(f"messages: {messages}")
        completion = self.oai.chat.completions.create(
            model=self.model_name,
            max_completion_tokens=200,
            top_p=None,
            temperature=0.1,
            messages=messages,
        )

        response_text = completion.choices[0].message.content
        if not response_text:
            raise RuntimeError("No response text from AI", completion)

        self.message_history.append({"role": "assistant", "content": response_text})
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]

        return response_text

    def parse_action(self, response_text: str) -> ParsedAction | None:
        """Parse action from AI response and return parsed action or None."""
        # return self.action_parser.parse_ai_response(response_text)
        return None


class PokemonRedPlayer:
    def __init__(
        self,
        ai_agent: OpenAIAgent,
        headless: bool = False,
    ):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.emulator = GameEmulator(headless=headless)
        self.ai_agent = ai_agent

    def start_game(self) -> None:
        """Start the Pokemon Red game and get initial AI response."""
        try:
            self.emulator.load_state("init.state")

            while True:
                screen_base64 = self.emulator.get_screen_base64()
                response_text = self.ai_agent.run_step(screen_base64)
                print(response_text)

                parsed_action = self.ai_agent.parse_action(response_text)
                success = self.emulator.execute_action(parsed_action)
                if not success:
                    self.logger.warning(
                        "Action parsing/execution failed, falling back to 'a' button"
                    )
                    self.emulator.fallback_action()

        except Exception as e:
            print(f"Error starting game: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up resources."""
        self.emulator.cleanup()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()


def main():
    """Main function to run the Pokemon Red player."""
    ai_agent = OpenAIAgent(model_name="anthropic/claude-sonnet-4")
    with PokemonRedPlayer(ai_agent=ai_agent) as player:
        player.start_game()


if __name__ == "__main__":
    main()
