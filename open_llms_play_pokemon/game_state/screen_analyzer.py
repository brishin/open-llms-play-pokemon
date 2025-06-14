"""Screen analysis and batch processing functions for Pokemon Red tile extraction.

This module provides functions for analyzing entire screen areas (20x18 tiles) and
categorizing tiles for AI decision-making.
"""

from pyboy import PyBoyMemoryView

from .data.memory_addresses import MemoryAddresses
from .data.tile_data_constants import TilesetID
from .enhanced_tile_creator import create_tile_data
from .tile_data import TileData, TileType


def analyze_screen(memory_view: PyBoyMemoryView) -> list[TileData]:
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
        if loading_status != 0:  # Map is transitioning
            return []
    except Exception:
        # If we can't read loading status, assume map is stable for tests
        pass

    tiles = []
    for y in range(18):  # Screen height
        for x in range(20):  # Screen width
            try:
                tile_data = create_tile_data(memory_view, x, y)
                tiles.append(tile_data)
            except Exception:
                # Skip problematic tiles during batch processing
                continue

    return tiles


def get_walkable_tiles(memory_view: PyBoyMemoryView) -> list[TileData]:
    """
    Get all walkable tiles on the current screen.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        List of walkable TileData objects
    """
    screen_tiles = analyze_screen(memory_view)
    return [tile for tile in screen_tiles if tile.is_walkable]


def get_interactive_tiles(memory_view: PyBoyMemoryView) -> list[TileData]:
    """
    Get all interactive tiles (signs, NPCs, items, etc.) on screen.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        List of interactive TileData objects
    """
    screen_tiles = analyze_screen(memory_view)
    return [
        tile
        for tile in screen_tiles
        if (
            tile.has_sign
            or tile.hidden_item_id is not None
            or tile.has_bookshelf
            or tile.cuttable_tree
            or tile.strength_boulder
        )
    ]


def get_encounter_tiles(memory_view: PyBoyMemoryView) -> list[TileData]:
    """
    Get all tiles where wild Pokemon encounters can occur.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        List of encounter TileData objects (grass, water, caves)
    """
    screen_tiles = analyze_screen(memory_view)
    return [tile for tile in screen_tiles if tile.is_encounter_tile]


def get_warp_tiles(memory_view: PyBoyMemoryView) -> list[TileData]:
    """
    Get all warp/transition tiles (doors, stairs, etc.) on screen.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        List of warp TileData objects
    """
    screen_tiles = analyze_screen(memory_view)
    return [tile for tile in screen_tiles if tile.is_warp_tile]


def categorize_tiles(memory_view: PyBoyMemoryView) -> dict:
    """
    Group tiles by type and properties for comprehensive game analysis.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        Dictionary with categorized tiles and metadata
    """
    # Validate memory state before processing
    try:
        current_map = memory_view[MemoryAddresses.current_map]
        tileset_id = TilesetID(memory_view[MemoryAddresses.current_tileset])
    except (ValueError, KeyError):
        # Return empty result if memory state is invalid
        return {
            "water": [],
            "trees": [],
            "grass": [],
            "doors": [],
            "walkable": [],
            "blocked": [],
            "interactive": [],
            "encounters": [],
            "warps": [],
            "special": [],
            "metadata": {
                "current_map": None,
                "tileset_id": None,
                "total_tiles": 0,
                "analysis_successful": False,
            },
        }

    screen_tiles = analyze_screen(memory_view)

    # Group tiles by type
    water_tiles = [t for t in screen_tiles if t.tile_type == TileType.WATER]
    tree_tiles = [t for t in screen_tiles if t.tile_type == TileType.TREE]
    grass_tiles = [t for t in screen_tiles if t.tile_type == TileType.GRASS]
    door_tiles = [t for t in screen_tiles if t.tile_type == TileType.WARP]

    # Group by properties
    walkable_tiles = [t for t in screen_tiles if t.is_walkable]
    blocked_tiles = [t for t in screen_tiles if not t.is_walkable]
    interactive_tiles = get_interactive_tiles(memory_view)
    encounter_tiles = get_encounter_tiles(memory_view)
    warp_tiles = get_warp_tiles(memory_view)

    # Special tiles (ledges, animated, etc.)
    special_tiles = [
        t
        for t in screen_tiles
        if (t.is_ledge_tile or t.is_animated or t.elevation_pair is not None)
    ]

    return {
        "water": water_tiles,
        "trees": tree_tiles,
        "grass": grass_tiles,
        "doors": door_tiles,
        "walkable": walkable_tiles,
        "blocked": blocked_tiles,
        "interactive": interactive_tiles,
        "encounters": encounter_tiles,
        "warps": warp_tiles,
        "special": special_tiles,
        "metadata": {
            "current_map": current_map,
            "tileset_id": tileset_id,
            "total_tiles": len(screen_tiles),
            "analysis_successful": True,
            "walkable_count": len(walkable_tiles),
            "blocked_count": len(blocked_tiles),
            "interactive_count": len(interactive_tiles),
        },
    }


