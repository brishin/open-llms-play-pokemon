import logging
import re
from typing import NamedTuple


class ParsedAction(NamedTuple):
    """Represents a parsed action with button sequence."""

    button_sequence: list[str]
    raw_action: str


class ActionParser:
    """Parser for AI-generated game actions."""

    VALID_BUTTONS = {"a", "b", "start", "select", "up", "down", "left", "right"}
    ACTION_PATTERN = re.compile(r"buttons\(['\"]([^'\"]*)['\"]", re.IGNORECASE)

    def __init__(self):
        """Initialize the action parser."""
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
