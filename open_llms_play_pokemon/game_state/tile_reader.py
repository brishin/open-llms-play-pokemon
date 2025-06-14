import numpy as np
from pyboy import PyBoy, PyBoyMemoryView

from .data.memory_addresses import MemoryAddresses
from .data.tile_data_constants import DOOR_TILES, GRASS_TILES, TilesetID
from .game_state import PokemonRedGameState
from .tile_data import (
    TileData,
    TileMatrix,
    TileType,
    classify_tile_type,
    is_tile_walkable,
)

# Core tile reading functions using PyBoy memory API with type-safe MemoryAddresses


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


class TileReader:
    """
    Reads and processes tile data from Pokemon Red using PyBoy memory API.

    Combines visual tile information with collision data and game state
    to create comprehensive tile matrices using type-safe memory access.
    """

    def __init__(self, pyboy: "PyBoy"):
        """
        Initialize the tile reader.

        Args:
            pyboy: PyBoy instance (required)
        """
        self.pyboy = pyboy

    def get_tile_matrix(
        self, game_state: PokemonRedGameState, game_area_offset: tuple = (0, 0)
    ) -> TileMatrix:
        """
        Extract comprehensive tile data and create a TileMatrix.

        Args:
            game_state: Current game state from memory reader
            game_area_offset: Offset for mapping game_area coordinates to map coordinates

        Returns:
            TileMatrix with full tile information
        """
        if self.pyboy.game_wrapper is None:
            raise ValueError("Game wrapper not available")

        # Get PyBoy memory view for type-safe access
        memory_view = self.pyboy.memory

        # Check if map is stable before processing
        loading_status = memory_view[MemoryAddresses.map_loading_status]
        if loading_status != 0:
            # Map is transitioning, return empty matrix
            return TileMatrix(
                tiles=[],
                width=0,
                height=0,
                current_map=game_state.current_map,
                player_x=game_state.player_x,
                player_y=game_state.player_y,
            )

        # Get the raw tile matrix from PyBoy (fallback for compatibility)
        raw_game_area = self.pyboy.game_wrapper.game_area()

        # Convert to numpy array for easier processing
        if hasattr(raw_game_area, "base"):
            # Handle memoryview case
            game_area_array = np.asarray(raw_game_area)
        else:
            game_area_array = np.array(raw_game_area)

        height, width = game_area_array.shape

        # Get current tileset ID using type-safe memory access
        current_tileset = TilesetID(memory_view[MemoryAddresses.current_tileset])

        # Build the tile matrix
        tiles = []
        for y in range(height):
            row = []
            for x in range(width):
                # Use enhanced tile reading functions with type-safe memory access
                try:
                    # Read tile ID using new memory API function
                    if x < 20 and y < 18:  # Within screen bounds
                        tile_id = get_tile_id(memory_view, x, y)
                    else:
                        # Fallback to game_area for tiles outside screen buffer
                        tile_id = int(game_area_array[y, x])
                except (IndexError, ValueError):
                    # Fallback to game_area if memory read fails
                    tile_id = int(game_area_array[y, x])

                # Calculate absolute map coordinates using new function
                if x < 20 and y < 18:
                    map_x, map_y = get_map_coordinates(memory_view, x, y)
                else:
                    # Fallback calculation for compatibility
                    map_x = game_state.player_x + x + game_area_offset[0] - width // 2
                    map_y = game_state.player_y + y + game_area_offset[1] - height // 2

                # Determine tile properties using enhanced collision detection
                try:
                    # Use new collision detection function
                    is_collision = is_collision_tile(memory_view, tile_id)
                    is_walkable_tile = not is_collision
                except Exception:
                    # Fallback to tileset-specific collision tables
                    is_walkable_tile = is_tile_walkable(tile_id, current_tileset)

                tile_type = classify_tile_type(
                    tile_id, is_walkable_tile, current_tileset
                )
                is_encounter = (
                    current_tileset in GRASS_TILES
                    and tile_id in GRASS_TILES[current_tileset]
                ) or tile_type == TileType.GRASS
                is_warp = (
                    current_tileset in DOOR_TILES
                    and tile_id in DOOR_TILES[current_tileset]
                ) or tile_type == TileType.WARP

                # Enhanced sprite detection using new memory API function
                sprite_offset = 0
                if x < 20 and y < 18:  # Within screen bounds
                    try:
                        sprite_offset = get_sprite_at_position(memory_view, x, y)
                    except Exception:
                        sprite_offset = 0
                else:
                    # Fallback for compatibility
                    if hasattr(self.pyboy.game_wrapper, "sprite_offset"):
                        sprite_offset = self.pyboy.game_wrapper.sprite_offset

                tile_data = TileData(
                    # Basic Identification
                    tile_id=tile_id,
                    x=x,
                    y=y,
                    map_x=map_x,
                    map_y=map_y,
                    tile_type=tile_type,
                    tileset_id=current_tileset,
                    raw_value=tile_id,
                    # Movement/Collision
                    is_walkable=is_walkable_tile,
                    is_ledge_tile=False,  # TODO: Implement ledge detection
                    ledge_direction=None,
                    movement_modifier=1.0,
                    # Environmental
                    is_encounter_tile=is_encounter,
                    is_warp_tile=is_warp,
                    is_animated=False,  # TODO: Implement animation detection
                    light_level=15,  # Default full light
                    # Interactions
                    has_sign=False,  # TODO: Implement sign detection
                    has_bookshelf=False,
                    strength_boulder=False,
                    cuttable_tree=False,
                    pc_accessible=False,
                    # Battle System
                    trainer_sight_line=False,  # TODO: Implement trainer detection
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
                    sprite_offset=sprite_offset,
                    blocks_light=False,
                    water_current_direction=None,
                    warp_destination_map=None,
                    warp_destination_x=None,
                    warp_destination_y=None,
                )
                row.append(tile_data)
            tiles.append(row)

        return TileMatrix(
            tiles=tiles,
            width=width,
            height=height,
            current_map=game_state.current_map,
            player_x=game_state.player_x,
            player_y=game_state.player_y,
            timestamp=getattr(self.pyboy, "frame_count", None),
        )

    def get_tile_at_position(
        self, x: int, y: int, game_state: PokemonRedGameState
    ) -> TileData | None:
        """
        Get tile data at a specific position in the game area.

        Args:
            x: X coordinate in game area
            y: Y coordinate in game area
            game_state: Current game state

        Returns:
            TileData for the specified position, or None if out of bounds
        """
        tile_matrix = self.get_tile_matrix(game_state)
        return tile_matrix.get_tile(x, y)

    def get_walkable_positions(
        self, game_state: PokemonRedGameState
    ) -> list[tuple[int, int]]:
        """
        Get all walkable positions in the current game area.

        Args:
            game_state: Current game state

        Returns:
            List of (x, y) coordinates that are walkable
        """
        tile_matrix = self.get_tile_matrix(game_state)
        walkable_tiles = tile_matrix.get_walkable_tiles()
        return [(tile.x, tile.y) for tile in walkable_tiles]

    def get_encounter_positions(
        self, game_state: PokemonRedGameState
    ) -> list[tuple[int, int]]:
        """
        Get all positions where wild Pokemon encounters can occur.

        Args:
            game_state: Current game state

        Returns:
            List of (x, y) coordinates where encounters are possible
        """
        tile_matrix = self.get_tile_matrix(game_state)
        encounter_tiles = [
            tile for tile in tile_matrix.get_walkable_tiles() if tile.is_encounter_tile
        ]
        return [(tile.x, tile.y) for tile in encounter_tiles]

    def _get_current_tileset(self, game_state: PokemonRedGameState) -> TilesetID:
        """
        Determine the current tileset ID using type-safe memory access.

        Args:
            game_state: Current game state

        Returns:
            TilesetID from memory or fallback mapping
        """
        try:
            # Use type-safe memory access to get current tileset directly
            tileset_id = self.pyboy.memory[MemoryAddresses.current_tileset]
            return TilesetID(tileset_id)
        except (ValueError, Exception):
            # Fallback to simplified mapping if memory read fails
            map_to_tileset = {
                0: TilesetID.OVERWORLD,  # Pallet Town
                1: TilesetID.OVERWORLD,  # Route 1
                2: TilesetID.REDS_HOUSE_1,  # Red's House
                3: TilesetID.POKECENTER,  # Pokemon Center
                4: TilesetID.FOREST,  # Viridian Forest
                # Add more mappings based on actual Pokemon Red data
            }
            return map_to_tileset.get(game_state.current_map, TilesetID.OVERWORLD)

    def analyze_area_around_player(
        self, game_state: PokemonRedGameState, radius: int = 3
    ) -> dict:
        """
        Analyze the area around the player's current position.

        Args:
            game_state: Current game state
            radius: Radius around player to analyze

        Returns:
            Dictionary with analysis results
        """
        tile_matrix = self.get_tile_matrix(game_state)

        # Find player position in the matrix (usually center)
        player_local_x = tile_matrix.width // 2
        player_local_y = tile_matrix.height // 2

        analysis = {
            "walkable_nearby": [],
            "blocked_nearby": [],
            "encounter_tiles": [],
            "warp_tiles": [],
            "tile_types": {},
            "directions_available": {
                "north": False,
                "south": False,
                "east": False,
                "west": False,
            },
        }

        # Check each direction
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                check_x = player_local_x + dx
                check_y = player_local_y + dy

                tile = tile_matrix.get_tile(check_x, check_y)
                if tile is None:
                    continue

                distance = abs(dx) + abs(dy)  # Manhattan distance

                if tile.is_walkable:
                    analysis["walkable_nearby"].append((check_x, check_y, distance))
                else:
                    analysis["blocked_nearby"].append((check_x, check_y, distance))

                if tile.is_encounter_tile:
                    analysis["encounter_tiles"].append((check_x, check_y))

                if tile.is_warp_tile:
                    analysis["warp_tiles"].append((check_x, check_y))

                # Count tile types
                tile_type_str = tile.tile_type.value
                analysis["tile_types"][tile_type_str] = (
                    analysis["tile_types"].get(tile_type_str, 0) + 1
                )

        # Check immediate directions (1 step away)
        directions = [
            ("north", 0, -1),
            ("south", 0, 1),
            ("east", 1, 0),
            ("west", -1, 0),
        ]

        for direction, dx, dy in directions:
            check_x = player_local_x + dx
            check_y = player_local_y + dy
            tile = tile_matrix.get_tile(check_x, check_y)
            if tile and tile.is_walkable:
                analysis["directions_available"][direction] = True

        return analysis
