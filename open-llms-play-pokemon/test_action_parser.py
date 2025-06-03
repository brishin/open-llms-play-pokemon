import unittest

from action_parser import ActionParser, ParsedAction


class MockPyBoy:
    """Mock PyBoy class for testing."""

    def __init__(self):
        self.button_presses = []
        self.tick_calls = []

    def button(self, btn):
        self.button_presses.append(btn)

    def tick(self, n, render=True):
        self.tick_calls.append((n, render))


class TestActionParser(unittest.TestCase):
    """Unit tests for ActionParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pyboy = MockPyBoy()
        self.parser = ActionParser(self.mock_pyboy)

    def test_parse_single_button(self):
        """Test parsing single button action."""
        response = 'Thought: I need to move up\nAction: buttons("up")'
        result = self.parser.parse_ai_response(response)

        self.assertIsNotNone(result)
        self.assertEqual(result.button_sequence, ["up"])
        self.assertEqual(result.raw_action, 'buttons("up")')

    def test_parse_multiple_buttons(self):
        """Test parsing multiple button sequence."""
        response = 'Thought: Move and press A\nAction: buttons("up up a")'
        result = self.parser.parse_ai_response(response)

        self.assertIsNotNone(result)
        self.assertEqual(result.button_sequence, ["up", "up", "a"])
        self.assertEqual(result.raw_action, 'buttons("up up a")')

    def test_parse_invalid_button(self):
        """Test parsing with invalid button names."""
        response = 'Thought: Invalid test\nAction: buttons("invalid_button")'
        result = self.parser.parse_ai_response(response)

        self.assertIsNone(result)

    def test_parse_mixed_valid_invalid(self):
        """Test parsing with mix of valid and invalid buttons."""
        response = (
            'Thought: Mixed valid/invalid\nAction: buttons("up invalid_button a")'
        )
        result = self.parser.parse_ai_response(response)

        self.assertIsNotNone(result)
        self.assertEqual(result.button_sequence, ["up", "a"])

    def test_parse_empty_sequence(self):
        """Test parsing empty button sequence."""
        response = 'Thought: Empty sequence\nAction: buttons("")'
        result = self.parser.parse_ai_response(response)

        self.assertIsNotNone(result)
        self.assertEqual(result.button_sequence, [])

    def test_parse_no_action_line(self):
        """Test parsing response with no action line."""
        response = "No action line in this response"
        result = self.parser.parse_ai_response(response)

        self.assertIsNone(result)

    def test_parse_invalid_format(self):
        """Test parsing response with invalid action format."""
        response = "Action: invalid_format()"
        result = self.parser.parse_ai_response(response)

        self.assertIsNone(result)

    def test_validate_button_sequence_valid(self):
        """Test validation of valid button sequence."""
        valid_sequence = ["up", "down", "a", "b"]
        self.assertTrue(self.parser.validate_button_sequence(valid_sequence))

    def test_validate_button_sequence_invalid(self):
        """Test validation of invalid button sequence."""
        invalid_sequence = ["up", "invalid", "a"]
        self.assertFalse(self.parser.validate_button_sequence(invalid_sequence))

    def test_execute_single_button(self):
        """Test execution of single button action."""
        action = ParsedAction(["a"], 'buttons("a")')
        result = self.parser.execute_action(action)

        self.assertTrue(result)
        self.assertEqual(self.mock_pyboy.button_presses, ["a"])
        self.assertEqual(len(self.mock_pyboy.tick_calls), 1)

    def test_execute_multiple_buttons(self):
        """Test execution of multiple button sequence."""
        action = ParsedAction(["up", "a"], 'buttons("up a")')
        result = self.parser.execute_action(action)

        self.assertTrue(result)
        self.assertEqual(self.mock_pyboy.button_presses, ["up", "a"])
        self.assertEqual(
            len(self.mock_pyboy.tick_calls), 2
        )  # One between buttons, one final

    def test_execute_empty_sequence(self):
        """Test execution of empty button sequence."""
        action = ParsedAction([], 'buttons("")')
        result = self.parser.execute_action(action)

        self.assertTrue(result)
        self.assertEqual(self.mock_pyboy.button_presses, [])
        self.assertEqual(len(self.mock_pyboy.tick_calls), 0)

    def test_extract_action_from_response(self):
        """Test extraction of action line from AI response."""
        response = 'Thought: Test\nAction: buttons("a")\nOther: stuff'
        action_line = self.parser.extract_action_from_response(response)

        self.assertEqual(action_line, 'buttons("a")')

    def test_extract_action_case_insensitive(self):
        """Test extraction is case insensitive."""
        response = 'Thought: Test\naction: buttons("a")'
        action_line = self.parser.extract_action_from_response(response)

        self.assertEqual(action_line, 'buttons("a")')

    def test_parse_and_execute_success(self):
        """Test complete parse and execute workflow."""
        response = 'Thought: Move up\nAction: buttons("up")'
        result = self.parser.parse_and_execute(response)

        self.assertTrue(result)
        self.assertEqual(self.mock_pyboy.button_presses, ["up"])

    def test_parse_and_execute_failure(self):
        """Test parse and execute with invalid response."""
        response = "No valid action here"
        result = self.parser.parse_and_execute(response)

        self.assertFalse(result)
        self.assertEqual(self.mock_pyboy.button_presses, [])


if __name__ == "__main__":
    unittest.main()
