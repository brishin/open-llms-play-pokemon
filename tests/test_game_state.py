"""Tests for game state and memory reading functionality with the new consolidated system."""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from open_llms_play_pokemon.game_state import (  # noqa: E402
    ConsolidatedGameState,
    PokemonRedGameState,
    PokemonRedMemoryReader,
)
from open_llms_play_pokemon.game_state.data.memory_addresses import (  # noqa: E402
    MemoryAddresses,
)


def test_game_state_to_dict_excludes_event_flags():
    """Test that PokemonRedGameState.to_dict() excludes event_flags."""
    game_state = PokemonRedGameState(
        player_name="ASH",
        current_map=1,
        player_x=5,
        player_y=5,
        party_count=2,
        party_pokemon_levels=[25, 20],
        party_pokemon_hp=[(50, 80), (40, 60)],
        badges_obtained=3,
        badges_binary=0b00000111,
        event_flags=[0, 1, 1, 0, 1, 0],
        is_in_battle=False,
        player_mon_hp=(50, 80),
        enemy_mon_hp=None,
    )

    result = game_state.to_dict()

    # Verify event_flags are excluded
    assert "event_flags" not in result

    # Verify other fields are present
    assert result["player_name"] == "ASH"
    assert result["current_map"] == 1
    assert result["party_count"] == 2
    assert result["badges_obtained"] == 3


def test_consolidated_game_state_structure():
    """Test ConsolidatedGameState structure and serialization."""
    state = ConsolidatedGameState(
        step_counter=10,
        timestamp="2023-01-01T12:00:00",
        player_name="TEST",
        current_map=5,
        player_x=10,
        player_y=8,
        party_count=1,
        party_pokemon_levels=[15],
        party_pokemon_hp=[(60, 80)],
        badges_obtained=2,
        is_in_battle=False,
        player_mon_hp=None,
        enemy_mon_hp=None,
        map_loading_status=0,
        current_tileset=2,
        walkable_tiles=[(5, 5, 2), (6, 6, 3), (7, 7, 4)],
        blocked_tiles=[(0, 0, 15), (1, 1, 14)],
        encounter_tiles=[(8, 8), (9, 9)],
        warp_tiles=[(10, 10)],
        interactive_tiles=[(11, 11)],
        tile_type_counts={"walkable": 3, "blocked": 2, "grass": 2},
        directions_available={
            "north": True,
            "south": False,
            "east": True,
            "west": True,
        },
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
    """Test PokemonRedMemoryReader.get_consolidated_game_state() with mocks."""
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

    # Test the consolidated method
    consolidated = reader.get_consolidated_game_state(mock_memory_view)

    # Verify the result
    assert isinstance(consolidated, ConsolidatedGameState)
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
    assert isinstance(consolidated.directions_available, dict)

    # Verify directions have the expected keys
    directions = consolidated.directions_available
    assert "north" in directions
    assert "south" in directions
    assert "east" in directions
    assert "west" in directions


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

    coords = reader._extract_tile_coordinates(mock_tiles)
    assert coords == [(5, 6), (7, 8), (9, 10)]

    # Test coordinate extraction with distance
    coords_with_distance = reader._extract_tile_coordinates_with_distance(mock_tiles)
    assert len(coords_with_distance) == 3
    assert len(coords_with_distance[0]) == 3  # x, y, distance
    assert coords_with_distance[0][0] == 5  # x
    assert coords_with_distance[0][1] == 6  # y
    assert isinstance(coords_with_distance[0][2], int)  # distance

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


if __name__ == "__main__":
    test_game_state_to_dict_excludes_event_flags()
    test_consolidated_game_state_structure()
    test_memory_reader_consolidated_method()
    test_memory_reader_utility_methods()
    print("✅ All new consolidated system tests passed!")
