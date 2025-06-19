"""
Interactive Tile Visualization System

This module provides visualization tools for displaying interactive tiles in Pokemon Red,
helping developers and AI agents understand the game's interactive elements at a glance.
"""

from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from ..game_state.tile_data import TileData, TileMatrix


class InteractiveTileVisualizer:
    """Visualizes interactive tiles in Pokemon Red game screens."""

    # Color scheme for different interactive elements
    COLORS = {
        "background": (32, 32, 32),      # Dark gray background
        "walkable": (64, 64, 64),        # Darker gray for walkable tiles
        "blocked": (16, 16, 16),         # Very dark for blocked tiles
        "sign": (255, 255, 0),           # Yellow for signs
        "bookshelf": (139, 69, 19),      # Brown for bookshelves
        "strength_boulder": (128, 128, 128),  # Gray for strength boulders
        "cuttable_tree": (34, 139, 34),  # Forest green for cuttable trees
        "pc_accessible": (0, 191, 255),  # Deep sky blue for PCs
        "npc": (255, 105, 180),          # Hot pink for NPCs
        "trainer": (255, 0, 0),          # Red for trainers
        "warp": (138, 43, 226),          # Blue violet for warps/doors
        "item": (255, 215, 0),           # Gold for items
        "grass": (50, 205, 50),          # Lime green for encounter grass
        "water": (0, 100, 200),          # Blue for water
        "ledge": (210, 180, 140),        # Tan for ledges
        "player": (255, 255, 255),       # White for player position
    }

    # Symbols for text representation
    SYMBOLS = {
        "walkable": ".",
        "blocked": "#",
        "sign": "?",
        "bookshelf": "B",
        "strength_boulder": "O",
        "cuttable_tree": "T",
        "pc_accessible": "P",
        "npc": "N",
        "trainer": "!",
        "warp": "W",
        "item": "$",
        "grass": "~",
        "water": "≈",
        "ledge": "^",
        "player": "@",
        "unknown": " ",
    }

    def __init__(self, tile_size: int = 16):
        """
        Initialize the visualizer.
        
        Args:
            tile_size: Size of each tile in pixels for image output
        """
        self.tile_size = tile_size

    def visualize_interactive_tiles(
        self,
        tile_matrix: TileMatrix,
        output_path: Optional[Path] = None,
        show_all_tiles: bool = False,
        highlight_player: bool = True,
    ) -> Image.Image:
        """
        Create a visual representation of interactive tiles.
        
        Args:
            tile_matrix: The tile matrix to visualize
            output_path: Optional path to save the image
            show_all_tiles: If True, show all tiles with base colors. If False, only highlight interactive ones.
            highlight_player: If True, highlight the player position
        
        Returns:
            PIL Image object of the visualization
        """
        width = tile_matrix.width * self.tile_size
        height = tile_matrix.height * self.tile_size
        
        # Create image with background color
        image = Image.new("RGB", (width, height), self.COLORS["background"])
        draw = ImageDraw.Draw(image)
        
        # Draw tiles
        for y in range(tile_matrix.height):
            for x in range(tile_matrix.width):
                tile = tile_matrix.tiles[y][x]
                
                # Calculate pixel coordinates
                pixel_x = x * self.tile_size
                pixel_y = y * self.tile_size
                
                # Determine tile color based on properties
                color = self._get_tile_color(tile, show_all_tiles)
                
                # Draw tile rectangle
                draw.rectangle(
                    [pixel_x, pixel_y, pixel_x + self.tile_size - 1, pixel_y + self.tile_size - 1],
                    fill=color
                )
                
                # Add border for interactive tiles
                if self._is_interactive_tile(tile):
                    draw.rectangle(
                        [pixel_x, pixel_y, pixel_x + self.tile_size - 1, pixel_y + self.tile_size - 1],
                        outline=(255, 255, 255),
                        width=1
                    )
        
        # Highlight player position if requested
        if highlight_player:
            # Player is typically at screen position (8,9) to (9,10) - 2x2 tiles
            player_x, player_y = 8, 9
            pixel_x = player_x * self.tile_size
            pixel_y = player_y * self.tile_size
            
            # Draw player indicator (2x2 tiles)
            draw.rectangle(
                [pixel_x, pixel_y, pixel_x + (self.tile_size * 2) - 1, pixel_y + (self.tile_size * 2) - 1],
                outline=self.COLORS["player"],
                width=2
            )
        
        # Save image if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path)
        
        return image

    def create_text_map(
        self,
        tile_matrix: TileMatrix,
        output_path: Optional[Path] = None,
        show_coordinates: bool = True,
    ) -> str:
        """
        Create a text-based representation of interactive tiles.
        
        Args:
            tile_matrix: The tile matrix to visualize
            output_path: Optional path to save the text file
            show_coordinates: If True, include coordinate headers
        
        Returns:
            String representation of the tile map
        """
        lines = []
        
        if show_coordinates:
            # Add column headers
            header = "   " + "".join(f"{x:2}" for x in range(tile_matrix.width))
            lines.append(header)
            lines.append("   " + "--" * tile_matrix.width)
        
        # Add rows
        for y in range(tile_matrix.height):
            row_chars = []
            for x in range(tile_matrix.width):
                tile = tile_matrix.tiles[y][x]
                symbol = self._get_tile_symbol(tile)
                row_chars.append(symbol)
            
            row_str = "".join(row_chars)
            if show_coordinates:
                row_str = f"{y:2}|" + row_str
            lines.append(row_str)
        
        text_map = "\n".join(lines)
        
        # Save text file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text_map)
        
        return text_map

    def create_legend(self) -> str:
        """
        Create a legend explaining the symbols and colors used.
        
        Returns:
            String containing the legend
        """
        legend_lines = [
            "Interactive Tile Visualization Legend",
            "=" * 40,
            "",
            "Text Symbols:",
        ]
        
        # Add symbol explanations
        symbol_descriptions = {
            "?": "Sign (readable)",
            "B": "Bookshelf (readable)",
            "O": "Strength Boulder (movable with Strength)",
            "T": "Cuttable Tree (cuttable with Cut)",
            "P": "PC (accessible)",
            "N": "NPC (talkable)",
            "!": "Trainer (will battle)",
            "W": "Warp/Door (enterable)",
            "$": "Item (pickupable)",
            "~": "Grass (Pokemon encounters)",
            "≈": "Water (surfable)",
            "^": "Ledge (jumpable)",
            "@": "Player position",
            ".": "Walkable tile",
            "#": "Blocked tile",
        }
        
        for symbol, description in symbol_descriptions.items():
            legend_lines.append(f"  {symbol} - {description}")
        
        legend_lines.extend([
            "",
            "Colors (for image output):",
            "  Yellow - Signs",
            "  Brown - Bookshelves", 
            "  Gray - Strength Boulders",
            "  Green - Cuttable Trees",
            "  Blue - PCs",
            "  Pink - NPCs",
            "  Red - Trainers",
            "  Purple - Warps/Doors",
            "  Gold - Items",
            "  Lime - Grass",
            "  Blue - Water",
            "  Tan - Ledges",
            "  White - Player",
        ])
        
        return "\n".join(legend_lines)

    def analyze_interactive_elements(self, tile_matrix: TileMatrix) -> dict:
        """
        Analyze and count interactive elements in the tile matrix.
        
        Args:
            tile_matrix: The tile matrix to analyze
            
        Returns:
            Dictionary with counts and locations of interactive elements
        """
        analysis = {
            "total_interactive": 0,
            "elements": {
                "signs": [],
                "bookshelves": [],
                "strength_boulders": [],
                "cuttable_trees": [],
                "pcs": [],
                "npcs": [],
                "trainers": [],
                "warps": [],
                "items": [],
                "grass": [],
                "water": [],
                "ledges": [],
            }
        }
        
        for y in range(tile_matrix.height):
            for x in range(tile_matrix.width):
                tile = tile_matrix.tiles[y][x]
                
                # Check each type of interactive element
                if tile.has_sign:
                    analysis["elements"]["signs"].append((x, y))
                if tile.has_bookshelf:
                    analysis["elements"]["bookshelves"].append((x, y))
                if tile.strength_boulder:
                    analysis["elements"]["strength_boulders"].append((x, y))
                if tile.cuttable_tree:
                    analysis["elements"]["cuttable_trees"].append((x, y))
                if tile.pc_accessible:
                    analysis["elements"]["pcs"].append((x, y))
                if tile.tile_type.value == "npc":
                    analysis["elements"]["npcs"].append((x, y))
                if tile.trainer_sight_line:
                    analysis["elements"]["trainers"].append((x, y))
                if tile.is_warp_tile:
                    analysis["elements"]["warps"].append((x, y))
                if tile.hidden_item_id is not None:
                    analysis["elements"]["items"].append((x, y))
                if tile.is_encounter_tile:
                    analysis["elements"]["grass"].append((x, y))
                if tile.tile_type.value == "water":
                    analysis["elements"]["water"].append((x, y))
                if tile.is_ledge_tile:
                    analysis["elements"]["ledges"].append((x, y))
        
        # Count total interactive elements
        for element_list in analysis["elements"].values():
            analysis["total_interactive"] += len(element_list)
        
        return analysis

    def _get_tile_color(self, tile: TileData, show_all_tiles: bool) -> tuple[int, int, int]:
        """Get the color for a tile based on its properties."""
        # Priority order: interactive elements first, then basic tile types
        
        # Interactive elements (highest priority)
        if tile.has_sign:
            return self.COLORS["sign"]
        if tile.has_bookshelf:
            return self.COLORS["bookshelf"]
        if tile.strength_boulder:
            return self.COLORS["strength_boulder"]
        if tile.cuttable_tree:
            return self.COLORS["cuttable_tree"]
        if tile.pc_accessible:
            return self.COLORS["pc_accessible"]
        if tile.tile_type.value == "npc":
            return self.COLORS["npc"]
        if tile.trainer_sight_line:
            return self.COLORS["trainer"]
        if tile.is_warp_tile:
            return self.COLORS["warp"]
        if tile.hidden_item_id is not None:
            return self.COLORS["item"]
        
        # Environmental elements (if showing all tiles)
        if show_all_tiles:
            if tile.is_encounter_tile:
                return self.COLORS["grass"]
            if tile.tile_type.value == "water":
                return self.COLORS["water"]
            if tile.is_ledge_tile:
                return self.COLORS["ledge"]
            if tile.is_walkable:
                return self.COLORS["walkable"]
            else:
                return self.COLORS["blocked"]
        
        # Default background for non-interactive elements when not showing all
        return self.COLORS["background"]

    def _get_tile_symbol(self, tile: TileData) -> str:
        """Get the text symbol for a tile based on its properties."""
        # Priority order: interactive elements first, then basic tile types
        
        if tile.has_sign:
            return self.SYMBOLS["sign"]
        if tile.has_bookshelf:
            return self.SYMBOLS["bookshelf"]
        if tile.strength_boulder:
            return self.SYMBOLS["strength_boulder"]
        if tile.cuttable_tree:
            return self.SYMBOLS["cuttable_tree"]
        if tile.pc_accessible:
            return self.SYMBOLS["pc_accessible"]
        if tile.tile_type.value == "npc":
            return self.SYMBOLS["npc"]
        if tile.trainer_sight_line:
            return self.SYMBOLS["trainer"]
        if tile.is_warp_tile:
            return self.SYMBOLS["warp"]
        if tile.hidden_item_id is not None:
            return self.SYMBOLS["item"]
        if tile.is_encounter_tile:
            return self.SYMBOLS["grass"]
        if tile.tile_type.value == "water":
            return self.SYMBOLS["water"]
        if tile.is_ledge_tile:
            return self.SYMBOLS["ledge"]
        if tile.is_walkable:
            return self.SYMBOLS["walkable"]
        elif not tile.is_walkable:
            return self.SYMBOLS["blocked"]
        
        return self.SYMBOLS["unknown"]

    def _is_interactive_tile(self, tile: TileData) -> bool:
        """Check if a tile has any interactive properties."""
        return (
            tile.has_sign
            or tile.has_bookshelf
            or tile.strength_boulder
            or tile.cuttable_tree
            or tile.pc_accessible
            or tile.tile_type.value == "npc"
            or tile.trainer_sight_line
            or tile.is_warp_tile
            or tile.hidden_item_id is not None
        )