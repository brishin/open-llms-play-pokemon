"""Tests for game state and memory reading functionality."""

import sys
from pathlib import Path
from typing import cast

from pyboy import PyBoy, PyBoyMemoryView

from open_llms_play_pokemon.game_state import (
    PokemonRedGameState,
    PokemonRedMemoryReader,
)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_memory_reader_with_init_state():
    """Test reading memory from emulator after loading init.state file."""
    pyboy = PyBoy("game/Pokemon Red.gb", window="null")

    try:
        with open("game/init.state", "rb") as state_file:
            pyboy.load_state(state_file)
        game_state = PokemonRedMemoryReader.parse_game_state(pyboy)

        assert isinstance(game_state, PokemonRedGameState)
        assert game_state.current_map >= 0
        assert game_state.player_x >= 0
        assert game_state.player_y >= 0
        assert game_state.party_count >= 0
        assert game_state.badges_obtained >= 0
        assert isinstance(game_state.event_flags, list)
        assert isinstance(game_state.is_in_battle, bool)

        print(f"Game state: {game_state}")

    finally:
        pyboy.stop()


def test_memory_reader_16bit_functions():
    """Test the 16-bit memory reading helper functions."""
    # Test data: 0x1234 should be stored as 0x34, 0x12 (little endian)
    test_data = [0x34, 0x12, 0x78, 0x56]
    memory_view = cast(PyBoyMemoryView, MockMemoryView(test_data))

    # Test single 16-bit read
    value = PokemonRedMemoryReader._read_16bit(memory_view, 0)
    assert value == 0x1234

    value = PokemonRedMemoryReader._read_16bit(memory_view, 2)
    assert value == 0x5678

    # Test multiple 16-bit reads
    values = PokemonRedMemoryReader._read_multiple_16bit(memory_view, [0, 2])
    assert values == [0x1234, 0x5678]


class MockMemoryView:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.data[key]
        return self.data[key]
