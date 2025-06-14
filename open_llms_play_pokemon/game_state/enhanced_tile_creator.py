"""
Enhanced Tile Data Creation System

Implements the complete create_tile_data() function from TILE_EXTRACTION_GUIDE using PyBoy
memory API that generates TileData with all 30+ properties including collision, interaction,
animation, and special behaviors.
"""

from pyboy import PyBoyMemoryView

from .data.memory_addresses import MemoryAddresses
from .data.tile_data_constants import TilesetID
from .tile_data import TileData, classify_tile_type, is_tile_walkable
from .tile_property_detector import TilePropertyDetector


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
    # Screen center is at (10, 9), so offset from player position
    map_x = player_x + screen_x - 10
    map_y = player_y + screen_y - 9

    return map_x, map_y


def is_collision_tile(memory_view: PyBoyMemoryView, tile_id: int) -> bool:
    """
    Check if a tile ID is in the collision table using PyBoy memory access.

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

        # Read collision table until FF termination
        offset = 0
        while True:
            collision_tile = memory_view[collision_ptr + offset]
            if collision_tile == 0xFF:  # End of table
                break
            if collision_tile == tile_id:
                return True  # Tile is in collision table (blocked)
            offset += 1
            if offset > 100:  # Safety limit
                break

        return False  # Tile not in collision table (walkable)
    except Exception:
        # Fallback to tileset-specific collision tables if memory read fails
        current_tileset = TilesetID(memory_view[MemoryAddresses.current_tileset])
        return not is_tile_walkable(tile_id, current_tileset)


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


def create_tile_data(memory_view: PyBoyMemoryView, x: int, y: int) -> TileData:
    """
    Create comprehensive TileData with all 30+ properties using PyBoy memory API.

    Args:
        memory_view: PyBoy memory view for type-safe memory access
        x: Screen X coordinate (0-19)
        y: Screen Y coordinate (0-17)

    Returns:
        Complete TileData with all properties populated
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

    # Enhanced property detection using detector class
    detector = TilePropertyDetector(memory_view)
    ledge_direction, is_ledge = detector.detect_ledge_info(tileset_id, tile_id)
    audio_props = detector.detect_audio_properties(tileset_id, tile_id)
    trainer_sight = detector.detect_trainer_sight_line(map_x, map_y)
    special_props = detector.detect_special_properties(
        tileset_id, tile_id, map_x, map_y
    )
    animation_info = detector.detect_animation_info(tileset_id, tile_id)
    interaction_props = detector.detect_interaction_properties(tileset_id, tile_id)
    environmental_props = detector.detect_environmental_properties(tileset_id, tile_id)

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
        is_ledge_tile=is_ledge,
        ledge_direction=ledge_direction,
        movement_modifier=special_props.get("movement_modifier", 1.0),
        # Environmental
        is_encounter_tile=environmental_props["is_encounter"],
        is_warp_tile=environmental_props["is_warp"],
        is_animated=animation_info["is_animated"],
        light_level=special_props.get("light_level", 15),
        # Interactions
        has_sign=interaction_props["has_sign"],
        has_bookshelf=interaction_props["has_bookshelf"],
        strength_boulder=interaction_props["strength_boulder"],
        cuttable_tree=interaction_props["cuttable_tree"],
        pc_accessible=interaction_props["pc_accessible"],
        # Battle System
        trainer_sight_line=trainer_sight["in_sight_line"],
        trainer_id=trainer_sight.get("trainer_id"),
        hidden_item_id=special_props.get("hidden_item_id"),
        requires_itemfinder=special_props.get("requires_itemfinder", False),
        # Special Zones
        safari_zone_steps=special_props.get("safari_zone_steps", False),
        game_corner_tile=special_props.get("game_corner_tile", False),
        is_fly_destination=special_props.get("is_fly_destination", False),
        # Audio/Visual
        has_footstep_sound=audio_props["has_footstep_sound"],
        sprite_priority=animation_info.get("sprite_priority", 0),
        background_priority=animation_info.get("background_priority", 0),
        elevation_pair=special_props.get("elevation_pair"),
        # Additional Properties
        sprite_offset=sprite_offset,
        blocks_light=special_props.get("blocks_light", False),
        water_current_direction=environmental_props.get("water_current_direction"),
        warp_destination_map=environmental_props.get("warp_destination_map"),
        warp_destination_x=environmental_props.get("warp_destination_x"),
        warp_destination_y=environmental_props.get("warp_destination_y"),
    )
