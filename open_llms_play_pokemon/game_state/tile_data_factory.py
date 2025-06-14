"""
Factory for creating TileData objects with various configurations.

This module provides factory methods for creating TileData instances,
reducing code duplication and improving maintainability.
"""

from .data.tile_data_constants import TilesetID
from .tile_data import TileData, TileType


class TileDataFactory:
    """Factory class for creating TileData objects."""

    @staticmethod
    def create_placeholder(
        x: int, y: int, tileset_id: TilesetID = TilesetID.OVERWORLD
    ) -> TileData:
        """
        Create a placeholder TileData object with default values.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate
            tileset_id: Tileset ID for the placeholder

        Returns:
            TileData object with default/placeholder values
        """
        return TileData(
            # Basic Identification
            tile_id=0x00,
            x=x,
            y=y,
            map_x=x,
            map_y=y,
            tile_type=TileType.UNKNOWN,
            tileset_id=tileset_id,
            raw_value=0x00,
            # Movement/Collision
            is_walkable=False,
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=1.0,
            # Environmental
            is_encounter_tile=False,
            is_warp_tile=False,
            is_animated=False,
            light_level=15,
            # Interactions
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            # Battle System
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
            requires_itemfinder=False,
            # Special Zones
            safari_zone_steps=False,
            game_corner_tile=False,
            is_fly_destination=False,
            # Audio/Visual
            has_footstep_sound=True,
            sprite_priority=0,
            background_priority=0,
            elevation_pair=None,
            # Additional Properties
            sprite_offset=0,
            blocks_light=False,
            water_current_direction=None,
            warp_destination_map=None,
            warp_destination_x=None,
            warp_destination_y=None,
        )

    @staticmethod
    def create_walkable(
        tile_id: int,
        x: int,
        y: int,
        map_x: int,
        map_y: int,
        tile_type: TileType = TileType.WALKABLE,
        tileset_id: TilesetID = TilesetID.OVERWORLD,
    ) -> TileData:
        """
        Create a basic walkable TileData object.

        Args:
            tile_id: Tile ID value
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            tile_type: Type of tile (default WALKABLE)
            tileset_id: Tileset ID

        Returns:
            TileData object configured as walkable
        """
        return TileData(
            # Basic Identification
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=tile_type,
            tileset_id=tileset_id,
            raw_value=tile_id,
            # Movement/Collision
            is_walkable=True,
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=1.0,
            # Environmental
            is_encounter_tile=(tile_type == TileType.GRASS),
            is_warp_tile=(tile_type == TileType.WARP),
            is_animated=False,
            light_level=15,
            # Interactions
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            # Battle System
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
            requires_itemfinder=False,
            # Special Zones
            safari_zone_steps=False,
            game_corner_tile=False,
            is_fly_destination=False,
            # Audio/Visual
            has_footstep_sound=True,
            sprite_priority=0,
            background_priority=0,
            elevation_pair=None,
            # Additional Properties
            sprite_offset=0,
            blocks_light=False,
            water_current_direction=None,
            warp_destination_map=None,
            warp_destination_x=None,
            warp_destination_y=None,
        )

    @staticmethod
    def create_blocked(
        tile_id: int,
        x: int,
        y: int,
        map_x: int,
        map_y: int,
        tile_type: TileType = TileType.BLOCKED,
        tileset_id: TilesetID = TilesetID.OVERWORLD,
        blocks_light: bool = False,
    ) -> TileData:
        """
        Create a blocked/collision TileData object.

        Args:
            tile_id: Tile ID value
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            tile_type: Type of tile (default BLOCKED)
            tileset_id: Tileset ID
            blocks_light: Whether this tile blocks light

        Returns:
            TileData object configured as blocked
        """
        return TileData(
            # Basic Identification
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=tile_type,
            tileset_id=tileset_id,
            raw_value=tile_id,
            # Movement/Collision
            is_walkable=False,
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=0.0,
            # Environmental
            is_encounter_tile=False,
            is_warp_tile=False,
            is_animated=False,
            light_level=15 if not blocks_light else 8,
            # Interactions
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=(tile_type == TileType.TREE),
            pc_accessible=False,
            # Battle System
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
            requires_itemfinder=False,
            # Special Zones
            safari_zone_steps=False,
            game_corner_tile=False,
            is_fly_destination=False,
            # Audio/Visual
            has_footstep_sound=False,
            sprite_priority=0,
            background_priority=0,
            elevation_pair=None,
            # Additional Properties
            sprite_offset=0,
            blocks_light=blocks_light,
            water_current_direction=None,
            warp_destination_map=None,
            warp_destination_x=None,
            warp_destination_y=None,
        )

    @staticmethod
    def create_water(
        tile_id: int,
        x: int,
        y: int,
        map_x: int,
        map_y: int,
        tileset_id: TilesetID = TilesetID.OVERWORLD,
        is_animated: bool = True,
        water_current_direction: str | None = None,
    ) -> TileData:
        """
        Create a water TileData object.

        Args:
            tile_id: Tile ID value
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            tileset_id: Tileset ID
            is_animated: Whether water tile is animated
            water_current_direction: Direction of water current for surfing

        Returns:
            TileData object configured as water
        """
        return TileData(
            # Basic Identification
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=TileType.WATER,
            tileset_id=tileset_id,
            raw_value=tile_id,
            # Movement/Collision
            is_walkable=False,  # Requires SURF
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=0.5,  # Surfing speed
            # Environmental
            is_encounter_tile=True,  # Water Pokemon encounters
            is_warp_tile=False,
            is_animated=is_animated,
            light_level=15,
            # Interactions
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            # Battle System
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
            requires_itemfinder=False,
            # Special Zones
            safari_zone_steps=False,
            game_corner_tile=False,
            is_fly_destination=False,
            # Audio/Visual
            has_footstep_sound=True,  # Splash sound
            sprite_priority=0,
            background_priority=0,
            elevation_pair=None,
            # Additional Properties
            sprite_offset=0,
            blocks_light=False,
            water_current_direction=water_current_direction,
            warp_destination_map=None,
            warp_destination_x=None,
            warp_destination_y=None,
        )

    @staticmethod
    def create_ledge(
        tile_id: int,
        x: int,
        y: int,
        map_x: int,
        map_y: int,
        ledge_direction: str,
        tileset_id: TilesetID = TilesetID.OVERWORLD,
    ) -> TileData:
        """
        Create a ledge TileData object.

        Args:
            tile_id: Tile ID value
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            ledge_direction: Direction player can jump ("down", "left", "right", "up")
            tileset_id: Tileset ID

        Returns:
            TileData object configured as a ledge
        """
        return TileData(
            # Basic Identification
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=TileType.LEDGE,
            tileset_id=tileset_id,
            raw_value=tile_id,
            # Movement/Collision
            is_walkable=False,  # Can only jump over
            is_ledge_tile=True,
            ledge_direction=ledge_direction,
            movement_modifier=1.0,
            # Environmental
            is_encounter_tile=False,
            is_warp_tile=False,
            is_animated=False,
            light_level=15,
            # Interactions
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            # Battle System
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
            requires_itemfinder=False,
            # Special Zones
            safari_zone_steps=False,
            game_corner_tile=False,
            is_fly_destination=False,
            # Audio/Visual
            has_footstep_sound=True,
            sprite_priority=0,
            background_priority=0,
            elevation_pair=None,
            # Additional Properties
            sprite_offset=0,
            blocks_light=False,
            water_current_direction=None,
            warp_destination_map=None,
            warp_destination_x=None,
            warp_destination_y=None,
        )
