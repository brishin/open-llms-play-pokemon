"""
Factory for creating TileData objects with common configurations.

Eliminates code duplication in placeholder creation and provides
reusable patterns for common tile types.
"""

from .data.tile_data_constants import TilesetID
from .tile_data import TileData, TileType


class TileDataFactory:
    """Factory class for creating TileData objects with common configurations."""

    @staticmethod
    def create_placeholder(
        x: int, y: int, map_x: int | None = None, map_y: int | None = None
    ) -> TileData:
        """
        Create a placeholder tile for missing or unknown positions.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate (defaults to x)
            map_y: Map Y coordinate (defaults to y)

        Returns:
            TileData configured as an unknown/blocked placeholder
        """
        return TileData(
            tile_id=0x00,
            x=x,
            y=y,
            map_x=map_x or x,
            map_y=map_y or y,
            tile_type=TileType.UNKNOWN,
            tileset_id=TilesetID.OVERWORLD,
            raw_value=0x00,
            is_walkable=False,
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=1.0,
            is_encounter_tile=False,
            is_warp_tile=False,
            is_animated=False,
            light_level=15,
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
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

    @staticmethod
    def create_walkable(
        tile_id: int,
        x: int,
        y: int,
        map_x: int,
        map_y: int,
        tileset_id: TilesetID = TilesetID.OVERWORLD,
        tile_type: TileType = TileType.WALKABLE,
    ) -> TileData:
        """
        Create a basic walkable tile.

        Args:
            tile_id: The tile ID from memory
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            tileset_id: Tileset ID
            tile_type: Type of tile

        Returns:
            TileData configured as a walkable tile
        """
        return TileData(
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=tile_type,
            tileset_id=tileset_id,
            raw_value=tile_id,
            is_walkable=True,
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=1.0,
            is_encounter_tile=False,
            is_warp_tile=False,
            is_animated=False,
            light_level=15,
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
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

    @staticmethod
    def create_blocked(
        tile_id: int,
        x: int,
        y: int,
        map_x: int,
        map_y: int,
        tileset_id: TilesetID = TilesetID.OVERWORLD,
        tile_type: TileType = TileType.BLOCKED,
    ) -> TileData:
        """
        Create a blocked/collision tile.

        Args:
            tile_id: The tile ID from memory
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            tileset_id: Tileset ID
            tile_type: Type of tile

        Returns:
            TileData configured as a blocked tile
        """
        return TileData(
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=tile_type,
            tileset_id=tileset_id,
            raw_value=tile_id,
            is_walkable=False,
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=1.0,
            is_encounter_tile=False,
            is_warp_tile=False,
            is_animated=False,
            light_level=15,
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
            requires_itemfinder=False,
            safari_zone_steps=False,
            game_corner_tile=False,
            is_fly_destination=False,
            has_footstep_sound=True,
            sprite_priority=0,
            background_priority=0,
            elevation_pair=None,
            sprite_offset=0,
            blocks_light=True,
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
        current_direction: str | None = None,
    ) -> TileData:
        """
        Create a water tile with animation and optional current.

        Args:
            tile_id: The tile ID from memory
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            tileset_id: Tileset ID
            current_direction: Water current direction if any

        Returns:
            TileData configured as a water tile
        """
        return TileData(
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=TileType.WATER,
            tileset_id=tileset_id,
            raw_value=tile_id,
            is_walkable=True,  # With surf
            is_ledge_tile=False,
            ledge_direction=None,
            movement_modifier=0.5,  # Surfing speed
            is_encounter_tile=True,  # Water encounters
            is_warp_tile=False,
            is_animated=True,
            light_level=15,
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
            requires_itemfinder=False,
            safari_zone_steps=False,
            game_corner_tile=False,
            is_fly_destination=False,
            has_footstep_sound=True,  # Splash sound
            sprite_priority=0,
            background_priority=0,
            elevation_pair=None,
            sprite_offset=0,
            blocks_light=False,
            water_current_direction=current_direction,
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
        direction: str,
        tileset_id: TilesetID = TilesetID.OVERWORLD,
    ) -> TileData:
        """
        Create a ledge tile with direction.

        Args:
            tile_id: The tile ID from memory
            x: Screen X coordinate
            y: Screen Y coordinate
            map_x: Map X coordinate
            map_y: Map Y coordinate
            direction: Ledge direction (north, south, east, west)
            tileset_id: Tileset ID

        Returns:
            TileData configured as a ledge tile
        """
        return TileData(
            tile_id=tile_id,
            x=x,
            y=y,
            map_x=map_x,
            map_y=map_y,
            tile_type=TileType.LEDGE,
            tileset_id=tileset_id,
            raw_value=tile_id,
            is_walkable=True,  # Can jump down
            is_ledge_tile=True,
            ledge_direction=direction,
            movement_modifier=1.0,
            is_encounter_tile=False,
            is_warp_tile=False,
            is_animated=False,
            light_level=15,
            has_sign=False,
            has_bookshelf=False,
            strength_boulder=False,
            cuttable_tree=False,
            pc_accessible=False,
            trainer_sight_line=False,
            trainer_id=None,
            hidden_item_id=None,
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
