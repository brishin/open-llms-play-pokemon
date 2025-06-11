"""Tests for the unified tile data system."""

from open_llms_play_pokemon.game_state.tile_data import (
    TileType,
    classify_tile_type,
    is_tile_walkable,
)


def test_tile_type_classification():
    """Test tile type classification system."""

    # Test different tile classifications
    grass_type = classify_tile_type(42, True, 0)  # 42 is in GRASS_TILES
    assert grass_type == TileType.GRASS

    walkable_type = classify_tile_type(25, True, 0)  # Road tile range
    assert walkable_type == TileType.ROAD

    blocked_type = classify_tile_type(110, False, 0)  # Tree tile range
    assert blocked_type == TileType.TREE

    unknown_type = classify_tile_type(999, False, 0)  # Unknown tile
    assert unknown_type == TileType.BLOCKED

    print("✓ Tile type classification test passed")


def test_collision_detection():
    """Test collision detection system."""

    # Test walkable tiles (these are in the example collision table)
    assert is_tile_walkable(32, 0)  # In overworld collision table
    assert is_tile_walkable(33, 0)

    # Test non-walkable tiles
    assert not is_tile_walkable(999, 0)  # Not in collision table

    # Test different tilesets
    assert is_tile_walkable(20, 1)  # In Red's House collision table
    assert not is_tile_walkable(20, 0)  # Not in overworld collision table