def get_comprehensive_game_data(memory_view: PyBoyMemoryView) -> dict:
    """
    Get comprehensive game state data including all tile categories and metadata.

    This is the main function for AI agents to get complete environmental data.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        Comprehensive dictionary with all game state information
    """
    # Get categorized tiles
    tile_categories = categorize_tiles(memory_view)

    # Add player position context
    try:
        player_x = memory_view[MemoryAddresses.x_coord]
        player_y = memory_view[MemoryAddresses.y_coord]
        player_direction = None  # Not available in current memory addresses
    except (ValueError, KeyError):
        player_x = player_y = player_direction = None

    # Add map context
    try:
        map_width = memory_view[MemoryAddresses.current_map_width]
        map_height = memory_view[MemoryAddresses.current_map_height]
        is_indoors = None  # Not available in current memory addresses
    except (ValueError, KeyError):
        map_width = map_height = is_indoors = None

    return {
        **tile_categories,
        "player_context": {
            "position": (player_x, player_y),
            "direction": player_direction,
            "screen_center": (10, 9),  # Player is always at screen center
        },
        "map_context": {
            "dimensions": (map_width, map_height),
            "is_indoors": bool(is_indoors) if is_indoors is not None else None,
            "screen_dimensions": (20, 18),  # Game Boy screen tile dimensions
        },
    }


def find_nearest_tiles(
    memory_view: PyBoyMemoryView, tile_type: TileType, max_count: int = 5
) -> list[TileData]:
    """
    Find nearest tiles of a specific type to the player.

    Args:
        memory_view: PyBoy memory view for accessing game memory
        tile_type: Type of tiles to search for
        max_count: Maximum number of tiles to return

    Returns:
        List of nearest TileData objects of the specified type
    """
    screen_tiles = analyze_screen(memory_view)
    matching_tiles = [t for t in screen_tiles if t.tile_type == tile_type]

    # Sort by distance from screen center (player position)
    center_x, center_y = 10, 9
    matching_tiles.sort(key=lambda t: abs(t.x - center_x) + abs(t.y - center_y))

    return matching_tiles[:max_count]


def get_movement_options(memory_view: PyBoyMemoryView) -> dict:
    """
    Analyze movement options from current player position.

    Args:
        memory_view: PyBoy memory view for accessing game memory

    Returns:
        Dictionary with directional movement analysis
    """
    try:
        # Get tiles adjacent to player (center of screen)
        center_x, center_y = 10, 9
        screen_tiles = analyze_screen(memory_view)

        # Create a lookup for quick tile access
        tile_lookup = {(t.x, t.y): t for t in screen_tiles}

        # Check each direction
        directions = {
            "up": (center_x, center_y - 1),
            "down": (center_x, center_y + 1),
            "left": (center_x - 1, center_y),
            "right": (center_x + 1, center_y),
        }

        movement_options = {}
        for direction, (x, y) in directions.items():
            tile = tile_lookup.get((x, y))
            if tile:
                movement_options[direction] = {
                    "walkable": tile.is_walkable,
                    "tile_type": tile.tile_type,
                    "is_warp": tile.is_warp_tile,
                    "is_encounter": tile.is_encounter_tile,
                    "is_interactive": (
                        tile.has_sign
                        or tile.hidden_item_id is not None
                        or tile.has_bookshelf
                        or tile.cuttable_tree
                        or tile.strength_boulder
                    ),
                    "tile_data": tile,
                }
            else:
                movement_options[direction] = {
                    "walkable": False,
                    "tile_type": None,
                    "is_warp": False,
                    "is_encounter": False,
                    "is_interactive": False,
                    "tile_data": None,
                }

        return movement_options

    except Exception:
        # Return safe defaults if analysis fails
        return {
            direction: {
                "walkable": False,
                "tile_type": None,
                "is_warp": False,
                "is_encounter": False,
                "is_interactive": False,
                "tile_data": None,
            }
            for direction in ["up", "down", "left", "right"]
        }
