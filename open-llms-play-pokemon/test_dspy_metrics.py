"""
Test script for DSPy metrics implementation.

This script provides unit tests and integration tests for the DSPy metrics
to ensure they work correctly with the Pokemon Red evaluation system.
"""

import pytest
from unittest.mock import Mock, patch
import dspy

from dspy_metrics import (
    GameplayExample,
    GameplayPrediction,
    action_exact_match,
    buttons_exact_match,
    buttons_partial_match,
    gameplay_effectiveness_metric,
    game_progress_metric,
    create_pokemon_evaluator,
    validate_reasoning_steps,
)


class TestBasicMetrics:
    """Test basic DSPy metrics functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.example = GameplayExample(
            screen_base64="test_base64",
            context="Player is in Pallet Town",
            expected_action="Move up to Professor Oak's lab",
            expected_buttons=["up", "a"],
            game_progress_indicators={
                "current_location": "pallet_town",
                "pokemon_health": 1.0,
                "has_pokeballs": False
            }
        )
        
        self.correct_prediction = GameplayPrediction(
            action="Move up to Professor Oak's lab",
            buttons=["up", "a"],
            reasoning="Need to visit Professor Oak to start the journey",
            confidence=0.9
        )
        
        self.incorrect_prediction = GameplayPrediction(
            action="Go to the Pokemon Center",
            buttons=["down", "left"],
            reasoning="Need to heal Pokemon",
            confidence=0.7
        )
    
    def test_action_exact_match_correct(self):
        """Test action exact match with correct prediction."""
        result = action_exact_match(self.example, self.correct_prediction)
        assert result is True
    
    def test_action_exact_match_incorrect(self):
        """Test action exact match with incorrect prediction."""
        result = action_exact_match(self.example, self.incorrect_prediction)
        assert result is False
    
    def test_action_exact_match_case_insensitive(self):
        """Test action exact match is case insensitive."""
        prediction = GameplayPrediction(
            action="MOVE UP TO PROFESSOR OAK'S LAB",
            buttons=["up", "a"]
        )
        result = action_exact_match(self.example, prediction)
        assert result is True
    
    def test_buttons_exact_match_correct(self):
        """Test button exact match with correct prediction."""
        result = buttons_exact_match(self.example, self.correct_prediction)
        assert result is True
    
    def test_buttons_exact_match_incorrect(self):
        """Test button exact match with incorrect prediction."""
        result = buttons_exact_match(self.example, self.incorrect_prediction)
        assert result is False
    
    def test_buttons_partial_match_full(self):
        """Test partial match with full overlap."""
        result = buttons_partial_match(self.example, self.correct_prediction)
        assert result == 1.0
    
    def test_buttons_partial_match_partial(self):
        """Test partial match with partial overlap."""
        prediction = GameplayPrediction(
            action="Some action",
            buttons=["up", "b"]  # One correct, one incorrect
        )
        result = buttons_partial_match(self.example, prediction)
        assert result == 0.5  # 1 out of 2 buttons match
    
    def test_buttons_partial_match_none(self):
        """Test partial match with no overlap."""
        result = buttons_partial_match(self.example, self.incorrect_prediction)
        assert result == 0.0


class TestComplexMetrics:
    """Test complex multi-criteria metrics."""
    
    def setup_method(self):
        """Set up test data."""
        self.example = GameplayExample(
            screen_base64="test_base64",
            context="Player is in battle with a wild Pidgey",
            expected_action="Use Tackle attack",
            expected_buttons=["a"],
            game_progress_indicators={
                "current_location": "battle",
                "pokemon_health": 0.8,
                "in_battle": True
            }
        )
    
    def test_gameplay_effectiveness_good_prediction(self):
        """Test gameplay effectiveness with good prediction."""
        prediction = GameplayPrediction(
            action="Use Tackle to battle the wild Pidgey",
            buttons=["a"],
            reasoning="Tackle is effective against normal-type Pokemon and will help gain experience points for our starter Pokemon",
            confidence=0.8
        )
        
        result = gameplay_effectiveness_metric(self.example, prediction)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
        assert result > 0.5  # Should be reasonably good
    
    def test_gameplay_effectiveness_poor_prediction(self):
        """Test gameplay effectiveness with poor prediction."""
        prediction = GameplayPrediction(
            action="Invalid action",
            buttons=["invalid_button"],
            reasoning="Short",  # Too short reasoning
            confidence=0.1
        )
        
        result = gameplay_effectiveness_metric(self.example, prediction)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
        assert result < 0.5  # Should be poor
    
    def test_gameplay_effectiveness_trace_mode(self):
        """Test gameplay effectiveness in trace mode (optimization)."""
        prediction = GameplayPrediction(
            action="Use Tackle to battle the wild Pidgey",
            buttons=["a"],
            reasoning="Tackle is effective against normal-type Pokemon and will help gain experience",
            confidence=0.8
        )
        
        # In trace mode, should return boolean
        result = gameplay_effectiveness_metric(self.example, prediction, trace={})
        assert isinstance(result, bool)
    
    def test_game_progress_metric_location_based(self):
        """Test game progress metric with location-based decisions."""
        # Pallet Town scenario
        example = GameplayExample(
            screen_base64="test",
            context="In Pallet Town",
            game_progress_indicators={"current_location": "pallet_town"}
        )
        
        prediction = GameplayPrediction(
            action="Explore the town",
            buttons=["up"]  # Valid movement for Pallet Town
        )
        
        result = game_progress_metric(example, prediction)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
    
    def test_game_progress_metric_health_based(self):
        """Test game progress metric with health-based decisions."""
        example = GameplayExample(
            screen_base64="test",
            context="Pokemon has low health",
            game_progress_indicators={
                "pokemon_health": 0.2,  # Low health
                "current_location": "route_1"
            }
        )
        
        prediction = GameplayPrediction(
            action="Go to Pokemon Center to heal",
            buttons=["left"]
        )
        
        result = game_progress_metric(example, prediction)
        assert isinstance(result, float)
        assert result > 0.5  # Should recognize good health management


class TestDataStructures:
    """Test data structure validation and functionality."""
    
    def test_gameplay_example_creation(self):
        """Test GameplayExample creation and attributes."""
        example = GameplayExample(
            screen_base64="test_base64",
            context="Test context",
            expected_action="Test action",
            expected_buttons=["a", "b"],
            game_progress_indicators={"test": "value"},
            success_criteria={"success": True}
        )
        
        assert example.screen_base64 == "test_base64"
        assert example.context == "Test context"
        assert example.expected_action == "Test action"
        assert example.expected_buttons == ["a", "b"]
        assert example.game_progress_indicators == {"test": "value"}
        assert example.success_criteria == {"success": True}
    
    def test_gameplay_prediction_creation(self):
        """Test GameplayPrediction creation and attributes."""
        prediction = GameplayPrediction(
            action="Test action",
            buttons=["a", "b"],
            reasoning="Test reasoning",
            confidence=0.8
        )
        
        assert prediction.action == "Test action"
        assert prediction.buttons == ["a", "b"]
        assert prediction.reasoning == "Test reasoning"
        assert prediction.confidence == 0.8


class TestEvaluatorCreation:
    """Test evaluator creation and configuration."""
    
    def test_create_pokemon_evaluator_basic(self):
        """Test basic evaluator creation."""
        dataset = [
            GameplayExample(
                screen_base64="test",
                context="test context",
                expected_action="test action",
                expected_buttons=["a"]
            )
        ]
        
        evaluator = create_pokemon_evaluator(
            devset=dataset,
            metric_name="gameplay_effectiveness"
        )
        
        assert isinstance(evaluator, type(dspy.evaluate.Evaluate))
    
    def test_create_pokemon_evaluator_invalid_metric(self):
        """Test evaluator creation with invalid metric name."""
        dataset = [
            GameplayExample(
                screen_base64="test",
                context="test context"
            )
        ]
        
        with pytest.raises(ValueError, match="Unknown metric"):
            create_pokemon_evaluator(
                devset=dataset,
                metric_name="invalid_metric_name"
            )
    
    def test_create_pokemon_evaluator_all_metrics(self):
        """Test that all advertised metrics can be created."""
        dataset = [
            GameplayExample(
                screen_base64="test",
                context="test context",
                expected_action="test action",
                expected_buttons=["a"]
            )
        ]
        
        valid_metrics = [
            "action_exact_match",
            "buttons_exact_match",
            "buttons_partial_match",
            "gameplay_effectiveness",
            "game_progress",
            "reasoning_validation"
        ]
        
        for metric_name in valid_metrics:
            evaluator = create_pokemon_evaluator(
                devset=dataset,
                metric_name=metric_name
            )
            assert evaluator is not None


class TestTraceBasedMetrics:
    """Test trace-based metrics for optimization."""
    
    def test_validate_reasoning_steps_no_trace(self):
        """Test reasoning validation without trace (should return True)."""
        example = GameplayExample(
            screen_base64="test",
            context="test context"
        )
        
        prediction = GameplayPrediction(
            action="test action",
            buttons=["a"]
        )
        
        result = validate_reasoning_steps(example, prediction, trace=None)
        assert result is True
    
    def test_validate_reasoning_steps_with_trace(self):
        """Test reasoning validation with mock trace."""
        example = GameplayExample(
            screen_base64="test",
            context="test context"
        )
        
        prediction = GameplayPrediction(
            action="test action",
            buttons=["a"]
        )
        
        # Mock trace with reasoning steps
        mock_step = Mock()
        mock_step.outputs = {
            'reasoning': 'This is a good Pokemon battle strategy that involves catching wild Pokemon in the tall grass'
        }
        
        trace = [mock_step]
        
        result = validate_reasoning_steps(example, prediction, trace=trace)
        assert isinstance(result, bool)


class TestIntegration:
    """Test integration with existing systems."""
    
    @patch('dspy.LM')
    def test_mock_llm_integration(self, mock_lm):
        """Test that metrics work with mocked LLM."""
        # This test ensures metrics don't break when LLM is unavailable
        example = GameplayExample(
            screen_base64="test",
            context="test context",
            expected_action="test action",
            expected_buttons=["a"]
        )
        
        prediction = GameplayPrediction(
            action="test action",
            buttons=["a"],
            reasoning="test reasoning"
        )
        
        # Test metrics that don't require LLM
        assert action_exact_match(example, prediction) is True
        assert buttons_exact_match(example, prediction) is True
        assert isinstance(gameplay_effectiveness_metric(example, prediction), float)
        assert isinstance(game_progress_metric(example, prediction), float)


def run_basic_functionality_test():
    """Run a basic functionality test without pytest."""
    print("Running basic DSPy metrics functionality test...")
    
    # Create test data
    example = GameplayExample(
        screen_base64="test_base64",
        context="Player is in Pallet Town and needs to visit Professor Oak's lab",
        expected_action="Move up to enter Professor Oak's lab",
        expected_buttons=["up", "a"],
        game_progress_indicators={
            "current_location": "pallet_town",
            "pokemon_health": 1.0,
            "has_pokeballs": False
        }
    )
    
    prediction = GameplayPrediction(
        action="Move up to enter Professor Oak's lab",
        buttons=["up", "a"],
        reasoning="Need to visit Professor Oak to start the Pokemon journey",
        confidence=0.9
    )
    
    # Test basic metrics
    print(f"Action exact match: {action_exact_match(example, prediction)}")
    print(f"Buttons exact match: {buttons_exact_match(example, prediction)}")
    print(f"Buttons partial match: {buttons_partial_match(example, prediction)}")
    print(f"Gameplay effectiveness: {gameplay_effectiveness_metric(example, prediction):.3f}")
    print(f"Game progress: {game_progress_metric(example, prediction):.3f}")
    
    # Test evaluator creation
    try:
        evaluator = create_pokemon_evaluator(
            devset=[example],
            metric_name="gameplay_effectiveness",
            display_progress=False
        )
        print("✓ Evaluator creation successful")
    except Exception as e:
        print(f"✗ Evaluator creation failed: {e}")
    
    print("Basic functionality test completed!")


if __name__ == "__main__":
    # Run basic test if executed directly
    run_basic_functionality_test()

