"""Tests for game state and memory reading functionality with the new consolidated system."""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from open_llms_play_pokemon.game_state import (  # noqa: E402
    DirectionsAvailable,
    PokemonHp,
    PokemonRedGameState,
    PokemonRedMemoryReader,
)
from open_llms_play_pokemon.game_state.data.memory_addresses import (  # noqa: E402
    MemoryAddresses,
)
from open_llms_play_pokemon.game_state.tile_data import TileMatrix  # noqa: E402
from open_llms_play_pokemon.game_state.tile_data_factory import (  # noqa: E402
    TileDataFactory,
)


def create_test_tile_matrix() -> TileMatrix:
    """Create a test TileMatrix with placeholder tiles."""
    width, height = 20, 18
    tiles = [
        [TileDataFactory.create_placeholder(x, y) for x in range(width)]
        for y in range(height)
    ]
    return TileMatrix(
        tiles=tiles,
        width=width,
        height=height,
        current_map=1,
        player_x=10,
        player_y=9,
        timestamp=None,
    )


def test_game_state_to_dict():
    """Test that PokemonRedGameState.to_dict() works correctly."""
    game_state = PokemonRedGameState(
        step_counter=10,
        timestamp="2024-01-01T00:00:00",
        player_name="ASH",
        current_map=1,
        player_x=5,
        player_y=5,
        party_count=2,
        party_pokemon_levels=[25, 20],
        party_pokemon_hp=[PokemonHp(current=50, max=80), PokemonHp(current=40, max=60)],
        badges_obtained=3,
        is_in_battle=False,
        player_mon_hp=PokemonHp(current=50, max=80),
        enemy_mon_hp=None,
        map_loading_status=0,
        current_tileset=1,
        tile_matrix=create_test_tile_matrix(),
        directions_available=DirectionsAvailable(
            north=True, south=True, east=True, west=True
        ),
    )

    result = game_state.to_dict()

    # Verify fields are present
    assert result["player_name"] == "ASH"
    assert result["current_map"] == 1
    assert result["party_count"] == 2
    assert result["badges_obtained"] == 3
    assert result["step_counter"] == 10


def test_consolidated_game_state_structure():
    """Test PokemonRedGameState structure and serialization."""
    state = PokemonRedGameState(
        step_counter=10,
        timestamp="2023-01-01T12:00:00",
        player_name="TEST",
        current_map=5,
        player_x=10,
        player_y=8,
        party_count=1,
        party_pokemon_levels=[15],
        party_pokemon_hp=[PokemonHp(current=60, max=80)],
        badges_obtained=2,
        is_in_battle=False,
        player_mon_hp=None,
        enemy_mon_hp=None,
        map_loading_status=0,
        current_tileset=2,
        tile_matrix=create_test_tile_matrix(),
        directions_available=DirectionsAvailable(
            north=True,
            south=False,
            east=True,
            west=True,
        ),
    )

    # Test serialization
    data = state.to_dict()

    # Verify core structure
    assert data["step_counter"] == 10
    assert data["player_name"] == "TEST"
    assert data["current_map"] == 5
    assert "tile_matrix" in data
    assert data["tile_matrix"]["width"] == 20
    assert data["tile_matrix"]["height"] == 18

    # Verify directions
    directions = data["directions_available"]
    assert directions["north"] is True
    assert directions["south"] is False
    assert directions["east"] is True
    assert directions["west"] is True


def test_memory_reader_consolidated_method():
    """Test PokemonRedMemoryReader.parse_game_state() with mocks."""
    # Create mock PyBoy and memory view
    mock_pyboy = Mock()
    mock_memory_view = Mock()

    # Setup memory mock data
    test_memory_data = {
        MemoryAddresses.party_count: 2,
        MemoryAddresses.obtained_badges: 0b00000011,  # 2 badges
        MemoryAddresses.is_in_battle: 0,
        MemoryAddresses.current_map: 3,
        MemoryAddresses.x_coord: 12,
        MemoryAddresses.y_coord: 8,
        MemoryAddresses.player_name: "PLAYER",
        MemoryAddresses.map_loading_status: 0,
        MemoryAddresses.current_tileset: 1,
        MemoryAddresses.event_flags_start: 0,
    }

    def mock_getitem(addr):
        if isinstance(addr, slice):
            if addr.start == MemoryAddresses.event_flags_start:
                return [0] * 320  # Event flags array
            elif addr.stop - addr.start == 2:
                return [75, 0]  # HP values
        try:
            return test_memory_data.get(addr, 0)  # type: ignore[arg-type]
        except (TypeError, KeyError):
            return 0

    mock_memory_view.__getitem__ = Mock(side_effect=mock_getitem)

    # Set up PyBoy's memory to use our mock
    mock_pyboy.memory = mock_memory_view

    # Create memory reader
    reader = PokemonRedMemoryReader(mock_pyboy)

    # Test the parse game state method
    consolidated = reader.parse_game_state(mock_memory_view)

    # Verify the result
    assert isinstance(consolidated, PokemonRedGameState)
    assert consolidated.player_name == "PLAYER"
    assert consolidated.current_map == 3
    assert consolidated.player_x == 12
    assert consolidated.player_y == 8
    assert consolidated.party_count == 2
    assert consolidated.badges_obtained == 2

    # Verify tile data structure
    assert isinstance(consolidated.tile_matrix, TileMatrix)
    assert consolidated.tile_matrix.width == 20
    assert consolidated.tile_matrix.height == 18
    assert isinstance(consolidated.directions_available, DirectionsAvailable)

    # Verify directions have the expected attributes
    directions = consolidated.directions_available
    assert hasattr(directions, "north")
    assert hasattr(directions, "south")
    assert hasattr(directions, "east")
    assert hasattr(directions, "west")


def test_memory_reader_utility_methods():
    """Test the remaining utility methods in PokemonRedMemoryReader."""
    reader = PokemonRedMemoryReader(Mock())

    # Test directions checking
    mock_tiles = [
        Mock(x=10, y=8, is_walkable=True),  # North of player (10, 9)
        Mock(x=10, y=10, is_walkable=False),  # South of player
        Mock(x=11, y=9, is_walkable=True),  # East of player
        Mock(x=9, y=9, is_walkable=True),  # West of player
    ]

    directions = reader._check_immediate_directions(mock_tiles, 10, 9)
    assert directions.north is True
    assert directions.south is False
    assert directions.east is True
    assert directions.west is True
