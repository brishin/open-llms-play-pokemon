import logging

from pyboy import PyBoyMemoryView

from .data.memory_addresses import MemoryAddresses
from .data.tile_data_constants import TilesetID
from .tile_data import TileData, classify_tile_type
from .tile_property_detector import TilePropertyDetector

logger = logging.getLogger(__name__)


def get_tile_id(memory_view: PyBoyMemoryView, x: int, y: int) -> int:
    """
    Read tile ID from wTileMap buffer using type-safe memory access.

    Args:
        memory_view: PyBoy memory view for type-safe memory access
        x: Screen X coordinate (0-19)
        y: Screen Y coordinate (0-17)

    Returns:
        Tile ID at the specified screen position
    """
    if not (0 <= x < 20 and 0 <= y < 18):
        raise ValueError(f"Invalid screen coordinates: ({x}, {y})")

    offset = (y * 20) + x
    return memory_view[MemoryAddresses.tile_map_buffer + offset]


def get_map_coordinates(
    memory_view: PyBoyMemoryView, screen_x: int, screen_y: int
) -> tuple[int, int]:
    """
    Convert screen coordinates to absolute map coordinates using player position.

    Args:
        memory_view: PyBoy memory view for accessing player position
        screen_x: Screen X coordinate (0-19)
        screen_y: Screen Y coordinate (0-17)

    Returns:
        Tuple of (map_x, map_y) absolute coordinates
    """
    player_x = memory_view[MemoryAddresses.x_coord]
    player_y = memory_view[MemoryAddresses.y_coord]

    # Convert screen coordinates to map coordinates
    # Player sprite is at screen position (8, 9), verified from Pokemon Red assembly
    map_x = player_x + screen_x - 8
    map_y = player_y + screen_y - 9

    return map_x, map_y


def is_collision_tile(memory_view: PyBoyMemoryView, tile_id: int) -> bool:
    """
    Check if a tile ID causes collision (blocks movement) using PyBoy memory access.

    Args:
        memory_view: PyBoy memory view for reading collision data
        tile_id: Tile ID to check for collision

    Returns:
        True if tile blocks movement, False if walkable
    """
    try:
        # Read collision table pointer (2 bytes, little endian)
        collision_ptr_low = memory_view[MemoryAddresses.tileset_collision_ptr]
        collision_ptr_high = memory_view[MemoryAddresses.tileset_collision_ptr + 1]
        collision_ptr = collision_ptr_low | (collision_ptr_high << 8)

        # Validate pointer is reasonable (should be in ROM space)
        if collision_ptr < 0x4000 or collision_ptr > 0x7FFF:
            # Fallback to hardcoded collision tables when pointer is invalid
            return _fallback_collision_check(memory_view, tile_id, logger)

        # Read collision table until FF termination
        # NOTE: Pokemon Red collision tables contain WALKABLE tiles, not blocked tiles
        offset = 0
        while True:
            collision_tile = memory_view[collision_ptr + offset]
            if collision_tile == 0xFF:  # End of table
                break
            if collision_tile == tile_id:
                return False  # Tile is in collision table (walkable)
            offset += 1
            if offset > 100:  # Safety limit to prevent infinite loops
                logger.warning(
                    f"Collision table too long, using fallback for tile {tile_id}"
                )
                return _fallback_collision_check(memory_view, tile_id, logger)

        return True  # Tile not in collision table (blocked)
    except Exception as e:
        logger.warning(f"Failed to read collision data for tile {tile_id}: {e}")
        return _fallback_collision_check(memory_view, tile_id, logger)


