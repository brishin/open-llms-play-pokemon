import numpy as np
from pyboy import PyBoy

from .data.tile_data_constants import DOOR_TILES, GRASS_TILES, TilesetID
from .game_state import PokemonRedGameState
from .tile_data import (
    TileData,
    TileMatrix,
    TileType,
    classify_tile_type,
    is_tile_walkable,
)


class TileReader:
    """
    Reads and processes tile data from Pokemon Red using PyBoy.

    Combines visual tile information from game_area() with collision data
    and game state to create comprehensive tile matrices.
    """

    def __init__(self, pyboy: "PyBoy"):
        """
        Initialize the tile reader.

        Args:
            pyboy: PyBoy instance (required)
        """
        self.pyboy = pyboy
        self._game_wrapper = None

    def _get_game_wrapper(self):
        """Get or create the game wrapper for accessing game_area()."""
        if self._game_wrapper is None:
            self._game_wrapper = self.pyboy.game_wrapper
        return self._game_wrapper

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
        game_wrapper = self._get_game_wrapper()
        if game_wrapper is None:
            raise ValueError("Game wrapper not available")

        # Get the raw tile matrix from PyBoy
        raw_game_area = game_wrapper.game_area()

        # Convert to numpy array for easier processing
        if hasattr(raw_game_area, "base"):
            # Handle memoryview case
            game_area_array = np.asarray(raw_game_area)
        else:
            game_area_array = np.array(raw_game_area)

        height, width = game_area_array.shape

        # Get current tileset ID (we might need to derive this from game state)
        current_tileset = self._get_current_tileset(game_state)

        # Build the tile matrix
        tiles = []
        for y in range(height):
            row = []
            for x in range(width):
                tile_id = int(game_area_array[y, x])

                # Calculate absolute map coordinates
                map_x = game_state.player_x + x + game_area_offset[0] - width // 2
                map_y = game_state.player_y + y + game_area_offset[1] - height // 2

                # Determine tile properties
                is_walkable = is_tile_walkable(tile_id, current_tileset)
                tile_type = classify_tile_type(tile_id, is_walkable, current_tileset)
                is_encounter = (
                    current_tileset in GRASS_TILES
                    and tile_id in GRASS_TILES[current_tileset]
                ) or tile_type == TileType.GRASS
                is_warp = (
                    current_tileset in DOOR_TILES
                    and tile_id in DOOR_TILES[current_tileset]
                ) or tile_type == TileType.WARP

                # Check for sprites (higher tile IDs often indicate sprites)
                sprite_offset = 0
                if hasattr(game_wrapper, "sprite_offset"):
                    sprite_offset = game_wrapper.sprite_offset

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
                    is_walkable=is_walkable,
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
        Determine the current tileset ID based on game state.

        This is a simplified implementation - in practice, you'd need to
        map current_map to tileset IDs based on Pokemon Red's map data.

        Args:
            game_state: Current game state

        Returns:
            TilesetID
        """
        # Simplified mapping - in reality this would be more complex
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
