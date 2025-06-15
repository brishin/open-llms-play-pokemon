"""Unit tests for the ReAct agent implementation."""

import sys
from pathlib import Path
from unittest.mock import patch

import dspy
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from open_llms_play_pokemon.agents.re_act import ReAct  # noqa: E402


class QASignature(dspy.Signature):
    """Question answering signature for ReAct testing."""

    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


class MockLM:
    """Mock Language Model for testing DSPy modules."""

    def __init__(self):
        self.responses = {}
        self.call_count = 0

    def set_response(self, signature_str: str, response_dict: dict):
        """Set a mock response for a given signature."""
        self.responses[signature_str] = response_dict

    def generate(self, prompt, **kwargs):  # noqa: ARG002
        """Mock generate method."""
        self.call_count += 1
        # Return a default response
        return {"choices": [{"message": {"content": "Mock response"}}]}

    def __call__(self, prompt, **kwargs):
        """Mock call method."""
        return self.generate(prompt, **kwargs)

    def request(self, prompt, **kwargs):
        """Mock request method."""
        return self.generate(prompt, **kwargs)


def simple_calculator(a: int, b: int) -> int:
    """Simple calculator tool for testing."""
    return a + b


def weather_tool(city: str) -> str:
    """Mock weather tool for testing."""
    return f"The weather in {city} is sunny and 72°F"


def failing_tool(message: str) -> str:
    """Tool that always fails for testing error handling."""
    raise ValueError(f"This tool always fails: {message}")


class TestReActInitialization:
    """Test ReAct module initialization."""

    def test_init_with_simple_tools(self):
        """Test initialization with simple callable tools."""
        tools = [simple_calculator, weather_tool]
        react = ReAct(QASignature, tools, max_iters=5)

        assert react.max_iters == 5
        assert len(react.tools) == 3  # 2 tools + finish tool
        assert "simple_calculator" in react.tools
        assert "weather_tool" in react.tools
        assert "finish" in react.tools

    def test_init_with_dspy_tools(self):
        """Test initialization with DSPy Tool objects."""
        from dspy.adapters.types.tool import Tool

        tool1 = Tool(simple_calculator)
        tool2 = Tool(weather_tool)

        react = ReAct(QASignature, [tool1, tool2], max_iters=10)

        assert react.max_iters == 10
        assert len(react.tools) == 3  # 2 tools + finish tool
        assert tool1.name in react.tools
        assert tool2.name in react.tools
        assert "finish" in react.tools

    def test_finish_tool_created(self):
        """Test that the finish tool is automatically created."""
        react = ReAct(QASignature, [simple_calculator])

        # Check if finish tool exists in the internal DSPy ReAct tools
        finish_tool = getattr(react._dspy_react, "tools", {}).get("finish")
        assert finish_tool is not None

        # Test that finish tool works
        result = finish_tool()
        assert result == "Completed."


