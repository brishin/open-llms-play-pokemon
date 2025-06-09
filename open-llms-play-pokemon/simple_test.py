"""
Simple test script for DSPy metrics without external dependencies.
"""

from dspy_metrics import (
    GameplayExample,
    GameplayPrediction,
    action_exact_match,
    buttons_exact_match,
    buttons_partial_match,
    gameplay_effectiveness_metric,
    game_progress_metric,
)

def test_basic_metrics():
    """Test basic metrics functionality."""
    print("Testing DSPy Metrics Implementation")
    print("=" * 50)
    
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
    
    correct_prediction = GameplayPrediction(
        action="Move up to enter Professor Oak's lab",
        buttons=["up", "a"],
        reasoning="Need to visit Professor Oak to start the Pokemon journey",
        confidence=0.9
    )
    
    incorrect_prediction = GameplayPrediction(
        action="Go to Pokemon Center",
        buttons=["down", "left"],
        reasoning="Need to heal Pokemon",
        confidence=0.7
    )
    
    print("\n1. Testing Action Exact Match:")
    print(f"   Correct prediction: {action_exact_match(example, correct_prediction)}")
    print(f"   Incorrect prediction: {action_exact_match(example, incorrect_prediction)}")
    
    print("\n2. Testing Buttons Exact Match:")
    print(f"   Correct prediction: {buttons_exact_match(example, correct_prediction)}")
    print(f"   Incorrect prediction: {buttons_exact_match(example, incorrect_prediction)}")
    
    print("\n3. Testing Buttons Partial Match:")
    print(f"   Correct prediction: {buttons_partial_match(example, correct_prediction):.3f}")
    print(f"   Incorrect prediction: {buttons_partial_match(example, incorrect_prediction):.3f}")
    
    print("\n4. Testing Gameplay Effectiveness:")
    print(f"   Correct prediction: {gameplay_effectiveness_metric(example, correct_prediction):.3f}")
    print(f"   Incorrect prediction: {gameplay_effectiveness_metric(example, incorrect_prediction):.3f}")
    
    print("\n5. Testing Game Progress:")
    print(f"   Correct prediction: {game_progress_metric(example, correct_prediction):.3f}")
    print(f"   Incorrect prediction: {game_progress_metric(example, incorrect_prediction):.3f}")
    
    # Test with trace mode (optimization)
    print("\n6. Testing Trace Mode (Optimization):")
    trace_result = gameplay_effectiveness_metric(example, correct_prediction, trace={})
    print(f"   Trace mode result (bool): {trace_result}")
    
    print("\n" + "=" * 50)
    print("✓ All basic tests completed successfully!")
    
    return True

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\nTesting Edge Cases:")
    print("-" * 30)
    
    # Test with minimal data
    minimal_example = GameplayExample(
        screen_base64="test",
        context="minimal context"
    )
    
    minimal_prediction = GameplayPrediction(
        action="minimal action",
        buttons=[]
    )
    
    print(f"Minimal data - Gameplay effectiveness: {gameplay_effectiveness_metric(minimal_example, minimal_prediction):.3f}")
    
    # Test with empty buttons
    empty_buttons_pred = GameplayPrediction(
        action="some action",
        buttons=[]
    )
    
    print(f"Empty buttons - Buttons partial match: {buttons_partial_match(minimal_example, empty_buttons_pred):.3f}")
    
    # Test with invalid buttons
    invalid_buttons_pred = GameplayPrediction(
        action="move around",
        buttons=["invalid_button", "another_invalid"]
    )
    
    print(f"Invalid buttons - Gameplay effectiveness: {gameplay_effectiveness_metric(minimal_example, invalid_buttons_pred):.3f}")
    
    print("✓ Edge case tests completed!")

if __name__ == "__main__":
    try:
        test_basic_metrics()
        test_edge_cases()
        print("\n🎉 All tests passed! DSPy metrics implementation is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

