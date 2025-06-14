"""Tests for enhanced tile creator system."""

from unittest.mock import MagicMock, Mock

import pytest
from game_state.data.tile_data_constants import TilesetID
from game_state.enhanced_tile_creator import (
    create_tile_data,
    detect_environmental_properties,
    detect_interaction_properties,
    detect_ledge_info,
)
from game_state.tile_data import TileType


def test_detect_ledge_info():
    """Test ledge detection using pokered ledge data."""
    # Test a known ledge tile from LEDGE_DATA (0x37 - down ledge)
    direction, is_ledge = detect_ledge_info(TilesetID.OVERWORLD, 0x37)
    assert is_ledge is True
    assert direction == "down"

    # Test non-ledge tile
    direction, is_ledge = detect_ledge_info(TilesetID.OVERWORLD, 0xFF)
    assert is_ledge is False
    assert direction is None


def test_detect_interaction_properties():
    """Test interaction property detection."""
    # Test sign tile
    interactions = detect_interaction_properties(TilesetID.OVERWORLD, 0x5A)
    assert interactions["has_sign"] is True
    assert interactions["has_bookshelf"] is False

    # Test tree tile
    interactions = detect_interaction_properties(TilesetID.OVERWORLD, 0x3D)
    assert interactions["cuttable_tree"] is True
    assert interactions["has_sign"] is False


def test_detect_environmental_properties():
    """Test environmental property detection."""
    # Test grass tile (encounter)
    env_props = detect_environmental_properties(TilesetID.OVERWORLD, 0x52)
    assert env_props["is_encounter"] is True
    assert env_props["is_warp"] is False

    # Test door tile (warp)
    env_props = detect_environmental_properties(TilesetID.OVERWORLD, 0x1B)
    assert env_props["is_warp"] is True
    assert env_props["is_encounter"] is False


def test_create_tile_data_integration(monkeypatch):
    """Test create_tile_data function with mocked memory view."""
    # Create mock memory view
    memory_view = Mock()
    memory_view.__getitem__ = MagicMock()

    # Mock memory addresses
    memory_view.__getitem__.side_effect = lambda addr: {
        0xD367: 0,  # current_tileset = OVERWORLD
        0xD362: 10,  # x_coord = 10
        0xD361: 10,  # y_coord = 10
        0xD36A: 0,  # map_loading_status = stable
        0xC3A0: 0x52,  # tile_map_buffer + 0 = grass tile
    }.get(addr, 0)

    # Mock the tile reader functions using monkeypatch
    def mock_get_tile_id(memory_view, x, y):
        return 0x52  # Grass tile

    def mock_get_map_coordinates(memory_view, screen_x, screen_y):
        return (10, 10)

    def mock_get_sprite_at_position(memory_view, screen_x, screen_y):
        return 0  # No sprite

    def mock_is_collision_tile(memory_view, tile_id):
        return False  # Walkable

    # Apply mocks using monkeypatch
    import game_state.enhanced_tile_creator as enhanced_tile_creator_module

    monkeypatch.setattr(enhanced_tile_creator_module, "get_tile_id", mock_get_tile_id)
    monkeypatch.setattr(
        enhanced_tile_creator_module, "get_map_coordinates", mock_get_map_coordinates
    )
    monkeypatch.setattr(
        enhanced_tile_creator_module,
        "get_sprite_at_position",
        mock_get_sprite_at_position,
    )
    monkeypatch.setattr(
        enhanced_tile_creator_module, "is_collision_tile", mock_is_collision_tile
    )

    # Test create_tile_data
    tile_data = create_tile_data(memory_view, 0, 0)

    # Verify basic properties
    assert tile_data.tile_id == 0x52
    assert tile_data.x == 0
    assert tile_data.y == 0
    assert tile_data.map_x == 10
    assert tile_data.map_y == 10
    assert tile_data.tileset_id == TilesetID.OVERWORLD
    assert tile_data.is_walkable is True
    assert tile_data.is_encounter_tile is True  # Grass tile
    assert tile_data.tile_type == TileType.GRASS


if __name__ == "__main__":
    pytest.main([__file__])
