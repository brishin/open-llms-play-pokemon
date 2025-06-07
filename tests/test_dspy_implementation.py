"""Test script for DSPy implementation."""

import dspy
from main_dspy import DSPyOpenAILM, GameState, PokemonRedDSPyAgent


def test_dspy_agent():
    """Test the DSPy agent without running the full game."""
    # Set up DSPy language model (this will work even without API credentials for basic init)
    lm = DSPyOpenAILM()
    dspy.configure(lm=lm)

    # Create agent
    agent = PokemonRedDSPyAgent()
    assert agent is not None

    # Create mock game state
    game_state = GameState(
        screen_base64="dummy_base64_data",
        context="Test context for Pokemon Red game",
    )
    assert game_state.screen_base64 == "dummy_base64_data"
    assert game_state.context == "Test context for Pokemon Red game"
