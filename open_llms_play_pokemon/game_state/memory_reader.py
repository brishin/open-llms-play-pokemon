from collections.abc import Sequence

from pyboy import PyBoyMemoryView

from .data.memory_addresses import MemoryAddresses
from .game_state import (
    DirectionsAvailable,
    PokemonHp,
    PokemonRedGameState,
)
from .screen_analyzer import analyze_screen
from .tile_data import TileMatrix
from .tile_data_factory import TileDataFactory


class PokemonRedMemoryReader:
    """Utility class to read Pokemon Red game state from memory/symbols"""

    # Player is always at screen center
    PLAYER_CENTER_X, PLAYER_CENTER_Y = 10, 9

    def __init__(self, pyboy):
        self.pyboy = pyboy

    def parse_game_state(
        self, memory_view: PyBoyMemoryView, step_counter: int = 0, timestamp: str = ""
    ) -> PokemonRedGameState:
        """Parse raw memory data into new PokemonRedGameState format"""

        # Read basic game state values
        party_count = memory_view[MemoryAddresses.party_count]
        badges_count = bin(memory_view[MemoryAddresses.obtained_badges]).count("1")
        is_in_battle = memory_view[MemoryAddresses.is_in_battle]
        current_map = memory_view[MemoryAddresses.current_map]
        player_x = memory_view[MemoryAddresses.x_coord]
        player_y = memory_view[MemoryAddresses.y_coord]

        # Parse party Pokemon data using bulk slice reads
        party_levels = []
        party_hp = []

        if party_count > 0:
            level_addrs = [0xD18C, 0xD1B8, 0xD1E4, 0xD210, 0xD23C, 0xD268]
            hp_addrs = [0xD16C, 0xD198, 0xD1C4, 0xD1F0, 0xD21C, 0xD248]
            max_hp_addrs = [0xD18D, 0xD1B9, 0xD1E5, 0xD211, 0xD23D, 0xD269]

            count = min(party_count, 6)

            party_levels = [
                memory_view[level_addr] for level_addr in level_addrs[:count]
            ]

            current_hps = PokemonRedMemoryReader._read_multiple_16bit(
                memory_view, hp_addrs[:count]
            )
            max_hps = PokemonRedMemoryReader._read_multiple_16bit(
                memory_view, max_hp_addrs[:count]
            )
            party_hp = [
                PokemonHp(current=current, max=max_hp)
                for current, max_hp in zip(current_hps, max_hps, strict=True)
            ]

        # Battle state
        player_mon_hp = None
        enemy_mon_hp = None
        if is_in_battle:
            # Read battle HP values using bulk method
            battle_addrs = [
                MemoryAddresses.battle_mon_hp,
                MemoryAddresses.battle_mon_max_hp,
                MemoryAddresses.enemy_mon_hp,
                MemoryAddresses.enemy_mon_max_hp,
            ]
            battle_hp_values = PokemonRedMemoryReader._read_multiple_16bit(
                memory_view, battle_addrs
            )

            player_mon_hp = PokemonHp(
                current=battle_hp_values[0], max=battle_hp_values[1]
            )
            enemy_mon_hp = PokemonHp(
                current=battle_hp_values[2], max=battle_hp_values[3]
            )

        # Read memory state
        map_loading_status = memory_view[MemoryAddresses.map_loading_status]
        current_tileset = memory_view[MemoryAddresses.current_tileset]

        # Process all tile data using unified method
        tile_data = self._process_tile_data(memory_view)

        return PokemonRedGameState(
            step_counter=step_counter,
            timestamp=timestamp,
            player_name=memory_view[MemoryAddresses.player_name],
            current_map=current_map,
            player_x=player_x,
            player_y=player_y,
            party_count=party_count,
            party_pokemon_levels=party_levels,
            party_pokemon_hp=party_hp,
            badges_obtained=badges_count,
            is_in_battle=bool(is_in_battle),
            player_mon_hp=player_mon_hp,
            enemy_mon_hp=enemy_mon_hp,
            map_loading_status=map_loading_status,
            current_tileset=current_tileset,
            tile_matrix=tile_data["tile_matrix"],
            directions_available=tile_data["directions_available"],
        )

    def _process_tile_data(self, memory_view: PyBoyMemoryView) -> dict:
        """
        Process tile data and create TileMatrix with movement analysis.

        Args:
            memory_view: PyBoy memory view for type-safe memory access

        Returns:
            Dictionary with tile matrix and directions available
        """
        # Get all tiles in one pass
        all_tiles = analyze_screen(memory_view)

        # Create TileMatrix from all_tiles (20x18 screen)
        tile_matrix = self._create_tile_matrix(memory_view, all_tiles)

        return {
            "tile_matrix": tile_matrix,
            "directions_available": self._check_immediate_directions(
                all_tiles, self.PLAYER_CENTER_X, self.PLAYER_CENTER_Y
            ),
        }

    def _check_immediate_directions(
        self, all_tiles: list, player_center_x: int, player_center_y: int
    ) -> DirectionsAvailable:
        """Check walkability of immediate neighboring tiles."""
        directions = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
        }

        directions_dict = {}
        for direction, (dx, dy) in directions.items():
            check_x = player_center_x + dx
            check_y = player_center_y + dy
            # Find tile at this position
            tile = next(
                (t for t in all_tiles if t.x == check_x and t.y == check_y), None
            )
            directions_dict[direction] = bool(tile and tile.is_walkable)

        return DirectionsAvailable(
            north=directions_dict["north"],
            south=directions_dict["south"],
            east=directions_dict["east"],
            west=directions_dict["west"],
        )

    def _create_tile_matrix(
        self, memory_view: PyBoyMemoryView, all_tiles: list
    ) -> TileMatrix:
        """
        Create a TileMatrix from the list of tiles.

        Args:
            memory_view: PyBoy memory view for getting player position and map info
            all_tiles: List of TileData objects from analyze_screen

        Returns:
            TileMatrix with 2D array of tiles
        """
        # GameBoy screen is 20x18 tiles
        width, height = 20, 18

        # Initialize 2D matrix with placeholder tiles
        matrix = [
            [TileDataFactory.create_placeholder(x, y) for x in range(width)]
            for y in range(height)
        ]

        # Fill matrix with actual tiles
        for tile in all_tiles:
            if 0 <= tile.x < width and 0 <= tile.y < height:
                matrix[tile.y][tile.x] = tile

        # Get current map info
        current_map = memory_view[MemoryAddresses.current_map]
        player_x = memory_view[MemoryAddresses.x_coord]
        player_y = memory_view[MemoryAddresses.y_coord]

        return TileMatrix(
            tiles=matrix,
            width=width,
            height=height,
            current_map=current_map,
            player_x=player_x,
            player_y=player_y,
            timestamp=None,  # Could add frame counter if needed
        )

    @staticmethod
    def _read_16bit(memory_view: PyBoyMemoryView, start_addr: int) -> int:
        hp_bytes = memory_view[start_addr : start_addr + 2]
        return hp_bytes[0] + (hp_bytes[1] << 8)

    @staticmethod
    def _read_multiple_16bit(
        memory_view: PyBoyMemoryView, addresses: Sequence[int]
    ) -> list[int]:
        """Read multiple 16-bit values efficiently"""
        values = []
        for addr in addresses:
            bytes_data = memory_view[addr : addr + 2]
            values.append(bytes_data[0] + (bytes_data[1] << 8))
        return values

    @staticmethod
    def _read_event_bits(memory_view: PyBoyMemoryView) -> list[int]:
        """Read all event flag bits using slice syntax"""
        start_addr = MemoryAddresses.event_flags_start
        end_addr = MemoryAddresses.event_flags_end
        event_bytes = memory_view[start_addr:end_addr]

        # Convert all bytes to bits in one comprehension
        event_bits = [
            int(bin(256 + byte_val)[-bit_pos - 1])
            for byte_val in event_bytes
            for bit_pos in range(8)
        ]
        return event_bits