def _fallback_collision_check(
    memory_view: PyBoyMemoryView, tile_id: int, logger
) -> bool:
    """
    Fallback collision detection using hardcoded tileset collision tables.
    Based on Pokemon Red source code collision tables.
    """
    try:
        current_tileset = memory_view[MemoryAddresses.current_tileset]
    except Exception:
        logger.warning(f"Could not read tileset, assuming tile {tile_id} is blocked")
        return True

    # Hardcoded collision tables from Pokemon Red source (walkable tiles for each tileset)
    # These correspond to the collision_tile_ids.asm file and tileset_headers.asm ordering
    tileset_walkable_tiles = {
        0: [
            0x00,
            0x10,
            0x1B,
            0x20,
            0x21,
            0x23,
            0x2C,
            0x2D,
            0x2E,
            0x30,
            0x31,
            0x33,
            0x39,
            0x3C,
            0x3E,
            0x52,
            0x54,
            0x58,
            0x5B,
        ],  # Overworld_Coll
        1: [0x01, 0x02, 0x03, 0x11, 0x12, 0x13, 0x14, 0x1C, 0x1A],  # RedsHouse1_Coll
        2: [0x11, 0x1A, 0x1C, 0x3C, 0x5E],  # Mart_Coll
        3: [
            0x1E,
            0x20,
            0x2E,
            0x30,
            0x34,
            0x37,
            0x39,
            0x3A,
            0x40,
            0x51,
            0x52,
            0x5A,
            0x5C,
            0x5E,
            0x5F,
        ],  # Forest_Coll
        4: [
            0x01,
            0x02,
            0x03,
            0x11,
            0x12,
            0x13,
            0x14,
            0x1C,
            0x1A,
        ],  # RedsHouse2_Coll (same as RedsHouse1_Coll)
        5: [
            0x11,
            0x16,
            0x19,
            0x2B,
            0x3C,
            0x3D,
            0x3F,
            0x4A,
            0x4C,
            0x4D,
            0x03,
        ],  # Dojo_Coll
        6: [0x11, 0x1A, 0x1C, 0x3C, 0x5E],  # Pokecenter_Coll (same as Mart_Coll)
        7: [
            0x11,
            0x16,
            0x19,
            0x2B,
            0x3C,
            0x3D,
            0x3F,
            0x4A,
            0x4C,
            0x4D,
            0x03,
        ],  # Gym_Coll (same as Dojo_Coll)
        8: [0x01, 0x12, 0x14, 0x28, 0x32, 0x37, 0x44, 0x54, 0x5C],  # House_Coll
        9: [
            0x01,
            0x12,
            0x14,
            0x1A,
            0x1C,
            0x37,
            0x38,
            0x3B,
            0x3C,
            0x5E,
        ],  # ForestGate_Coll
        10: [
            0x01,
            0x12,
            0x14,
            0x1A,
            0x1C,
            0x37,
            0x38,
            0x3B,
            0x3C,
            0x5E,
        ],  # Museum_Coll (same as ForestGate_Coll)
        11: [0x0B, 0x0C, 0x13, 0x15, 0x18],  # Underground_Coll
        12: [
            0x01,
            0x12,
            0x14,
            0x1A,
            0x1C,
            0x37,
            0x38,
            0x3B,
            0x3C,
            0x5E,
        ],  # Gate_Coll (same as ForestGate_Coll)
        13: [0x04, 0x0D, 0x17, 0x1D, 0x1E, 0x23, 0x34, 0x37, 0x39, 0x4A],  # Ship_Coll
        14: [0x0A, 0x1A, 0x32, 0x3B],  # ShipPort_Coll
        15: [0x01, 0x10, 0x13, 0x1B, 0x22, 0x42, 0x52],  # Cemetery_Coll
        16: [0x04, 0x0F, 0x15, 0x1F, 0x3B, 0x45, 0x47, 0x55, 0x56],  # Interior_Coll
        17: [0x05, 0x15, 0x18, 0x1A, 0x20, 0x21, 0x22, 0x2A, 0x2D, 0x30],  # Cavern_Coll
        18: [0x14, 0x17, 0x1A, 0x1C, 0x20, 0x38, 0x45],  # Lobby_Coll
        19: [0x01, 0x05, 0x11, 0x12, 0x14, 0x1A, 0x1C, 0x2C, 0x53],  # Mansion_Coll
        20: [0x0C, 0x26, 0x16, 0x1E, 0x34, 0x37],  # Lab_Coll
        21: [
            0x0F,
            0x1A,
            0x1F,
            0x26,
            0x28,
            0x29,
            0x2C,
            0x2D,
            0x2E,
            0x2F,
            0x41,
        ],  # Club_Coll
        22: [
            0x01,
            0x10,
            0x11,
            0x13,
            0x1B,
            0x20,
            0x21,
            0x22,
            0x30,
            0x31,
            0x32,
            0x42,
            0x43,
            0x48,
            0x52,
            0x55,
            0x58,
            0x5E,
        ],  # Facility_Coll
        23: [0x1B, 0x23, 0x2C, 0x2D, 0x3B, 0x45],  # Plateau_Coll
    }

    walkable_tiles = tileset_walkable_tiles.get(current_tileset, [])

    if tile_id in walkable_tiles:
        return False  # Tile is walkable
    else:
        return True  # Tile is blocked


