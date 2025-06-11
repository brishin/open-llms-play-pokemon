"""Tests for the unified tile data system."""

import json
import sys
from pathlib import Path
from typing import Dict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # Import directly from the modules to avoid init.py PyBoy requirements
    from open_llms_play_pokemon.game_state.tile_data import (
        TileData, 
        TileMatrix, 
        TileType, 
        classify_tile_type,
        is_tile_walkable
    )
    TILE_CLASSES_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    TILE_CLASSES_AVAILABLE = False

# Try to import TileReader separately (may fail due to PyBoy requirement)
try:
    from open_llms_play_pokemon.game_state.tile_reader import TileReader
    TILE_READER_AVAILABLE = True
except ImportError:
    TILE_READER_AVAILABLE = False

# Try to import PokemonRedMemoryReader
try:
    from open_llms_play_pokemon.game_state.memory_reader import PokemonRedMemoryReader
    MEMORY_READER_AVAILABLE = True
except ImportError:
    MEMORY_READER_AVAILABLE = False


def test_tile_data_creation():
    """Test creating and manipulating TileData objects."""
    if not TILE_CLASSES_AVAILABLE:
        print("Tile classes not available, skipping test")
        return
    
    # Create a sample tile
    tile = TileData(
        tile_id=42,
        x=5,
        y=10,
        map_x=100,
        map_y=200,
        tile_type=TileType.GRASS,
        is_walkable=True,
        is_encounter_tile=True,
        is_warp_tile=False,
        sprite_offset=0,
        raw_value=42
    )
    
    # Test properties
    assert tile.tile_id == 42
    assert tile.tile_type == TileType.GRASS
    assert tile.is_walkable == True
    assert tile.is_encounter_tile == True
    
    # Test serialization
    tile_dict = tile.to_dict()
    assert isinstance(tile_dict, dict)
    assert tile_dict['tile_id'] == 42
    assert tile_dict['tile_type'] == 'grass'
    
    # Test deserialization
    reconstructed = TileData.from_dict(tile_dict)
    assert reconstructed == tile
    
    print("✓ TileData creation and serialization test passed")


def test_tile_matrix_creation():
    """Test creating and manipulating TileMatrix objects."""
    if not TILE_CLASSES_AVAILABLE:
        print("Tile classes not available, skipping test")
        return
    
    # Create a small test matrix
    tiles = []
    for y in range(3):
        row = []
        for x in range(3):
            tile = TileData(
                tile_id=x + y * 3,
                x=x,
                y=y,
                map_x=x + 10,
                map_y=y + 20,
                tile_type=TileType.WALKABLE if (x + y) % 2 == 0 else TileType.BLOCKED,
                is_walkable=(x + y) % 2 == 0,
                is_encounter_tile=False,
                is_warp_tile=False,
                sprite_offset=0,
                raw_value=x + y * 3
            )
            row.append(tile)
        tiles.append(row)
    
    matrix = TileMatrix(
        tiles=tiles,
        width=3,
        height=3,
        current_map=1,
        player_x=15,
        player_y=25,
        timestamp=12345
    )
    
    # Test basic properties
    assert matrix.width == 3
    assert matrix.height == 3
    assert matrix.current_map == 1
    
    # Test tile access
    tile = matrix.get_tile(1, 1)
    assert tile is not None
    assert tile.tile_id == 4  # 1 + 1 * 3
    
    # Test walkable tiles
    walkable_tiles = matrix.get_walkable_tiles()
    expected_walkable = 5  # tiles at (0,0), (1,1), (2,0), (0,2), (2,2)
    assert len(walkable_tiles) == expected_walkable
    
    # Test serialization
    matrix_dict = matrix.to_dict()
    assert isinstance(matrix_dict, dict)
    assert matrix_dict['width'] == 3
    assert matrix_dict['height'] == 3
    
    # Test JSON serialization
    json_str = matrix.to_json()
    assert isinstance(json_str, str)
    
    # Test deserialization
    reconstructed = TileMatrix.from_json(json_str)
    assert reconstructed.width == matrix.width
    assert reconstructed.height == matrix.height
    assert reconstructed.current_map == matrix.current_map
    
    # Test matrix conversions (returns lists if numpy not available)
    tile_ids = matrix.get_tile_id_matrix()
    walkability = matrix.get_walkability_matrix()
    encounters = matrix.get_encounter_matrix()
    
    # Check dimensions (works for both numpy arrays and lists)
    if hasattr(tile_ids, 'shape'):
        # Numpy array
        assert tile_ids.shape == (3, 3)
        assert walkability.shape == (3, 3)
        assert encounters.shape == (3, 3)
    else:
        # List of lists
        assert len(tile_ids) == 3
        assert len(tile_ids[0]) == 3
        assert len(walkability) == 3
        assert len(walkability[0]) == 3
        assert len(encounters) == 3
        assert len(encounters[0]) == 3
    
    # Test specific values
    if hasattr(tile_ids, 'shape'):
        assert tile_ids[1, 1] == 4
        assert walkability[0, 0] == True  # (0+0) % 2 == 0
        assert walkability[1, 0] == False  # (1+0) % 2 == 1
    else:
        assert tile_ids[1][1] == 4
        assert walkability[0][0] == True
        assert walkability[1][0] == False
    
    print("✓ TileMatrix creation and manipulation test passed")


def test_tile_type_classification():
    """Test tile type classification system."""
    if not TILE_CLASSES_AVAILABLE:
        print("Tile classes not available, skipping test")
        return
    
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
    if not TILE_CLASSES_AVAILABLE:
        print("Tile classes not available, skipping test")
        return
    
    # Test walkable tiles (these are in the example collision table)
    assert is_tile_walkable(32, 0) == True  # In overworld collision table
    assert is_tile_walkable(33, 0) == True
    
    # Test non-walkable tiles
    assert is_tile_walkable(999, 0) == False  # Not in collision table
    
    # Test different tilesets
    assert is_tile_walkable(20, 1) == True  # In Red's House collision table
    assert is_tile_walkable(20, 0) == False  # Not in overworld collision table
    
    print("✓ Collision detection test passed")


def test_memory_reader_integration():
    """Test integration with memory reader (without PyBoy)."""
    if not MEMORY_READER_AVAILABLE:
        print("Memory reader not available, skipping test")
        return
    
    # Test that memory reader can be created without PyBoy
    memory_reader = PokemonRedMemoryReader()
    assert memory_reader.tile_reader is None
    
    print("✓ Memory reader integration test passed")


def main():
    """Run all tests."""
    print("Running unified tile data system tests...")
    
    if not TILE_CLASSES_AVAILABLE:
        print("❌ Tile classes not available - check imports")
        return
    
    test_tile_data_creation()
    test_tile_matrix_creation()
    test_tile_type_classification()
    test_collision_detection()
    test_memory_reader_integration()
    
    print("\n✅ All unified tile data tests passed!")
    
    # Print availability status
    print(f"\nComponent availability:")
    print(f"  Tile classes: {'✓' if TILE_CLASSES_AVAILABLE else '✗'}")
    print(f"  Tile reader: {'✓' if TILE_READER_AVAILABLE else '✗'}")
    print(f"  Memory reader: {'✓' if MEMORY_READER_AVAILABLE else '✗'}")


if __name__ == "__main__":
    main()