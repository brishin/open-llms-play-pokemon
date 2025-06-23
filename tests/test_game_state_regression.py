"""Regression tests for specific game state parsing issues."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from open_llms_play_pokemon.game_state.game_state_parsing import (
    get_game_state_json,
    get_game_state_text,
)


def test_all_directions_available_state():
    """
    Regression test for issue where west direction was incorrectly blocked.

    This test uses a specific game state (all_directions_available.state) where
    the player should be able to move in all four directions, but previously
    west was incorrectly detected as blocked due to collision detection issues.

    Fixed in: memory_reader.py and tile_reader.py
    """

    # Use the fixture state file
    state_file = "tests/fixtures/all_directions_available.state"

    # Test JSON output
    game_state = get_game_state_json(state_file)

    # Verify basic state info
    assert game_state["current_map"] == 38
    assert game_state["player_x"] == 4
    assert game_state["player_y"] == 3

    # Verify all directions are available (main regression test)
    directions = game_state["directions_available"]
    assert directions["north"] is True, "North should be available"
    assert directions["south"] is True, "South should be available"
    assert directions["east"] is True, "East should be available"
    assert directions["west"] is True, (
        "West should be available (was previously blocked)"
    )

    # Test text output format
    text_output = get_game_state_text(state_file)

    # Verify text contains all movement symbols
    assert "↑N" in text_output, "North movement symbol should be present"
    assert "↓S" in text_output, "South movement symbol should be present"
    assert "→E" in text_output, "East movement symbol should be present"
    assert "←W" in text_output, (
        "West movement symbol should be present (was previously missing)"
    )

    # Verify no blocked directions are mentioned
    assert "blocked" not in text_output.lower(), "No directions should be blocked"


def test_map_loading_status_16_not_transitioning():
    """
    Regression test for issue where map loading status 16 was incorrectly
    interpreted as "Map transition in progress".

    Status value 16 should be considered stable/loaded, not transitioning.
    Only values 1-3 should be treated as actively transitioning.

    Fixed in: game_state_parsing.py and tile_reader.py
    """
    state_file = "tests/fixtures/all_directions_available.state"
    game_state = get_game_state_json(state_file)

    assert game_state["map_loading_status"] == 16
