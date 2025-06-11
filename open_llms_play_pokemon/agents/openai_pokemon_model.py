import logging
import os
from typing import Any, Dict

import mlflow
from dotenv import load_dotenv
from openai import OpenAI

from ..emulation.action_parser import ActionParser, ParsedAction
from ..emulation.game_emulator import GameEmulator

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
        return self.action_parser.parse_ai_response(response_text)


class PokemonRedOpenAIModel(mlflow.pyfunc.PythonModel):
    """MLFlow 3 compatible model wrapper for Pokemon Red OpenAI agent."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.emulator = None
        self.ai_agent = None
        
    def load_context(self, context):
        """Load model context and initialize components."""
        # Set model name - this could be made configurable
        model_name = "anthropic/claude-sonnet-4"
        mlflow.set_tag("llm_name", model_name)
        
        # Initialize AI agent
        self.ai_agent = OpenAIAgent(model_name=model_name)
        
        # Initialize emulator
        self.emulator = GameEmulator(headless=True)  # Default to headless for production

    def predict(self, context, model_input, params=None):
        """
        Predict method for MLFlow model interface.
        
        Args:
            context: MLFlow context (not used)
            model_input: Dictionary with 'action' key ('start_game' or 'step') 
                        and optional 'headless' boolean
            params: Additional parameters (not used)
            
        Returns:
            Dictionary with game state and action results
        """
        try:
            action = model_input.get("action", "start_game")
            headless = model_input.get("headless", True)
            
            # Reinitialize emulator if headless setting changed
            if self.emulator is None or self.emulator.headless != headless:
                if self.emulator:
                    self.emulator.cleanup()
                self.emulator = GameEmulator(headless=headless)
            
            if action == "start_game":
                return self._start_game()
            elif action == "step":
                return self._step()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Error in predict: {e}")
            return {"error": str(e)}
    
    def _start_game(self) -> Dict[str, Any]:
        """Start the Pokemon Red game and return initial state."""
        try:
            self.emulator.load_state("init.state")
            screen_base64 = self.emulator.get_screen_base64()
            
            # Get AI response
            response_text = self.ai_agent.run_step(screen_base64)
            
            # Parse and execute action
            parsed_action = self.ai_agent.parse_action(response_text)
            success = self.emulator.execute_action(parsed_action)
            
            if not success:
                self.logger.warning(
                    "Action parsing/execution failed, falling back to 'a' button"
                )
                self.emulator.fallback_action()
                
            return {
                "status": "success",
                "screen_base64": self.emulator.get_screen_base64(),
                "ai_response": response_text,
                "action_executed": str(parsed_action) if parsed_action else "fallback",
                "success": success
            }

        except Exception as e:
            self.logger.error(f"Error starting game: {e}")
            return {"error": str(e)}
    
    def _step(self) -> Dict[str, Any]:
        """Execute a single game step."""
        try:
            screen_base64 = self.emulator.get_screen_base64()
            
            # Get AI response
            response_text = self.ai_agent.run_step(screen_base64)
            
            # Parse and execute action
            parsed_action = self.ai_agent.parse_action(response_text)
            success = self.emulator.execute_action(parsed_action)
            
            if not success:
                self.logger.warning(
                    "Action parsing/execution failed, falling back to 'a' button"
                )
                self.emulator.fallback_action()
                
            return {
                "status": "success",
                "screen_base64": self.emulator.get_screen_base64(),
                "ai_response": response_text,
                "action_executed": str(parsed_action) if parsed_action else "fallback",
                "success": success
            }
            
        except Exception as e:
            self.logger.error(f"Error in step: {e}")
            return {"error": str(e)}


# MLFlow 3 requires this call to set the model for "Models from Code" logging
mlflow.models.set_model(PokemonRedOpenAIModel())