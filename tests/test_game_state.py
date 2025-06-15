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
    TilePosition,
    TileWithDistance,
)
from open_llms_play_pokemon.game_state.data.memory_addresses import (  # noqa: E402
    MemoryAddresses,
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
        walkable_tiles=[],
        blocked_tiles=[],
        encounter_tiles=[],
        warp_tiles=[],
        interactive_tiles=[],
        tile_type_counts={},
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
        walkable_tiles=[
            TileWithDistance(x=5, y=5, distance=2),
            TileWithDistance(x=6, y=6, distance=3),
            TileWithDistance(x=7, y=7, distance=4),
        ],
        blocked_tiles=[
            TileWithDistance(x=0, y=0, distance=15),
            TileWithDistance(x=1, y=1, distance=14),
        ],
        encounter_tiles=[TilePosition(x=8, y=8), TilePosition(x=9, y=9)],
        warp_tiles=[TilePosition(x=10, y=10)],
        interactive_tiles=[TilePosition(x=11, y=11)],
        tile_type_counts={"walkable": 3, "blocked": 2, "grass": 2},
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
    assert len(data["walkable_tiles"]) == 3
    assert len(data["blocked_tiles"]) == 2
    assert data["tile_type_counts"]["walkable"] == 3

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
    assert isinstance(consolidated.walkable_tiles, list)
    assert isinstance(consolidated.blocked_tiles, list)
    assert isinstance(consolidated.tile_type_counts, dict)
    assert isinstance(consolidated.directions_available, DirectionsAvailable)

    # Verify directions have the expected attributes
    directions = consolidated.directions_available
    assert hasattr(directions, "north")
    assert hasattr(directions, "south")
    assert hasattr(directions, "east")
    assert hasattr(directions, "west")


def test_memory_reader_utility_methods():
    """Test the utility methods in PokemonRedMemoryReader."""
    reader = PokemonRedMemoryReader(Mock())

    # Test distance calculation
    distance = reader._calculate_distance(15, 12)
    expected = abs(15 - 10) + abs(12 - 9)  # Manhattan distance from center (10, 9)
    assert distance == expected

    # Test coordinate extraction
    mock_tiles = [
        Mock(x=5, y=6),
        Mock(x=7, y=8),
        Mock(x=9, y=10),
    ]

    positions = reader._extract_tile_positions(mock_tiles)
    expected_positions = [
        TilePosition(x=5, y=6),
        TilePosition(x=7, y=8),
        TilePosition(x=9, y=10),
    ]
    assert positions == expected_positions

    # Test position extraction with distance
    tiles_with_distance = reader._extract_tiles_with_distance(mock_tiles)
    assert len(tiles_with_distance) == 3
    assert tiles_with_distance[0].x == 5
    assert tiles_with_distance[0].y == 6
    assert isinstance(tiles_with_distance[0].distance, int)

    # Test tile type counting
    mock_tiles_for_count = [
        Mock(tile_type=Mock(value="walkable")),
        Mock(tile_type=Mock(value="walkable")),
        Mock(tile_type=Mock(value="blocked")),
        Mock(tile_type=Mock(value="grass")),
        Mock(tile_type=Mock(value="walkable")),
    ]

    counts = reader._count_tile_types(mock_tiles_for_count)
    assert counts["walkable"] == 3
    assert counts["blocked"] == 1
    assert counts["grass"] == 1
