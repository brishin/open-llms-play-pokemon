"""Tests for the unified tile data system."""

from open_llms_play_pokemon.game_state.data.tile_data_constants import TilesetID
from open_llms_play_pokemon.game_state.tile_data import (
    TileType,
    classify_tile_type,
    is_tile_walkable,
)


def test_tile_type_classification():
    """Test tile type classification system."""

    # Test different tile classifications using actual pokered values
    grass_type = classify_tile_type(
        0x52, True, TilesetID.OVERWORLD
    )  # 0x52 is in GRASS_TILES for OVERWORLD
    assert grass_type == TileType.GRASS

    walkable_type = classify_tile_type(25, True, TilesetID.OVERWORLD)  # Road tile range
    assert walkable_type == TileType.ROAD

    tree_type = classify_tile_type(
        0x3D, False, TilesetID.OVERWORLD
    )  # 0x3d is in TREE_TILES for OVERWORLD
    assert tree_type == TileType.TREE

    unknown_type = classify_tile_type(999, False, TilesetID.OVERWORLD)  # Unknown tile
    assert unknown_type == TileType.BLOCKED

    print("✓ Tile type classification test passed")


def test_collision_detection():
    """Test collision detection system."""

    # Test walkable tiles using actual pokered collision data
    assert is_tile_walkable(
        0x00, TilesetID.OVERWORLD
    )  # 0x00 is in overworld collision table
    assert is_tile_walkable(
        0x10, TilesetID.OVERWORLD
    )  # 0x10 is in overworld collision table

    # Test non-walkable tiles
    assert not is_tile_walkable(999, TilesetID.OVERWORLD)  # Not in collision table

    # Test different tilesets
    assert is_tile_walkable(
        0x01, TilesetID.REDS_HOUSE_1
    )  # 0x01 is in Red's House collision table
    assert not is_tile_walkable(
        0x01, TilesetID.OVERWORLD
    )  # 0x01 is not in overworld collision table
