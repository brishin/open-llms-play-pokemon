"""Tests for screen analyzer module."""

from unittest.mock import MagicMock, Mock

import pytest
from game_state.data.tile_data_constants import TilesetID
from game_state.screen_analyzer import (
    analyze_screen,
    categorize_tiles,
    find_nearest_tiles,
    get_comprehensive_game_data,
    get_interactive_tiles,
    get_movement_options,
    get_walkable_tiles,
)
from game_state.tile_data import TileData, TileType


@pytest.fixture
def mock_memory_view():
    """Create a mock memory view with stable map state."""
    memory_view = Mock()
    memory_view.__getitem__ = MagicMock()

    # Mock stable map state
    memory_view.__getitem__.side_effect = lambda addr: {
        0xD367: 0,  # current_tileset = OVERWORLD
        0xD362: 10,  # x_coord = 10
        0xD361: 10,  # y_coord = 10
        0xD36A: 0,  # map_loading_status = stable
        0xD35E: 1,  # current_map
        0xD368: 18,  # current_map_height
        0xD369: 20,  # current_map_width
        0xD357: 0,  # is_indoors = false
        0xC109: 0,  # player_direction
    }.get(addr, 0x10)  # Default to normal tile

    return memory_view


def create_test_tile_data(
    tile_id=0x52,
    x=5,
    y=5,
    map_x=15,
    map_y=15,
    tile_type=TileType.GRASS,
    is_walkable=True,
    is_encounter_tile=True,
    is_warp_tile=False,
    has_sign=False,
    **kwargs,
):
    """Helper to create TileData with correct field names."""
    defaults = {
        "tileset_id": TilesetID.OVERWORLD,
        "raw_value": tile_id,
        "is_ledge_tile": False,
        "ledge_direction": None,
        "movement_modifier": 1.0,
        "is_animated": False,
        "light_level": 15,
        "has_bookshelf": False,
        "strength_boulder": False,
        "cuttable_tree": False,
        "pc_accessible": False,
        "trainer_sight_line": False,
        "trainer_id": None,
        "hidden_item_id": None,
        "requires_itemfinder": False,
        "safari_zone_steps": False,
        "game_corner_tile": False,
        "is_fly_destination": False,
        "has_footstep_sound": True,
        "sprite_priority": 0,
        "background_priority": 0,
        "elevation_pair": None,
        "sprite_offset": 0,
        "blocks_light": False,
        "water_current_direction": None,
        "warp_destination_map": None,
        "warp_destination_x": None,
        "warp_destination_y": None,
    }
    defaults.update(kwargs)

    return TileData(
        tile_id=tile_id,
        x=x,
        y=y,
        map_x=map_x,
        map_y=map_y,
        tile_type=tile_type,
        is_walkable=is_walkable,
        is_encounter_tile=is_encounter_tile,
        is_warp_tile=is_warp_tile,
        has_sign=has_sign,
        **defaults,
    )


def test_analyze_screen_stable_map(monkeypatch, mock_memory_view):
    """Test screen analysis with stable map state."""

    # Mock create_tile_data to return predictable results
    def mock_create_tile_data(memory_view, x, y):
        return create_test_tile_data(x=x, y=y, map_x=x + 10, map_y=y + 10)

    import game_state.screen_analyzer as screen_analyzer_module

    monkeypatch.setattr(
        screen_analyzer_module, "create_tile_data", mock_create_tile_data
    )

    tiles = analyze_screen(mock_memory_view)

    # Should return 360 tiles (20 * 18)
    assert len(tiles) == 360

    # Check first and last tiles
    assert tiles[0].x == 0 and tiles[0].y == 0
    assert tiles[-1].x == 19 and tiles[-1].y == 17


def test_analyze_screen_loading_map(mock_memory_view):
    """Test screen analysis returns empty list when map is loading."""
    # Set map loading status to indicate transition
    mock_memory_view.__getitem__.side_effect = lambda addr: {
        0xD36A: 1,  # map_loading_status = loading
    }.get(addr, 0)

    tiles = analyze_screen(mock_memory_view)
    assert tiles == []


def test_get_walkable_tiles(monkeypatch, mock_memory_view):
    """Test filtering walkable tiles."""

    def mock_analyze_screen(memory_view):
        return [
            create_test_tile_data(x=0, y=0, is_walkable=True),
            create_test_tile_data(
                x=1, y=0, tile_type=TileType.BLOCKED, is_walkable=False
            ),
        ]

    import game_state.screen_analyzer as screen_analyzer_module

    monkeypatch.setattr(screen_analyzer_module, "analyze_screen", mock_analyze_screen)

    walkable = get_walkable_tiles(mock_memory_view)
    assert len(walkable) == 1
    assert walkable[0].is_walkable is True


def test_get_interactive_tiles(monkeypatch, mock_memory_view):
    """Test filtering interactive tiles."""

    def mock_analyze_screen(memory_view):
        return [
            create_test_tile_data(x=0, y=0, tile_type=TileType.GRASS, has_sign=True),
            create_test_tile_data(x=1, y=0, tile_type=TileType.GRASS, has_sign=False),
        ]

    import game_state.screen_analyzer as screen_analyzer_module

    monkeypatch.setattr(screen_analyzer_module, "analyze_screen", mock_analyze_screen)

    interactive = get_interactive_tiles(mock_memory_view)
    assert len(interactive) == 1
    assert interactive[0].has_sign is True