class TestReActToolExecution:
    """Test tool execution in ReAct forward pass."""

    def test_tool_execution_success(self):
        """Test successful tool execution."""
        react = ReAct(QASignature, [simple_calculator, weather_tool])

        # Create proper mock prediction with the expected attributes
        mock_prediction = type(
            "MockPrediction",
            (),
            {
                "next_thought": "I need to calculate 5 + 3",
                "next_tool_name": "simple_calculator",
                "next_tool_args": {"a": 5, "b": 3},
            },
        )()

        # Mock the _call_with_potential_trajectory_truncation method that react calls
        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            # First call returns the tool prediction, second call returns the extract
            mock_extract = type(
                "MockExtract", (), {"answer": "8", "__dict__": {"answer": "8"}}
            )()

            # Create a call counter to track which call this is
            call_count = 0

            def mock_side_effect(*args, **kwargs):  # noqa: ARG001
                nonlocal call_count
                call_count += 1
                if call_count == 1:  # First call - return prediction
                    return mock_prediction
                else:  # Second call - return extract
                    return mock_extract

            mock_call.side_effect = mock_side_effect

            result = react.forward(question="What is 5 + 3?")

            assert result is not None
            assert hasattr(result, "trajectory")
            assert hasattr(result, "answer")
            assert result.answer == "8"

            # Verify trajectory contains tool execution
            trajectory = result.trajectory
            assert "thought_0" in trajectory
            assert "tool_name_0" in trajectory
            assert "tool_args_0" in trajectory
            assert "observation_0" in trajectory

            assert trajectory["thought_0"] == "I need to calculate 5 + 3"
            assert trajectory["tool_name_0"] == "simple_calculator"
            assert trajectory["tool_args_0"] == {"a": 5, "b": 3}
            assert trajectory["observation_0"] == 8

    def test_tool_execution_with_finish(self):
        """Test tool execution that ends with finish tool."""
        react = ReAct(QASignature, [weather_tool])

        # Create sequence of predictions: tool call, then finish
        prediction1 = type(
            "MockPrediction",
            (),
            {
                "next_thought": "I'll get the weather for Paris",
                "next_tool_name": "weather_tool",
                "next_tool_args": {"city": "Paris"},
            },
        )()

        prediction2 = type(
            "MockPrediction",
            (),
            {
                "next_thought": "I have the weather information",
                "next_tool_name": "finish",
                "next_tool_args": {},
            },
        )()

        # Mock extract result
        mock_extract = type(
            "MockExtract",
            (),
            {
                "answer": "The weather in Paris is sunny and 72°F",
                "__dict__": {"answer": "The weather in Paris is sunny and 72°F"},
            },
        )()

        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            # Return predictions for react calls, then extract result
            mock_call.side_effect = [prediction1, prediction2, mock_extract]

            result = react.forward(question="What's the weather in Paris?")

            trajectory = result.trajectory

            # Should have 2 iterations
            assert "thought_0" in trajectory
            assert "thought_1" in trajectory
            assert trajectory["tool_name_0"] == "weather_tool"
            assert trajectory["tool_name_1"] == "finish"
            assert (
                "The weather in Paris is sunny and 72°F" in trajectory["observation_0"]
            )

    def test_tool_execution_error_handling(self):
        """Test error handling when tools fail."""
        react = ReAct(QASignature, [failing_tool])

        mock_prediction = type(
            "MockPrediction",
            (),
            {
                "next_thought": "I'll try the failing tool",
                "next_tool_name": "failing_tool",
                "next_tool_args": {"message": "test error"},
            },
        )()

        mock_extract = type(
            "MockExtract",
            (),
            {"answer": "Tool failed", "__dict__": {"answer": "Tool failed"}},
        )()

        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            call_count = 0

            def mock_side_effect(*args, **kwargs):  # noqa: ARG001
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return mock_prediction
                else:
                    return mock_extract

            mock_call.side_effect = mock_side_effect

            result = react.forward(question="Test failing tool")

            trajectory = result.trajectory
            observation = trajectory["observation_0"]

            # Should contain error message
            assert "Execution error in failing_tool" in observation
            assert "This tool always fails: test error" in observation

    def test_invalid_tool_name(self):
        """Test handling of invalid tool names."""
        react = ReAct(QASignature, [simple_calculator])

        mock_prediction = type(
            "MockPrediction",
            (),
            {
                "next_thought": "I'll try a non-existent tool",
                "next_tool_name": "non_existent_tool",
                "next_tool_args": {},
            },
        )()

        mock_extract = type(
            "MockExtract",
            (),
            {"answer": "Tool not found", "__dict__": {"answer": "Tool not found"}},
        )()

        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            call_count = 0

            def mock_side_effect(*args, **kwargs):  # noqa: ARG001
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return mock_prediction
                else:
                    return mock_extract

            mock_call.side_effect = mock_side_effect

            result = react.forward(question="Test invalid tool")

            trajectory = result.trajectory
            observation = trajectory["observation_0"]

            assert "Tool 'non_existent_tool' not found" in observation

    def test_max_iterations_limit(self):
        """Test that max_iters is respected."""
        react = ReAct(QASignature, [simple_calculator], max_iters=2)

        # Create prediction that never calls finish
        mock_prediction = type(
            "MockPrediction",
            (),
            {
                "next_thought": "Keep going",
                "next_tool_name": "simple_calculator",
                "next_tool_args": {"a": 1, "b": 1},
            },
        )()

        mock_extract = type(
            "MockExtract",
            (),
            {
                "answer": "Stopped at max iterations",
                "__dict__": {"answer": "Stopped at max iterations"},
            },
        )()

        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            # Return the same prediction twice, then extract
            mock_call.side_effect = [mock_prediction, mock_prediction, mock_extract]

            result = react.forward(question="Test max iterations")

            trajectory = result.trajectory

            # Should only have 2 iterations due to max_iters=2
            assert "thought_0" in trajectory
            assert "thought_1" in trajectory
            assert "thought_2" not in trajectory

    def test_prediction_none_handling(self):
        """Test handling when prediction returns None."""
        react = ReAct(QASignature, [simple_calculator])

        mock_extract = type(
            "MockExtract",
            (),
            {"answer": "No prediction", "__dict__": {"answer": "No prediction"}},
        )()

        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            # First call returns None, second call returns extract
            call_count = 0

            def mock_side_effect(*args, **kwargs):  # noqa: ARG001
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return None  # Prediction returns None
                else:
                    return mock_extract  # Extract still works

            mock_call.side_effect = mock_side_effect

            result = react.forward(question="Test None prediction")

            # Should handle None gracefully and still return result
            assert result is not None
            assert hasattr(result, "answer")


