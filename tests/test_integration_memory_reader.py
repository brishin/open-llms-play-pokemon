"""Integration tests for memory reader with real game data."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from open_llms_play_pokemon.game_state import (
    DirectionsAvailable,
    PokemonHp,
    PokemonRedGameState,
    PokemonRedMemoryReader,
)
from open_llms_play_pokemon.game_state.tile_data import TileMatrix


def test_memory_reader_integration_with_init_state():
    """Integration test that loads real init.state and tests memory reader parsing."""
    try:
        from pyboy import PyBoy
    except ImportError:
        import pytest

        pytest.skip("PyBoy not available for integration test")

    # Get paths to game files
    game_dir = project_root / "game"
    rom_path = game_dir / "Pokemon Red.gb"
    state_path = game_dir / "init.state"

    if not rom_path.exists():
        raise FileNotFoundError(f"Game files not found at {game_dir}")
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found at {state_path}")

    # Initialize PyBoy with the ROM
    pyboy = None
    try:
        pyboy = PyBoy(str(rom_path), window="null")

        # Load the init.state
        with open(state_path, "rb") as f:
            pyboy.load_state(f)

        # Create memory reader and parse game state
        memory_reader = PokemonRedMemoryReader(pyboy)
        memory_view = pyboy.memory

        # Parse the game state
        game_state = memory_reader.parse_game_state(
            memory_view, step_counter=1, timestamp="2024-01-01T10:00:00"
        )

        # Verify the parsed state structure and basic sanity checks
        assert isinstance(game_state, PokemonRedGameState)

        # Runtime metadata
        assert game_state.step_counter == 1
        assert game_state.timestamp == "2024-01-01T10:00:00"

        # Basic game state validation
        # Note: player_name might be raw bytes/int in some cases, not decoded string
        assert game_state.player_name is not None
        assert isinstance(game_state.current_map, int)
        assert game_state.current_map >= 0
        assert isinstance(game_state.player_x, int)
        assert isinstance(game_state.player_y, int)
        assert game_state.player_x >= 0
        assert game_state.player_y >= 0

        # Party data validation
        assert isinstance(game_state.party_count, int)
        assert 0 <= game_state.party_count <= 6
        assert isinstance(game_state.party_pokemon_levels, list)
        assert isinstance(game_state.party_pokemon_hp, list)
        assert len(game_state.party_pokemon_levels) == game_state.party_count
        assert len(game_state.party_pokemon_hp) == game_state.party_count

        # Verify HP structures if party exists
        for hp in game_state.party_pokemon_hp:
            assert isinstance(hp, PokemonHp)
            assert hp.current >= 0
            assert hp.max > 0
            assert hp.current <= hp.max

        # Badge count validation
        assert isinstance(game_state.badges_obtained, int)
        assert 0 <= game_state.badges_obtained <= 8

        # Battle state validation
        assert isinstance(game_state.is_in_battle, bool)
        if game_state.is_in_battle:
            assert game_state.player_mon_hp is not None
            assert isinstance(game_state.player_mon_hp, PokemonHp)

        # Tile matrix validation
        assert isinstance(game_state.tile_matrix, TileMatrix)
        assert game_state.tile_matrix.width == 20
        assert game_state.tile_matrix.height == 18
        assert game_state.tile_matrix.current_map == game_state.current_map
        assert game_state.tile_matrix.player_x == game_state.player_x
        assert game_state.tile_matrix.player_y == game_state.player_y

        # Verify tile matrix has tiles
        test_tile = game_state.tile_matrix.get_tile(0, 0)
        assert test_tile is not None
        assert hasattr(test_tile, "tile_id")
        assert hasattr(test_tile, "is_walkable")
        assert hasattr(test_tile, "tile_type")

        # Directions validation
        assert isinstance(game_state.directions_available, DirectionsAvailable)
        assert isinstance(game_state.directions_available.north, bool)
        assert isinstance(game_state.directions_available.south, bool)
        assert isinstance(game_state.directions_available.east, bool)
        assert isinstance(game_state.directions_available.west, bool)

        # Serialization test
        game_dict = game_state.to_dict()
        assert isinstance(game_dict, dict)
        assert "player_name" in game_dict
        assert "current_map" in game_dict
        assert "party_count" in game_dict
        assert "tile_matrix" in game_dict
        assert "directions_available" in game_dict

        # Verify serialized directions structure
        directions_dict = game_dict["directions_available"]
        assert isinstance(directions_dict, dict)
        assert directions_dict == {
            "north": False,
            "south": False,
            "east": False,
            "west": False,
        }

        print("✅ Integration test passed - loaded init.state with:")
        print(f"   Player: {game_state.player_name} at map {game_state.current_map}")
        print(f"   Position: ({game_state.player_x}, {game_state.player_y})")
        print(f"   Party: {game_state.party_count} Pokemon")
        print(f"   Badges: {game_state.badges_obtained}")
        print(
            f"   Tile Matrix: {game_state.tile_matrix.width}x{game_state.tile_matrix.height}"
        )
        print(
            f"   Walkable tiles in matrix: {len(game_state.tile_matrix.get_walkable_tiles())}"
        )
        print(f"   Directions available: {directions_dict}")

    finally:
        if pyboy:
            pyboy.stop()
