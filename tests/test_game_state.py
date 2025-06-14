"""Tests for game state and memory reading functionality."""

import sys
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

from pyboy import PyBoy, PyBoyMemoryView

from open_llms_play_pokemon.game_state import (
    PokemonRedGameState,
    PokemonRedMemoryReader,
)
from open_llms_play_pokemon.game_state.data.memory_addresses import MemoryAddresses
from open_llms_play_pokemon.game_state.tile_data import TileData, TileMatrix, TileType

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


def test_enhanced_tile_system_integration():
    """Test full integration of enhanced tile system with memory reader."""
    pyboy = PyBoy("game/Pokemon Red.gb", window="null")

    try:
        with open("game/init.state", "rb") as state_file:
            pyboy.load_state(state_file)

        memory_reader = PokemonRedMemoryReader(pyboy)
        memory_view = pyboy.memory

        # Test enhanced tile system integration
        game_state, tile_matrix = memory_reader.parse_game_state_with_tiles(memory_view)

        # Verify game state is valid
        assert isinstance(game_state, PokemonRedGameState)
        assert game_state.current_map >= 0

        # Verify tile matrix structure
        if tile_matrix is not None:
            assert isinstance(tile_matrix, TileMatrix)
            assert tile_matrix.width == 20
            assert tile_matrix.height == 18
            assert len(tile_matrix.tiles) == 18
            assert len(tile_matrix.tiles[0]) == 20

            # Check that tiles have enhanced properties
            sample_tile = tile_matrix.tiles[5][10]  # Middle of screen
            assert isinstance(sample_tile, TileData)
            assert hasattr(sample_tile, "is_walkable")
            assert hasattr(sample_tile, "is_encounter_tile")
            assert hasattr(sample_tile, "tile_type")
            assert hasattr(sample_tile, "tileset_id")

    finally:
        pyboy.stop()


def test_comprehensive_game_data_integration():
    """Test comprehensive game data collection with enhanced tile analysis."""
    pyboy = PyBoy("game/Pokemon Red.gb", window="null")

    try:
        with open("game/init.state", "rb") as state_file:
            pyboy.load_state(state_file)

        memory_reader = PokemonRedMemoryReader(pyboy)
        memory_view = pyboy.memory

        # Get comprehensive game data
        comprehensive_data = memory_reader.get_comprehensive_game_data(memory_view)

        # Verify structure
        assert "game_state" in comprehensive_data
        assert "tile_data" in comprehensive_data
        assert "enhanced_tile_analysis" in comprehensive_data
        assert "memory_state" in comprehensive_data

        # Check game state section
        game_state_data = comprehensive_data["game_state"]
        assert "current_map" in game_state_data
        assert "player_x" in game_state_data
        assert "player_y" in game_state_data
        assert "party_count" in game_state_data

        # Check memory state validation
        memory_state = comprehensive_data["memory_state"]
        assert "enhanced_system_available" in memory_state
        assert isinstance(memory_state["enhanced_system_available"], bool)

        # If enhanced tile analysis is available, verify structure
        enhanced_analysis = comprehensive_data["enhanced_tile_analysis"]
        if enhanced_analysis is not None:
            assert "walkable" in enhanced_analysis
            assert "blocked" in enhanced_analysis
            assert "player_context" in enhanced_analysis
            assert "map_context" in enhanced_analysis

            # Check player context
            player_context = enhanced_analysis["player_context"]
            assert "position" in player_context
            assert "screen_center" in player_context
            assert player_context["screen_center"] == (10, 9)

            # Check map context
            map_context = enhanced_analysis["map_context"]
            assert "screen_dimensions" in map_context
            assert map_context["screen_dimensions"] == (20, 18)

    finally:
        pyboy.stop()


def test_enhanced_tile_matrix_fallback():
    """Test that enhanced tile system falls back gracefully to legacy system."""
    # Create mock pyboy and memory reader
    mock_pyboy = Mock()
    mock_memory_view = Mock()

    # Mock memory addresses for stable map state
    def mock_getitem(addr):
        return {
            MemoryAddresses.map_loading_status: 0,
            MemoryAddresses.current_map: 1,
            MemoryAddresses.current_tileset: 0,
            MemoryAddresses.x_coord: 10,
            MemoryAddresses.y_coord: 10,
        }.get(addr, 0)

    mock_memory_view.__getitem__ = Mock(side_effect=mock_getitem)

    memory_reader = PokemonRedMemoryReader(mock_pyboy)

    # Mock the enhanced tile system to fail
    with patch(
        "open_llms_play_pokemon.game_state.memory_reader.analyze_screen"
    ) as mock_analyze:
        mock_analyze.side_effect = Exception("Enhanced system failed")

        # Mock the legacy tile reader to succeed
        mock_tile_matrix = Mock(spec=TileMatrix)
        memory_reader.tile_reader.get_tile_matrix = Mock(return_value=mock_tile_matrix)

        # Mock parse_game_state
        mock_game_state = Mock(spec=PokemonRedGameState)
        memory_reader.parse_game_state = Mock(return_value=mock_game_state)

        # Test fallback behavior
        game_state, tile_matrix = memory_reader.parse_game_state_with_tiles(
            mock_memory_view
        )

        # Verify fallback worked
        assert game_state == mock_game_state
        assert tile_matrix == mock_tile_matrix
        mock_analyze.assert_called_once()