def test_categorize_tiles(monkeypatch, mock_memory_view):
    """Test comprehensive tile categorization."""

    def mock_analyze_screen(memory_view):
        return [
            create_test_tile_data(x=0, y=0, tile_type=TileType.GRASS, is_walkable=True),
            create_test_tile_data(
                x=1, y=0, tile_type=TileType.WATER, is_walkable=False, is_animated=True
            ),
        ]

    import game_state.screen_analyzer as screen_analyzer_module

    monkeypatch.setattr(screen_analyzer_module, "analyze_screen", mock_analyze_screen)

    categories = categorize_tiles(mock_memory_view)

    assert len(categories["grass"]) == 1
    assert len(categories["water"]) == 1
    assert len(categories["walkable"]) == 1
    assert len(categories["blocked"]) == 1
    assert categories["metadata"]["total_tiles"] == 2
    assert categories["metadata"]["analysis_successful"] is True


def test_get_comprehensive_game_data(monkeypatch, mock_memory_view):
    """Test comprehensive game data collection."""

    def mock_categorize_tiles(memory_view):
        return {
            "water": [],
            "trees": [],
            "grass": [Mock()],
            "doors": [],
            "walkable": [Mock(), Mock()],
            "blocked": [Mock()],
            "interactive": [],
            "encounters": [Mock()],
            "warps": [],
            "special": [],
            "metadata": {
                "current_map": 1,
                "tileset_id": TilesetID.OVERWORLD,
                "total_tiles": 3,
                "analysis_successful": True,
            },
        }

    import game_state.screen_analyzer as screen_analyzer_module

    monkeypatch.setattr(
        screen_analyzer_module, "categorize_tiles", mock_categorize_tiles
    )

    game_data = get_comprehensive_game_data(mock_memory_view)

    # Check that all tile categories are present
    assert "grass" in game_data
    assert "walkable" in game_data

    # Check player context
    assert "player_context" in game_data
    assert game_data["player_context"]["position"] == (10, 10)
    assert game_data["player_context"]["screen_center"] == (10, 9)

    # Check map context
    assert "map_context" in game_data
    assert game_data["map_context"]["dimensions"] == (20, 18)
    assert game_data["map_context"]["screen_dimensions"] == (20, 18)


def test_find_nearest_tiles(monkeypatch, mock_memory_view):
    """Test finding nearest tiles by type."""

    def mock_analyze_screen(memory_view):
        return [
            create_test_tile_data(x=5, y=5, tile_type=TileType.GRASS),
            create_test_tile_data(x=15, y=15, tile_type=TileType.GRASS),
        ]

    import game_state.screen_analyzer as screen_analyzer_module

    monkeypatch.setattr(screen_analyzer_module, "analyze_screen", mock_analyze_screen)

    nearest = find_nearest_tiles(mock_memory_view, TileType.GRASS, max_count=2)

    assert len(nearest) == 2
    # First tile should be closer to center (10, 9)
    assert nearest[0].x == 5 and nearest[0].y == 5


def test_get_movement_options(monkeypatch, mock_memory_view):
    """Test movement option analysis."""

    def mock_analyze_screen(memory_view):
        # Create tiles around player position (center at 10, 9)
        return [
            # Up from player
            create_test_tile_data(
                x=10,
                y=8,
                tile_type=TileType.GRASS,
                is_walkable=True,
                is_encounter_tile=True,
            ),
            # Down from player
            create_test_tile_data(
                x=10, y=10, tile_type=TileType.BLOCKED, is_walkable=False
            ),
            # Left from player
            create_test_tile_data(
                x=9, y=9, tile_type=TileType.WARP, is_walkable=True, is_warp_tile=True
            ),
            # Right from player
            create_test_tile_data(
                x=11, y=9, tile_type=TileType.GRASS, is_walkable=False, has_sign=True
            ),
        ]

    import game_state.screen_analyzer as screen_analyzer_module

    monkeypatch.setattr(screen_analyzer_module, "analyze_screen", mock_analyze_screen)

    movement = get_movement_options(mock_memory_view)

    # Check all directions are present
    assert "up" in movement
    assert "down" in movement
    assert "left" in movement
    assert "right" in movement

    # Check specific properties
    assert movement["up"]["walkable"] is True
    assert movement["up"]["is_encounter"] is True

    assert movement["down"]["walkable"] is False

    assert movement["left"]["walkable"] is True
    assert movement["left"]["is_warp"] is True

    assert movement["right"]["walkable"] is False
    assert movement["right"]["is_interactive"] is True


def test_invalid_memory_state(mock_memory_view):
    """Test handling of invalid memory state."""
    # Mock memory view that raises exceptions
    mock_memory_view.__getitem__.side_effect = ValueError("Invalid memory access")

    categories = categorize_tiles(mock_memory_view)

    # Should return safe defaults
    assert categories["metadata"]["analysis_successful"] is False
    assert categories["metadata"]["current_map"] is None
    assert categories["metadata"]["total_tiles"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
