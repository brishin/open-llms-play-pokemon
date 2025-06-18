import logging
from typing import NamedTuple


class ParsedAction(NamedTuple):
    """Represents a parsed action with button sequence."""

    button_sequence: list[str]
    sequence_str: str


class ActionParser:
    """Parser for button sequences."""

    VALID_BUTTONS = {"a", "b", "start", "select", "up", "down", "left", "right"}

    def __init__(self):
        """Initialize the action parser."""
        self.logger = logging.getLogger(__name__)

    def parse_button_action(self, sequence_str: str) -> ParsedAction | None:
        """
        Parse button sequence string directly.

        Args:
            sequence_str: Button sequence string like "a b"

        Returns:
            ParsedAction with button sequence or None if parsing fails
        """
        try:
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
            return ParsedAction(buttons, sequence_str)

        except Exception as e:
            self.logger.error(f"Error parsing button action: {e}")
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
