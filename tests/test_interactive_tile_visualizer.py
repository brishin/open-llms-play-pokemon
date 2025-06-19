"""
Tests for the interactive tile visualizer.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from open_llms_play_pokemon.game_state.tile_data import TileData, TileMatrix, TileType
from open_llms_play_pokemon.game_state.data.tile_data_constants import TilesetID
from open_llms_play_pokemon.visualization.interactive_tile_visualizer import (
    InteractiveTileVisualizer,
)


def create_test_tile_data(
    x: int,
    y: int,
    tile_type: TileType = TileType.WALKABLE,
    has_sign: bool = False,
    has_bookshelf: bool = False,
    strength_boulder: bool = False,
    cuttable_tree: bool = False,
    pc_accessible: bool = False,
    trainer_sight_line: bool = False,
    is_warp_tile: bool = False,
    hidden_item_id: int | None = None,
) -> TileData:
    """Create a test tile data object with specified properties."""
    return TileData(
        tile_id=0x01,
        x=x,
        y=y,
        map_x=x + 100,
        map_y=y + 100,
        tile_type=tile_type,
        tileset_id=TilesetID.OVERWORLD,
        raw_value=0x01,
        is_walkable=True,
        is_ledge_tile=False,
        ledge_direction=None,
        movement_modifier=1.0,
        is_encounter_tile=False,
        is_warp_tile=is_warp_tile,
        is_animated=False,
        light_level=15,
        has_sign=has_sign,
        has_bookshelf=has_bookshelf,
        strength_boulder=strength_boulder,
        cuttable_tree=cuttable_tree,
        pc_accessible=pc_accessible,
        trainer_sight_line=trainer_sight_line,
        trainer_id=None,
        hidden_item_id=hidden_item_id,
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


def create_test_tile_matrix() -> TileMatrix:
    """Create a small test tile matrix with various interactive elements."""
    width, height = 5, 4
    tiles = []
    
    for y in range(height):
        row = []
        for x in range(width):
            # Create different types of interactive tiles for testing
            if x == 0 and y == 0:
                # Sign
                tile = create_test_tile_data(x, y, has_sign=True)
            elif x == 1 and y == 0:
                # Bookshelf  
                tile = create_test_tile_data(x, y, has_bookshelf=True)
            elif x == 2 and y == 0:
                # Strength boulder
                tile = create_test_tile_data(x, y, strength_boulder=True)
            elif x == 3 and y == 0:
                # Cuttable tree
                tile = create_test_tile_data(x, y, cuttable_tree=True)
            elif x == 4 and y == 0:
                # PC
                tile = create_test_tile_data(x, y, pc_accessible=True)
            elif x == 0 and y == 1:
                # NPC
                tile = create_test_tile_data(x, y, tile_type=TileType.NPC)
            elif x == 1 and y == 1:
                # Trainer
                tile = create_test_tile_data(x, y, trainer_sight_line=True)
            elif x == 2 and y == 1:
                # Warp
                tile = create_test_tile_data(x, y, is_warp_tile=True)
            elif x == 3 and y == 1:
                # Hidden item
                tile = create_test_tile_data(x, y, hidden_item_id=42)
            else:
                # Regular walkable tile
                tile = create_test_tile_data(x, y)
            
            row.append(tile)
        tiles.append(row)
    
    return TileMatrix(
        tiles=tiles,
        width=width,
        height=height,
        current_map=1,
        player_x=108,
        player_y=109,
        timestamp=12345,
    )


class TestInteractiveTileVisualizer:
    """Test the interactive tile visualizer."""

    def test_init(self):
        """Test visualizer initialization."""
        visualizer = InteractiveTileVisualizer(tile_size=20)
        assert visualizer.tile_size == 20

    def test_is_interactive_tile(self):
        """Test interactive tile detection."""
        visualizer = InteractiveTileVisualizer()
        
        # Test interactive tiles
        sign_tile = create_test_tile_data(0, 0, has_sign=True)
        assert visualizer._is_interactive_tile(sign_tile)
        
        bookshelf_tile = create_test_tile_data(0, 0, has_bookshelf=True)
        assert visualizer._is_interactive_tile(bookshelf_tile)
        
        npc_tile = create_test_tile_data(0, 0, tile_type=TileType.NPC)
        assert visualizer._is_interactive_tile(npc_tile)
        
        # Test non-interactive tile
        walkable_tile = create_test_tile_data(0, 0)
        assert not visualizer._is_interactive_tile(walkable_tile)

    def test_get_tile_symbol(self):
        """Test tile symbol generation."""
        visualizer = InteractiveTileVisualizer()
        
        # Test interactive symbols
        sign_tile = create_test_tile_data(0, 0, has_sign=True)
        assert visualizer._get_tile_symbol(sign_tile) == "?"
        
        bookshelf_tile = create_test_tile_data(0, 0, has_bookshelf=True)
        assert visualizer._get_tile_symbol(bookshelf_tile) == "B"
        
        npc_tile = create_test_tile_data(0, 0, tile_type=TileType.NPC)
        assert visualizer._get_tile_symbol(npc_tile) == "N"
        
        # Test walkable symbol
        walkable_tile = create_test_tile_data(0, 0)
        assert visualizer._get_tile_symbol(walkable_tile) == "."

    def test_get_tile_color(self):
        """Test tile color assignment."""
        visualizer = InteractiveTileVisualizer()
        
        # Test interactive colors
        sign_tile = create_test_tile_data(0, 0, has_sign=True)
        assert visualizer._get_tile_color(sign_tile, False) == visualizer.COLORS["sign"]
        
        bookshelf_tile = create_test_tile_data(0, 0, has_bookshelf=True)
        assert visualizer._get_tile_color(bookshelf_tile, False) == visualizer.COLORS["bookshelf"]
        
        # Test background for non-interactive when not showing all
        walkable_tile = create_test_tile_data(0, 0)
        assert visualizer._get_tile_color(walkable_tile, False) == visualizer.COLORS["background"]
        
        # Test walkable color when showing all tiles
        assert visualizer._get_tile_color(walkable_tile, True) == visualizer.COLORS["walkable"]

    def test_analyze_interactive_elements(self):
        """Test interactive element analysis."""
        visualizer = InteractiveTileVisualizer()
        tile_matrix = create_test_tile_matrix()
        
        analysis = visualizer.analyze_interactive_elements(tile_matrix)
        
        # Check that we found the expected interactive elements
        assert len(analysis["elements"]["signs"]) == 1
        assert analysis["elements"]["signs"][0] == (0, 0)
        
        assert len(analysis["elements"]["bookshelves"]) == 1
        assert analysis["elements"]["bookshelves"][0] == (1, 0)
        
        assert len(analysis["elements"]["strength_boulders"]) == 1
        assert analysis["elements"]["strength_boulders"][0] == (2, 0)
        
        assert len(analysis["elements"]["cuttable_trees"]) == 1
        assert analysis["elements"]["cuttable_trees"][0] == (3, 0)
        
        assert len(analysis["elements"]["pcs"]) == 1
        assert analysis["elements"]["pcs"][0] == (4, 0)
        
        assert len(analysis["elements"]["npcs"]) == 1
        assert analysis["elements"]["npcs"][0] == (0, 1)
        
        assert len(analysis["elements"]["trainers"]) == 1
        assert analysis["elements"]["trainers"][0] == (1, 1)
        
        assert len(analysis["elements"]["warps"]) == 1
        assert analysis["elements"]["warps"][0] == (2, 1)
        
        assert len(analysis["elements"]["items"]) == 1
        assert analysis["elements"]["items"][0] == (3, 1)
        
        # Check total count
        assert analysis["total_interactive"] == 9

    def test_create_text_map(self):
        """Test text map generation."""
        visualizer = InteractiveTileVisualizer()
        tile_matrix = create_test_tile_matrix()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_map.txt"
            text_map = visualizer.create_text_map(
                tile_matrix, 
                output_path=output_path,
                show_coordinates=True
            )
            
            # Check that file was created
            assert output_path.exists()
            
            # Check content
            assert "?" in text_map  # Sign
            assert "B" in text_map  # Bookshelf
            assert "N" in text_map  # NPC
            assert "." in text_map  # Walkable tiles
            
            # Check coordinate headers
            assert "0 1 2 3 4" in text_map
            assert "0|" in text_map

    def test_visualize_interactive_tiles(self):
        """Test image visualization generation."""
        visualizer = InteractiveTileVisualizer(tile_size=8)
        tile_matrix = create_test_tile_matrix()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_image.png"
            image = visualizer.visualize_interactive_tiles(
                tile_matrix,
                output_path=output_path,
                show_all_tiles=True,
                highlight_player=True
            )
            
            # Check that image was created
            assert output_path.exists()
            
            # Check image properties
            expected_width = tile_matrix.width * 8
            expected_height = tile_matrix.height * 8
            assert image.size == (expected_width, expected_height)

    def test_create_legend(self):
        """Test legend generation."""
        visualizer = InteractiveTileVisualizer()
        legend = visualizer.create_legend()
        
        # Check that legend contains key elements
        assert "Interactive Tile Visualization Legend" in legend
        assert "?" in legend  # Sign symbol
        assert "B" in legend  # Bookshelf symbol
        assert "Yellow - Signs" in legend  # Color description
        assert "Brown - Bookshelves" in legend  # Color description

    def test_visualize_interactive_tiles_no_player_highlight(self):
        """Test visualization without player highlighting."""
        visualizer = InteractiveTileVisualizer()
        tile_matrix = create_test_tile_matrix()
        
        image = visualizer.visualize_interactive_tiles(
            tile_matrix,
            highlight_player=False
        )
        
        # Should still create an image
        assert image is not None
        expected_width = tile_matrix.width * visualizer.tile_size
        expected_height = tile_matrix.height * visualizer.tile_size
        assert image.size == (expected_width, expected_height)

    def test_visualize_interactive_tiles_only_interactive(self):
        """Test visualization showing only interactive tiles."""
        visualizer = InteractiveTileVisualizer()
        tile_matrix = create_test_tile_matrix()
        
        image = visualizer.visualize_interactive_tiles(
            tile_matrix,
            show_all_tiles=False
        )
        
        # Should still create an image
        assert image is not None
        expected_width = tile_matrix.width * visualizer.tile_size
        expected_height = tile_matrix.height * visualizer.tile_size
        assert image.size == (expected_width, expected_height)