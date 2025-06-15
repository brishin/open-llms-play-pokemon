"""
Unified Tile Data System for Pokemon Red

This module provides structured tile data that combines visual information,
collision properties, and position data into serializable formats.
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum

import numpy as np

from .data.tile_data_constants import (
    COLLISION_TABLES,
    DOOR_TILES,
    GRASS_TILES,
    LEDGE_TILES,
    TREE_TILES,
    WATER_TILES,
    TilesetID,
)


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


@dataclass(slots=True, frozen=True)
class TileData:
    """
    Enhanced tile data structure containing comprehensive information about a tile.

    This structure provides 30+ properties covering all aspects of Pokemon Red tiles
    including collision, interaction, animation, and special behaviors.
    """

    # Basic Identification
    tile_id: int
    x: int
    y: int
    map_x: int
    map_y: int
    tile_type: TileType
    tileset_id: TilesetID
    raw_value: int

    # Movement/Collision
    is_walkable: bool
    is_ledge_tile: bool
    ledge_direction: str | None  # "down", "left", "right", "up"
    movement_modifier: float  # Speed multiplier (1.0 = normal)

    # Environmental
    is_encounter_tile: bool
    is_warp_tile: bool
    is_animated: bool
    light_level: int  # 0-15, for caves/buildings

    # Interactions
    has_sign: bool
    has_bookshelf: bool
    strength_boulder: bool
    cuttable_tree: bool
    pc_accessible: bool

    # Battle System
    trainer_sight_line: bool
    trainer_id: int | None
    hidden_item_id: int | None
    requires_itemfinder: bool

    # Special Zones
    safari_zone_steps: bool
    game_corner_tile: bool
    is_fly_destination: bool

    # Audio/Visual
    has_footstep_sound: bool
    sprite_priority: int  # 0-3, sprite layer priority
    background_priority: int  # 0-3, background layer priority
    elevation_pair: int | None  # Paired tile ID for height differences

    # Additional Properties
    sprite_offset: int
    blocks_light: bool
    water_current_direction: str | None  # For surfing mechanics
    warp_destination_map: int | None
    warp_destination_x: int | None
    warp_destination_y: int | None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["tile_type"] = self.tile_type.value  # Handle enum serialization
        data["tileset_id"] = int(self.tileset_id)  # Handle IntEnum serialization
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "TileData":
        """Create TileData from dictionary."""
        data = data.copy()
        data["tile_type"] = TileType(data["tile_type"])  # Convert enum back
        data["tileset_id"] = TilesetID(data["tileset_id"])  # Convert IntEnum back
        return cls(**data)


@dataclass(slots=True, frozen=True)
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

    tiles: list[list[TileData]]
    width: int
    height: int
    current_map: int
    player_x: int
    player_y: int
    timestamp: int | None = None

    def get_tile(self, x: int, y: int) -> TileData | None:
        """Get tile data at specific coordinates."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.tiles[y][x]
        return None

    def get_walkable_tiles(self) -> list[TileData]:
        """Get all walkable tiles in the matrix."""
        walkable = []
        for row in self.tiles:
            for tile in row:
                if tile.is_walkable:
                    walkable.append(tile)
        return walkable

    def get_tiles_by_type(self, tile_type: TileType) -> list[TileData]:
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
            "tiles": [[tile.to_dict() for tile in row] for row in self.tiles],
            "width": self.width,
            "height": self.height,
            "current_map": self.current_map,
            "player_x": self.player_x,
            "player_y": self.player_y,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "TileMatrix":
        """Create TileMatrix from dictionary."""
        tiles = [
            [TileData.from_dict(tile_data) for tile_data in row]
            for row in data["tiles"]
        ]
        return cls(
            tiles=tiles,
            width=data["width"],
            height=data["height"],
            current_map=data["current_map"],
            player_x=data["player_x"],
            player_y=data["player_y"],
            timestamp=data.get("timestamp"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "TileMatrix":
        """Create TileMatrix from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def get_tile_id_matrix(self):
        """Get a simple 2D numpy array of just tile IDs for compatibility."""
        return np.array(
            [[tile.tile_id for tile in row] for row in self.tiles], dtype=np.uint32
        )

    def get_walkability_matrix(self):
        """Get a boolean matrix indicating walkable tiles."""
        return np.array(
            [[tile.is_walkable for tile in row] for row in self.tiles], dtype=bool
        )

    def get_encounter_matrix(self):
        """Get a boolean matrix indicating encounter tiles."""
        return np.array(
            [[tile.is_encounter_tile for tile in row] for row in self.tiles], dtype=bool
        )


def classify_tile_type(
    tile_id: int, is_walkable: bool, tileset_id: TilesetID = TilesetID.OVERWORLD
) -> TileType:
    """
    Classify a tile based on its ID and properties using tileset-specific data.

    Args:
        tile_id: The tile identifier
        is_walkable: Whether the tile is walkable
        tileset_id: Current tileset ID for context

    Returns:
        TileType classification
    """
    # Check tileset-specific mappings
    if tileset_id in GRASS_TILES and tile_id in GRASS_TILES[tileset_id]:
        return TileType.GRASS

    if tileset_id in WATER_TILES and tile_id in WATER_TILES[tileset_id]:
        return TileType.WATER

    if tileset_id in DOOR_TILES and tile_id in DOOR_TILES[tileset_id]:
        return TileType.WARP

    if tileset_id in LEDGE_TILES:
        # Check all ledge directions for this tileset
        for tiles in LEDGE_TILES[tileset_id].values():
            if tile_id in tiles:
                return TileType.LEDGE

    if tileset_id in TREE_TILES and tile_id in TREE_TILES[tileset_id]:
        return TileType.TREE

    if is_walkable:
        # Further classify walkable tiles
        if 20 <= tile_id <= 30:  # Road tile range
            return TileType.ROAD
        else:
            return TileType.WALKABLE
    else:
        # Classify blocked tiles
        if 100 <= tile_id <= 120:  # Generic rock tile range
            return TileType.ROCK
        elif 200 <= tile_id <= 220:  # Generic building tile range
            return TileType.BUILDING
        else:
            return TileType.BLOCKED

    return TileType.UNKNOWN


def is_tile_walkable(tile_id: int, tileset_id: TilesetID = TilesetID.OVERWORLD) -> bool:
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