def test_enhanced_tile_matrix_creation():
    """Test creation of enhanced tile matrix from tile data."""
    # Create mock enhanced tiles
    from open_llms_play_pokemon.game_state.data.tile_data_constants import TilesetID

    enhanced_tiles = []
    for y in range(3):  # Small test area
        for x in range(3):
            tile = TileData(
                tile_id=0x52,
                x=x,
                y=y,
                map_x=x + 10,
                map_y=y + 10,
                tile_type=TileType.GRASS,
                tileset_id=TilesetID.OVERWORLD,
                raw_value=0x52,
                is_walkable=True,
                is_ledge_tile=False,
                ledge_direction=None,
                movement_modifier=1.0,
                is_encounter_tile=True,
                is_warp_tile=False,
                is_animated=False,
                light_level=15,
                has_sign=False,
                has_bookshelf=False,
                strength_boulder=False,
                cuttable_tree=False,
                pc_accessible=False,
                trainer_sight_line=False,
                trainer_id=None,
                hidden_item_id=None,
                requires_itemfinder=False,
                safari_zone_steps=False,
                game_corner_tile=False,
                is_fly_destination=False,
                has_footstep_sound=True,
                sprite_priority=0,
                background_priority=0,
                elevation_pair=None,
                sprite_offset=0,
                blocks_light=False,
                water_current_direction=None,
                warp_destination_map=None,
                warp_destination_x=None,
                warp_destination_y=None,
            )
            enhanced_tiles.append(tile)

    # Create mock game state
    mock_game_state = Mock()
    mock_game_state.current_map = 1
    mock_game_state.player_x = 10
    mock_game_state.player_y = 10

    # Create memory reader and test tile matrix creation
    mock_pyboy = Mock()
    memory_reader = PokemonRedMemoryReader(mock_pyboy)
    tile_matrix = memory_reader._create_enhanced_tile_matrix(
        enhanced_tiles, mock_game_state
    )

    # Verify matrix structure
    assert isinstance(tile_matrix, TileMatrix)
    assert tile_matrix.width == 20
    assert tile_matrix.height == 18
    assert tile_matrix.current_map == 1
    assert tile_matrix.player_x == 10
    assert tile_matrix.player_y == 10

    # Check that enhanced tiles are in correct positions
    for y in range(3):
        for x in range(3):
            tile = tile_matrix.get_tile(x, y)
            assert tile is not None
            assert tile.x == x
            assert tile.y == y
            assert tile.tile_type == TileType.GRASS
            assert tile.is_encounter_tile is True

    # Check that missing positions have placeholders
    placeholder = tile_matrix.get_tile(5, 5)
    assert placeholder is not None
    assert placeholder.tile_type == TileType.UNKNOWN
    assert placeholder.is_walkable is False


def test_memory_state_validation():
    """Test memory state validation in enhanced tile system."""
    mock_pyboy = Mock()
    mock_memory_view = Mock()
    memory_reader = PokemonRedMemoryReader(mock_pyboy)

    # Test with loading map state (should return None)
    def mock_getitem(addr):
        return {
            MemoryAddresses.map_loading_status: 1,  # Map is loading
        }.get(addr, 0)

    mock_memory_view.__getitem__ = Mock(side_effect=mock_getitem)

    mock_game_state = Mock(spec=PokemonRedGameState)
    memory_reader.parse_game_state = Mock(return_value=mock_game_state)

    game_state, tile_matrix = memory_reader.parse_game_state_with_tiles(
        mock_memory_view
    )

    # Should return game state but no tile matrix when map is loading
    assert game_state == mock_game_state
    assert tile_matrix is None


def test_comprehensive_data_with_enhanced_analysis():
    """Test comprehensive data includes enhanced analysis when available."""
    mock_pyboy = Mock()
    mock_memory_view = Mock()
    memory_reader = PokemonRedMemoryReader(mock_pyboy)

    # Mock memory addresses
    def mock_getitem(addr):
        return {
            MemoryAddresses.map_loading_status: 0,
            MemoryAddresses.current_map: 1,
            MemoryAddresses.current_tileset: 0,
        }.get(addr, 0)

    mock_memory_view.__getitem__ = Mock(side_effect=mock_getitem)

    # Mock enhanced analysis
    mock_enhanced_data = {
        "walkable": [],
        "blocked": [],
        "player_context": {"position": (10, 10), "screen_center": (10, 9)},
        "map_context": {"screen_dimensions": (20, 18)},
    }

    with patch(
        "open_llms_play_pokemon.game_state.memory_reader.get_comprehensive_game_data"
    ) as mock_enhanced:
        mock_enhanced.return_value = mock_enhanced_data

        # Mock game state parsing with all required attributes
        mock_game_state = Mock(spec=PokemonRedGameState)
        mock_game_state.player_name = "RED"
        mock_game_state.current_map = 1
        mock_game_state.player_x = 10
        mock_game_state.player_y = 10
        mock_game_state.party_count = 1
        mock_game_state.party_pokemon_levels = [5]
        mock_game_state.party_pokemon_hp = [(15, 20)]
        mock_game_state.badges_obtained = 0
        mock_game_state.badges_binary = 0
        mock_game_state.is_in_battle = False
        mock_game_state.player_mon_hp = None
        mock_game_state.enemy_mon_hp = None
        mock_game_state.event_flags = []

        memory_reader.parse_game_state = Mock(return_value=mock_game_state)

        # Mock tile matrix creation to return None (no tiles)
        memory_reader.parse_game_state_with_tiles = Mock(
            return_value=(mock_game_state, None)
        )

        comprehensive_data = memory_reader.get_comprehensive_game_data(mock_memory_view)

        # Verify enhanced analysis is included
        assert comprehensive_data["enhanced_tile_analysis"] == mock_enhanced_data
        assert comprehensive_data["memory_state"]["enhanced_system_available"] is True

        # Verify the enhanced analysis function was called with memory view
        mock_enhanced.assert_called_once_with(mock_memory_view)


class MockMemoryView:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.data[key]
        return self.data[key]