def get_sprite_at_position(
    memory_view: PyBoyMemoryView, screen_x: int, screen_y: int
) -> int:
    """
    Detect sprite at screen position using PyBoy memory access to sprite data.

    Args:
        memory_view: PyBoy memory view for accessing sprite data
        screen_x: Screen X coordinate (0-19)
        screen_y: Screen Y coordinate (0-17)

    Returns:
        Sprite offset if sprite found at position, 0 if no sprite
    """
    try:
        # Convert screen coordinates to pixel coordinates
        pixel_x = screen_x * 8
        pixel_y = screen_y * 8

        # Check up to 16 sprite slots (standard for Game Boy)
        for sprite_id in range(16):
            sprite_base = MemoryAddresses.sprite_state_data + (sprite_id * 16)

            # Read sprite position (SPRITESTATEDATA structure)
            sprite_x = memory_view[sprite_base + 6]  # SPRITESTATEDATA1_XPIXELS
            sprite_y = memory_view[sprite_base + 4]  # SPRITESTATEDATA1_YPIXELS

            # Check if sprite is at the target position (8x8 tile)
            if abs(sprite_x - pixel_x) < 8 and abs(sprite_y - pixel_y) < 8:
                return sprite_id + 1  # Return non-zero sprite offset

        return 0  # No sprite found
    except Exception:
        return 0  # Return 0 if sprite detection fails


def read_entire_screen(memory_view: PyBoyMemoryView) -> list[TileData]:
    """
    Process entire visible screen using type-safe PyBoy memory access.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        List of TileData objects for all tiles on screen (360 tiles max)
        Empty list if map is transitioning/loading
    """
    # Check if map is stable before analysis
    try:
        loading_status = memory_view[MemoryAddresses.map_loading_status]
        # Allow common stable values: 0 (classic stable), 16 (stable - observed in init.state)
        # Only treat values 1-3 as actively transitioning states based on Pokemon Red source
        if 1 <= loading_status <= 3:  # Map is actively transitioning
            return []
    except Exception:
        # If we can't read loading status, assume map is stable for tests
        pass

    tiles = []
    for y in range(18):  # Screen height
        for x in range(20):  # Screen width
            try:
                tile_data = read_single_tile(memory_view, x, y)
                tiles.append(tile_data)
            except Exception:
                # Skip problematic tiles during batch processing
                continue

    return tiles


def read_single_tile(memory_view: PyBoyMemoryView, x: int, y: int) -> TileData:
    """
    Read a single tile from the game state using PyBoy memory API.

    Args:
        memory_view: PyBoy memory view for accessing game memory
        x: Screen X coordinate (0-19)
        y: Screen Y coordinate (0-17)
    """
    # Basic tile reading with type-safe enum addresses
    tile_id = get_tile_id(memory_view, x, y)
    tileset_id = TilesetID(memory_view[MemoryAddresses.current_tileset])

    # Coordinate conversion using map coordinates function
    map_x, map_y = get_map_coordinates(memory_view, x, y)

    # Collision detection with type-safe collision pointer
    is_collision = is_collision_tile(memory_view, tile_id)
    is_walkable_tile = not is_collision

    # Sprite detection using PyBoy memory API with IntEnum base address
    sprite_offset = get_sprite_at_position(memory_view, x, y)

    # Classify tile type using existing system
    tile_type = classify_tile_type(tile_id, is_walkable_tile, tileset_id)

    # Enhanced property detection using consolidated detector
    all_props = TilePropertyDetector.detect_all_properties(
        memory_view, tileset_id, tile_id, map_x, map_y
    )

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
        is_walkable=is_walkable_tile,
        is_ledge_tile=all_props["is_ledge"],
        ledge_direction=all_props["ledge_direction"],
        movement_modifier=all_props.get("movement_modifier", 1.0),
        # Environmental
        is_encounter_tile=all_props["is_encounter"],
        is_warp_tile=all_props["is_warp"],
        is_animated=all_props["is_animated"],
        light_level=all_props.get("light_level", 15),
        # Interactions
        has_sign=all_props["has_sign"],
        has_bookshelf=all_props["has_bookshelf"],
        strength_boulder=all_props["strength_boulder"],
        cuttable_tree=all_props["cuttable_tree"],
        pc_accessible=all_props["pc_accessible"],
        # Battle System
        trainer_sight_line=all_props["in_sight_line"],
        trainer_id=all_props.get("trainer_id"),
        hidden_item_id=all_props.get("hidden_item_id"),
        requires_itemfinder=all_props.get("requires_itemfinder", False),
        # Special Zones
        safari_zone_steps=all_props.get("safari_zone_steps", False),
        game_corner_tile=all_props.get("game_corner_tile", False),
        is_fly_destination=all_props.get("is_fly_destination", False),
        # Audio/Visual
        has_footstep_sound=all_props["has_footstep_sound"],
        sprite_priority=all_props.get("sprite_priority", 0),
        background_priority=all_props.get("background_priority", 0),
        elevation_pair=all_props.get("elevation_pair"),
        # Additional Properties
        sprite_offset=sprite_offset,
        blocks_light=all_props.get("blocks_light", False),
        water_current_direction=all_props.get("water_current_direction"),
        warp_destination_map=all_props.get("warp_destination_map"),
        warp_destination_x=all_props.get("warp_destination_x"),
        warp_destination_y=all_props.get("warp_destination_y"),
    )
