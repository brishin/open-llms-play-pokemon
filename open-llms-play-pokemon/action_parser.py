import logging
import re
from typing import NamedTuple

from pyboy import PyBoy


class ParsedAction(NamedTuple):
    """Represents a parsed action with button sequence."""

    button_sequence: list[str]
    raw_action: str


class ActionParser:
    """Parser for AI-generated game actions with PyBoy integration."""

    VALID_BUTTONS = {"a", "b", "start", "select", "up", "down", "left", "right"}
    ACTION_PATTERN = re.compile(r"buttons\(['\"]([^'\"]*)['\"]", re.IGNORECASE)

    def __init__(self, pyboy: PyBoy, ticks_between_buttons: int = 60):
        """
        Initialize the action parser.

        Args:
            pyboy: PyBoy emulator instance
            ticks_between_buttons: Number of ticks to wait between button presses
        """
        self.pyboy = pyboy
        self.ticks_between_buttons = ticks_between_buttons
        self.logger = logging.getLogger(__name__)

    def extract_action_from_response(self, response: str) -> str | None:
        """
        Extract action line from AI response.

        Args:
            response: Full AI response containing Thought: and Action: sections

        Returns:
            Action line content or None if not found
        """
        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.lower().startswith("action:"):
                return line[7:].strip()  # Remove "Action:" prefix
        return None

    def parse_ai_response(self, response: str) -> ParsedAction | None:
        """
        Parse AI response and extract button sequence.

        Args:
            response: Full AI response text

        Returns:
            ParsedAction with button sequence or None if parsing fails
        """
        try:
            action_line = self.extract_action_from_response(response)
            if not action_line:
                self.logger.warning("No action line found in response")
                return None

            match = self.ACTION_PATTERN.search(action_line)
            if not match:
                self.logger.warning(f"No buttons() action found in: {action_line}")
                return None

            sequence_str = match.group(1).strip()
            if not sequence_str:
                self.logger.info("Empty button sequence")
                return ParsedAction([], action_line)

            # Split and validate button sequence
            buttons = [
                btn.strip().lower() for btn in sequence_str.split() if btn.strip()
            ]

            if not self.validate_button_sequence(buttons):
                invalid_buttons = [
                    btn for btn in buttons if btn not in self.VALID_BUTTONS
                ]
                self.logger.warning(
                    f"Invalid buttons found: {invalid_buttons}. Valid buttons: {self.VALID_BUTTONS}"
                )
                # Filter out invalid buttons
                buttons = [btn for btn in buttons if btn in self.VALID_BUTTONS]

                if not buttons:
                    self.logger.warning("No valid buttons remaining after filtering")
                    return None

            self.logger.info(f"Parsed button sequence: {buttons}")
            return ParsedAction(buttons, action_line)

        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return None

    def validate_button_sequence(self, sequence: list[str]) -> bool:
        """
        Validate that all buttons in sequence are valid.

        Args:
            sequence: List of button names

        Returns:
            True if all buttons are valid
        """
        return all(button in self.VALID_BUTTONS for button in sequence)

    def execute_action(self, parsed_action: ParsedAction) -> bool:
        """
        Execute a parsed action on the PyBoy emulator.

        Args:
            parsed_action: ParsedAction containing button sequence

        Returns:
            True if execution succeeded, False otherwise
        """
        if not parsed_action.button_sequence:
            self.logger.info("No buttons to execute")
            return True

        try:
            self.logger.info(
                f"Executing button sequence: {' '.join(parsed_action.button_sequence)}"
            )

            for i, button in enumerate(parsed_action.button_sequence):
                if button not in self.VALID_BUTTONS:
                    self.logger.warning(f"Skipping invalid button: {button}")
                    continue

                self.logger.debug(f"Pressing button: {button}")
                self.pyboy.button(button)

                # Add ticks between buttons except for the last one
                if i < len(parsed_action.button_sequence) - 1:
                    self.pyboy.tick(self.ticks_between_buttons, render=True)

            # Final tick after button sequence
            self.pyboy.tick(self.ticks_between_buttons, render=True)
            return True

        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            return False

    def parse_and_execute(self, response: str) -> bool:
        """
        Parse AI response and execute the action in one call.

        Args:
            response: Full AI response text

        Returns:
            True if parsing and execution succeeded, False otherwise
        """
        parsed_action = self.parse_ai_response(response)
        if parsed_action is None:
            self.logger.warning("Failed to parse action from response")
            return False

        return self.execute_action(parsed_action)