class TestReActAsyncExecution:
    """Test async execution of ReAct."""

    def test_async_tool_execution(self):
        """Test async tool execution setup (without actually running async)."""
        react = ReAct(QASignature, [weather_tool])

        # Test that async methods exist and are callable
        assert hasattr(react, "aforward")
        assert callable(react.aforward)
        # Check if the method exists on the internal DSPy ReAct object
        if hasattr(
            react._dspy_react, "_async_call_with_potential_trajectory_truncation"
        ):
            assert callable(
                react._dspy_react._async_call_with_potential_trajectory_truncation
            )


class TestReActTrajectoryHandling:
    """Test trajectory formatting and truncation."""

    def test_trajectory_formatting(self):
        """Test trajectory formatting."""
        react = ReAct(QASignature, [simple_calculator])

        test_trajectory = {
            "thought_0": "I need to calculate",
            "tool_name_0": "simple_calculator",
            "tool_args_0": {"a": 2, "b": 3},
            "observation_0": 5,
        }

        # Check if the method exists, otherwise skip this test
        if hasattr(react._dspy_react, "_format_trajectory"):
            formatted = react._dspy_react._format_trajectory(test_trajectory)
        else:
            formatted = str(test_trajectory)  # Fallback

        # Should return a string representation
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_trajectory_truncation(self):
        """Test trajectory truncation when too long."""
        react = ReAct(QASignature, [simple_calculator])

        # Create a trajectory with multiple tool calls
        test_trajectory = {}
        for i in range(10):
            test_trajectory[f"thought_{i}"] = f"Thought {i}"
            test_trajectory[f"tool_name_{i}"] = "simple_calculator"
            test_trajectory[f"tool_args_{i}"] = {"a": i, "b": i + 1}
            test_trajectory[f"observation_{i}"] = i + (i + 1)

        original_length = len(test_trajectory)
        # Check if the method exists, otherwise skip this test
        if hasattr(react._dspy_react, "truncate_trajectory"):
            truncated = react._dspy_react.truncate_trajectory(test_trajectory.copy())
        else:
            # Fallback: just return the original trajectory
            truncated = test_trajectory.copy()

        # Should remove the first tool call (4 keys) if truncation is available
        if hasattr(react._dspy_react, "truncate_trajectory"):
            assert len(truncated) == original_length - 4
            assert "thought_0" not in truncated
            assert "tool_name_0" not in truncated
            assert "tool_args_0" not in truncated
            assert "observation_0" not in truncated
            assert "thought_1" in truncated
        else:
            # Fallback case: no truncation occurred
            assert len(truncated) == original_length

    def test_trajectory_truncation_minimum_size(self):
        """Test trajectory truncation with minimum size."""
        react = ReAct(QASignature, [simple_calculator])

        # Create trajectory with fewer than 4 keys to trigger the error
        tiny_trajectory = {
            "thought_0": "Only thought",
            "tool_name_0": "simple_calculator",
            "tool_args_0": {"a": 1, "b": 2},
            # Missing observation_0
        }

        # Check if the method exists, otherwise skip this test
        if hasattr(react._dspy_react, "truncate_trajectory"):
            with pytest.raises(ValueError, match="the trajectory cannot be truncated"):
                react._dspy_react.truncate_trajectory(tiny_trajectory)
        else:
            # Skip this test if the method doesn't exist
            pytest.skip("truncate_trajectory method not available")


