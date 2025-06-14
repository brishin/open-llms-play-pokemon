"""
Tile property detection system for Pokemon Red.

This module consolidates all tile property detection logic into a single class,
improving organization and maintainability.
"""

from pyboy import PyBoyMemoryView

from .data.memory_addresses import MemoryAddresses
from .data.tile_data_constants import (
    BOOKSHELF_TILES,
    DOOR_TILES,
    GRASS_TILES,
    LEDGE_DATA,
    LEDGE_TILES,
    PC_TILES,
    SIGN_TILES,
    STRENGTH_BOULDER_TILES,
    TREE_TILES,
    WATER_TILES,
    TilesetID,
)


class TilePropertyDetector:
    """Detects various properties of tiles based on tileset and tile ID."""

    def __init__(self, memory_view: PyBoyMemoryView):
        """
        Initialize the detector with a memory view.

        Args:
            memory_view: PyBoy memory view for accessing game memory
        """
        self.memory_view = memory_view

    def detect_ledge_info(
        self, tileset_id: TilesetID, tile_id: int
    ) -> tuple[str | None, bool]:
        """
        Detect ledge properties using pokered ledge data.

        Args:
            tileset_id: Current tileset ID
            tile_id: Tile ID to check

        Returns:
            Tuple of (ledge_direction, is_ledge_tile)
        """
        # Check against pokered ledge data structure
        for _facing_direction, _standing_tile, ledge_tile, input_required in LEDGE_DATA:
            if tile_id == ledge_tile:
                # Extract direction from input_required (e.g., "D_DOWN" -> "down")
                direction = input_required.split("_")[-1].lower()
                return direction, True

        # Check tileset-specific ledge tiles for backward compatibility
        if tileset_id in LEDGE_TILES:
            for direction, tiles in LEDGE_TILES[tileset_id].items():
                if tile_id in tiles:
                    return direction, True

        return None, False

    def detect_audio_properties(self, tileset_id: TilesetID, tile_id: int) -> dict:
        """
        Detect audio properties for footstep sounds and environmental audio.

        Args:
            tileset_id: Current tileset ID
            tile_id: Tile ID to check

        Returns:
            Dictionary with audio properties
        """
        # Default footstep sound for most tiles
        has_footstep = True
        audio_type = "normal"

        # Water tiles typically have splash sounds
        if tileset_id in WATER_TILES and tile_id in WATER_TILES[tileset_id]:
            has_footstep = True
            audio_type = "splash"

        # Grass tiles might have rustling sounds
        elif tileset_id in GRASS_TILES and tile_id in GRASS_TILES[tileset_id]:
            audio_type = "grass"

        # Some special tiles might be silent (would need pokered audio analysis)

        return {
            "has_footstep_sound": has_footstep,
            "audio_type": audio_type,
        }

    def detect_trainer_sight_line(self, map_x: int, map_y: int) -> dict:
        """
        Detect if position is in trainer sight line using sprite data analysis.

        Args:
            map_x: Absolute map X coordinate
            map_y: Absolute map Y coordinate

        Returns:
            Dictionary with trainer sight line information
        """
        try:
            # Check trainer sprites for sight line detection
            # This would require analysis of trainer sprite data and facing directions
            # For now, return basic structure

            in_sight_line = False
            trainer_id = None

            # Check up to 16 sprites for trainer types
            for sprite_id in range(16):
                sprite_base = MemoryAddresses.sprite_state_data + (sprite_id * 16)

                # Read sprite data (would need trainer sprite identification)
                _sprite_x = self.memory_view[
                    sprite_base + 6
                ]  # SPRITESTATEDATA1_XPIXELS
                _sprite_y = self.memory_view[
                    sprite_base + 4
                ]  # SPRITESTATEDATA1_YPIXELS

                # This would need proper trainer detection logic
                # For now, placeholder implementation
                del _sprite_x, _sprite_y  # Silence unused variable warnings

            return {
                "in_sight_line": in_sight_line,
                "trainer_id": trainer_id,
                "sight_distance": 0,
            }
        except Exception:
            return {
                "in_sight_line": False,
                "trainer_id": None,
                "sight_distance": 0,
            }

    def detect_special_properties(
        self, tileset_id: TilesetID, tile_id: int, map_x: int, map_y: int
    ) -> dict:
        """
        Detect special zone properties and unique tile behaviors.

        Args:
            tileset_id: Current tileset ID
            tile_id: Tile ID to check
            map_x: Absolute map X coordinate
            map_y: Absolute map Y coordinate

        Returns:
            Dictionary with special properties
        """
        properties = {
            "movement_modifier": 1.0,
            "light_level": 15,
            "blocks_light": False,
            "safari_zone_steps": False,
            "game_corner_tile": False,
            "is_fly_destination": False,
            "hidden_item_id": None,
            "requires_itemfinder": False,
            "elevation_pair": None,
        }

        # Cave/dungeon areas have reduced light
        if tileset_id == TilesetID.CAVERN:
            properties["light_level"] = 8
            properties["blocks_light"] = True

        # Indoor areas have moderate light
        elif tileset_id in [
            TilesetID.REDS_HOUSE_1,
            TilesetID.REDS_HOUSE_2,
            TilesetID.POKECENTER,
            TilesetID.MART,
        ]:
            properties["light_level"] = 12

        # Water tiles might slow movement
        if tileset_id in WATER_TILES and tile_id in WATER_TILES[tileset_id]:
            properties["movement_modifier"] = 0.5  # Surfing speed

        # Special zone detection would require map-specific analysis
        # This would need pokered map data to determine special zones

        return properties

    def detect_animation_info(self, tileset_id: TilesetID, tile_id: int) -> dict:
        """
        Detect animation properties and sprite priorities.

        Args:
            tileset_id: Current tileset ID
            tile_id: Tile ID to check

        Returns:
            Dictionary with animation information
        """
        # Default values
        animation_info = {
            "is_animated": False,
            "sprite_priority": 0,
            "background_priority": 0,
            "animation_speed": 0,
        }

        # Water tiles are typically animated
        if tileset_id in WATER_TILES and tile_id in WATER_TILES[tileset_id]:
            animation_info["is_animated"] = True
            animation_info["animation_speed"] = 2

        # Grass tiles might have wind animation
        if tileset_id in GRASS_TILES and tile_id in GRASS_TILES[tileset_id]:
            animation_info["is_animated"] = True
            animation_info["animation_speed"] = 1

        # This would need pokered tileset animation analysis for complete accuracy

        return animation_info

    def detect_interaction_properties(
        self, tileset_id: TilesetID, tile_id: int
    ) -> dict:
        """
        Detect interactive elements like signs, bookshelves, trees, etc.

        Args:
            tileset_id: Current tileset ID
            tile_id: Tile ID to check

        Returns:
            Dictionary with interaction properties
        """
        interactions = {
            "has_sign": False,
            "has_bookshelf": False,
            "strength_boulder": False,
            "cuttable_tree": False,
            "pc_accessible": False,
        }

        # Check tileset-specific interaction tiles
        if tileset_id in SIGN_TILES and tile_id in SIGN_TILES[tileset_id]:
            interactions["has_sign"] = True

        if tileset_id in BOOKSHELF_TILES and tile_id in BOOKSHELF_TILES[tileset_id]:
            interactions["has_bookshelf"] = True

        if (
            tileset_id in STRENGTH_BOULDER_TILES
            and tile_id in STRENGTH_BOULDER_TILES[tileset_id]
        ):
            interactions["strength_boulder"] = True

        if tileset_id in TREE_TILES and tile_id in TREE_TILES[tileset_id]:
            interactions["cuttable_tree"] = True

        if tileset_id in PC_TILES and tile_id in PC_TILES[tileset_id]:
            interactions["pc_accessible"] = True

        return interactions

    def detect_environmental_properties(
        self, tileset_id: TilesetID, tile_id: int
    ) -> dict:
        """
        Detect environmental properties like encounters, warps, water currents.

        Args:
            tileset_id: Current tileset ID
            tile_id: Tile ID to check

        Returns:
            Dictionary with environmental properties
        """
        env_props = {
            "is_encounter": False,
            "is_warp": False,
            "water_current_direction": None,
            "warp_destination_map": None,
            "warp_destination_x": None,
            "warp_destination_y": None,
        }

        # Check for encounter tiles (grass)
        if tileset_id in GRASS_TILES and tile_id in GRASS_TILES[tileset_id]:
            env_props["is_encounter"] = True

        # Check for warp tiles (doors)
        if tileset_id in DOOR_TILES and tile_id in DOOR_TILES[tileset_id]:
            env_props["is_warp"] = True
            # Warp destination would need map data analysis

        # Water current detection for surfing mechanics
        if tileset_id in WATER_TILES and tile_id in WATER_TILES[tileset_id]:
            # This would need pokered water current analysis
            pass

        return env_props
