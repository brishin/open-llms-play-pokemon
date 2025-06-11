"""
Unified Tile Data System for Pokemon Red

This module provides structured tile data that combines visual information,
collision properties, and position data into serializable formats.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union
import json

# Try to import numpy for matrix operations
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class TileType(Enum):
    """Categories of tiles based on their game function."""
    UNKNOWN = "unknown"
    WALKABLE = "walkable"
    BLOCKED = "blocked"
    GRASS = "grass"
    WATER = "water"
    WARP = "warp"
    LEDGE = "ledge"
    BUILDING = "building"
    ROAD = "road"
    TREE = "tree"
    ROCK = "rock"
    NPC = "npc"
    ITEM = "item"


@dataclass(frozen=True)
class TileData:
    """
    Unified tile data structure containing all known information about a tile.
    
    Attributes:
        tile_id: PyBoy tile identifier (0-383)
        x: X coordinate in the game area matrix
        y: Y coordinate in the game area matrix
        map_x: Absolute X coordinate on the current map
        map_y: Absolute Y coordinate on the current map
        tile_type: Categorized tile type based on function
        is_walkable: Whether the player can walk through this tile
        is_encounter_tile: Whether this tile can trigger wild Pokemon encounters
        is_warp_tile: Whether this tile is a warp/door entrance
        sprite_offset: Additional offset if this tile contains a sprite
        raw_value: Raw tile value before any mapping transformations
    """
    tile_id: int
    x: int
    y: int
    map_x: int
    map_y: int
    tile_type: TileType
    is_walkable: bool
    is_encounter_tile: bool
    is_warp_tile: bool
    sprite_offset: int
    raw_value: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'tile_id': self.tile_id,
            'x': self.x,
            'y': self.y,
            'map_x': self.map_x,
            'map_y': self.map_y,
            'tile_type': self.tile_type.value,
            'is_walkable': self.is_walkable,
            'is_encounter_tile': self.is_encounter_tile,
            'is_warp_tile': self.is_warp_tile,
            'sprite_offset': self.sprite_offset,
            'raw_value': self.raw_value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TileData':
        """Create TileData from dictionary."""
        return cls(
            tile_id=data['tile_id'],
            x=data['x'],
            y=data['y'],
            map_x=data['map_x'],
            map_y=data['map_y'],
            tile_type=TileType(data['tile_type']),
            is_walkable=data['is_walkable'],
            is_encounter_tile=data['is_encounter_tile'],
            is_warp_tile=data['is_warp_tile'],
            sprite_offset=data['sprite_offset'],
            raw_value=data['raw_value']
        )


@dataclass
class TileMatrix:
    """
    Complete tile data matrix for a game area.
    
    Attributes:
        tiles: 2D matrix of TileData objects
        width: Width of the matrix
        height: Height of the matrix
        current_map: Map ID where this data was captured
        player_x: Player's X position when data was captured
        player_y: Player's Y position when data was captured
        timestamp: When this data was captured (frame count or timestamp)
    """
    tiles: List[List[TileData]]
    width: int
    height: int
    current_map: int
    player_x: int
    player_y: int
    timestamp: Optional[int] = None

    def get_tile(self, x: int, y: int) -> Optional[TileData]:
        """Get tile data at specific coordinates."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.tiles[y][x]
        return None
    
    def get_walkable_tiles(self) -> List[TileData]:
        """Get all walkable tiles in the matrix."""
        walkable = []
        for row in self.tiles:
            for tile in row:
                if tile.is_walkable:
                    walkable.append(tile)
        return walkable
    
    def get_tiles_by_type(self, tile_type: TileType) -> List[TileData]:
        """Get all tiles of a specific type."""
        matching = []
        for row in self.tiles:
            for tile in row:
                if tile.tile_type == tile_type:
                    matching.append(tile)
        return matching
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'tiles': [[tile.to_dict() for tile in row] for row in self.tiles],
            'width': self.width,
            'height': self.height,
            'current_map': self.current_map,
            'player_x': self.player_x,
            'player_y': self.player_y,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TileMatrix':
        """Create TileMatrix from dictionary."""
        tiles = [[TileData.from_dict(tile_data) for tile_data in row] 
                 for row in data['tiles']]
        return cls(
            tiles=tiles,
            width=data['width'],
            height=data['height'],
            current_map=data['current_map'],
            player_x=data['player_x'],
            player_y=data['player_y'],
            timestamp=data.get('timestamp')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TileMatrix':
        """Create TileMatrix from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def get_tile_id_matrix(self):
        """Get a simple 2D numpy array of just tile IDs for compatibility."""
        if not NUMPY_AVAILABLE:
            # Return as nested lists if numpy is not available
            return [[tile.tile_id for tile in row] for row in self.tiles]
        
        return np.array([[tile.tile_id for tile in row] for row in self.tiles], dtype=np.uint32)
    
    def get_walkability_matrix(self):
        """Get a boolean matrix indicating walkable tiles."""
        if not NUMPY_AVAILABLE:
            # Return as nested lists if numpy is not available
            return [[tile.is_walkable for tile in row] for row in self.tiles]
        
        return np.array([[tile.is_walkable for tile in row] for row in self.tiles], dtype=bool)
    
    def get_encounter_matrix(self):
        """Get a boolean matrix indicating encounter tiles."""
        if not NUMPY_AVAILABLE:
            # Return as nested lists if numpy is not available
            return [[tile.is_encounter_tile for tile in row] for row in self.tiles]
        
        return np.array([[tile.is_encounter_tile for tile in row] for row in self.tiles], dtype=bool)


# Known collision data from Pokemon Red symbols
COLLISION_TABLES = {
    # Tileset ID -> set of walkable tile IDs (these would need to be populated from actual game data)
    0: {32, 33, 34, 35, 36, 37, 38, 39},  # Overworld - example walkable tiles
    1: {20, 21, 22, 23, 24},  # Red's House - example
    2: {15, 16, 17, 18, 19},  # Pokemon Center - example
    3: {40, 41, 42, 43, 44},  # Viridian Forest - example
    # Add more tilesets as needed
}

# Known special tile mappings (these would need to be determined from game analysis)
GRASS_TILES = {42, 43, 44}  # Example grass tile IDs
WATER_TILES = {60, 61, 62, 63}  # Example water tile IDs
WARP_TILES = {80, 81, 82}  # Example door/warp tile IDs
LEDGE_TILES = {90, 91, 92}  # Example ledge tile IDs


def classify_tile_type(tile_id: int, is_walkable: bool, tileset_id: int = 0) -> TileType:
    """
    Classify a tile based on its ID and properties.
    
    Args:
        tile_id: The tile identifier
        is_walkable: Whether the tile is walkable
        tileset_id: Current tileset ID for context
        
    Returns:
        TileType classification
    """
    if tile_id in GRASS_TILES:
        return TileType.GRASS
    elif tile_id in WATER_TILES:
        return TileType.WATER
    elif tile_id in WARP_TILES:
        return TileType.WARP
    elif tile_id in LEDGE_TILES:
        return TileType.LEDGE
    elif is_walkable:
        # Further classify walkable tiles
        if 20 <= tile_id <= 30:  # Example road tile range
            return TileType.ROAD
        else:
            return TileType.WALKABLE
    else:
        # Classify blocked tiles
        if 100 <= tile_id <= 120:  # Example tree tile range
            return TileType.TREE
        elif 150 <= tile_id <= 170:  # Example rock tile range
            return TileType.ROCK
        elif 200 <= tile_id <= 220:  # Example building tile range
            return TileType.BUILDING
        else:
            return TileType.BLOCKED
    
    return TileType.UNKNOWN


def is_tile_walkable(tile_id: int, tileset_id: int = 0) -> bool:
    """
    Determine if a tile is walkable based on collision tables.
    
    Args:
        tile_id: The tile identifier
        tileset_id: Current tileset ID
        
    Returns:
        True if walkable, False if blocked
    """
    collision_table = COLLISION_TABLES.get(tileset_id, set())
    return tile_id in collision_table