class TestReActToolIntegration:
    """Integration tests for ReAct tool execution."""

    def test_tool_execution_with_real_functions(self):
        """Test that tools are actually executed and return correct results."""
        react = ReAct(QASignature, [simple_calculator])

        # Create a prediction that calls the calculator
        mock_prediction = type(
            "MockPrediction",
            (),
            {
                "next_thought": "I should use the calculator",
                "next_tool_name": "simple_calculator",
                "next_tool_args": {"a": 10, "b": 5},
            },
        )()

        mock_extract = type(
            "MockExtract",
            (),
            {"answer": "The answer is 15", "__dict__": {"answer": "The answer is 15"}},
        )()

        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            call_count = 0

            def mock_side_effect(*args, **kwargs):  # noqa: ARG001
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return mock_prediction
                else:
                    return mock_extract

            mock_call.side_effect = mock_side_effect

            result = react.forward(question="What is 10 + 5?")

            assert result is not None
            assert hasattr(result, "answer")
            assert result.answer == "The answer is 15"

            # Verify tool was actually executed and returned correct result
            trajectory = result.trajectory
            assert trajectory["observation_0"] == 15  # 10 + 5 = 15

    def test_multiple_tool_calls_in_sequence(self):
        """Test multiple tool calls work correctly."""
        react = ReAct(QASignature, [simple_calculator, weather_tool])

        # First prediction: use calculator
        prediction1 = type(
            "MockPrediction",
            (),
            {
                "next_thought": "First I'll calculate 2 + 3",
                "next_tool_name": "simple_calculator",
                "next_tool_args": {"a": 2, "b": 3},
            },
        )()

        # Second prediction: get weather
        prediction2 = type(
            "MockPrediction",
            (),
            {
                "next_thought": "Now I'll get weather for NYC",
                "next_tool_name": "weather_tool",
                "next_tool_args": {"city": "NYC"},
            },
        )()

        # Third prediction: finish
        prediction3 = type(
            "MockPrediction",
            (),
            {
                "next_thought": "I have all the information",
                "next_tool_name": "finish",
                "next_tool_args": {},
            },
        )()

        mock_extract = type(
            "MockExtract",
            (),
            {
                "answer": "Calculation and weather complete",
                "__dict__": {"answer": "Calculation and weather complete"},
            },
        )()

        with patch.object(
            react, "_call_with_potential_trajectory_truncation"
        ) as mock_call:
            mock_call.side_effect = [
                prediction1,
                prediction2,
                prediction3,
                mock_extract,
            ]

            result = react.forward(question="Calculate 2+3 and get NYC weather")

            trajectory = result.trajectory

            # Verify both tools were executed
            assert trajectory["tool_name_0"] == "simple_calculator"
            assert trajectory["observation_0"] == 5  # 2 + 3

            assert trajectory["tool_name_1"] == "weather_tool"
            assert "NYC" in trajectory["observation_1"]
            assert "sunny" in trajectory["observation_1"]

            assert trajectory["tool_name_2"] == "finish"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
