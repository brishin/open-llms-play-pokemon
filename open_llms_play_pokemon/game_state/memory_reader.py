from collections.abc import Sequence

from pyboy import PyBoy, PyBoyMemoryView
from pyboy.plugins.game_wrapper_pokemon_gen1 import GameWrapperPokemonGen1

from .consolidated_state import ConsolidatedGameState
from .data.memory_addresses import MemoryAddresses
from .game_state import PokemonRedGameState
from .screen_analyzer import (
    analyze_screen,
    categorize_tiles,
)


class PokemonRedMemoryReader:
    """Utility class to read Pokemon Red game state from memory/symbols"""

    # Player is always at screen center
    PLAYER_CENTER_X, PLAYER_CENTER_Y = 10, 9

    def __init__(self, pyboy):
        self.pyboy = pyboy

    @staticmethod
    def parse_game_state(pyboy: PyBoy) -> PokemonRedGameState:
        """Parse raw memory data into structured game state"""
        memory_view = pyboy.memory

        # Read basic game state values
        party_count = memory_view[MemoryAddresses.party_count]
        badges_binary = memory_view[MemoryAddresses.obtained_badges]
        badges_count = bin(badges_binary).count("1")
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
            party_hp = list(zip(current_hps, max_hps, strict=True))

        game_wrapper = pyboy.game_wrapper
        if isinstance(game_wrapper, GameWrapperPokemonGen1):
            print(game_wrapper)
            print(game_wrapper.game_area())
            print(game_wrapper.game_area_collision())

        # Read event flags using helper method
        event_flags = PokemonRedMemoryReader._read_event_bits(memory_view)

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

            player_mon_hp = (battle_hp_values[0], battle_hp_values[1])
            enemy_mon_hp = (battle_hp_values[2], battle_hp_values[3])

        return PokemonRedGameState(
            player_name=memory_view[MemoryAddresses.player_name],
            current_map=current_map,
            player_x=player_x,
            player_y=player_y,
            party_count=party_count,
            party_pokemon_levels=party_levels,
            party_pokemon_hp=party_hp,
            badges_obtained=badges_count,
            badges_binary=badges_binary,
            is_in_battle=bool(is_in_battle),
            player_mon_hp=player_mon_hp,
            enemy_mon_hp=enemy_mon_hp,
            event_flags=event_flags,
        )

    def _process_tile_data(self, memory_view: PyBoyMemoryView) -> dict:
        """
        Single method to process all tile data consistently.

        Args:
            memory_view: PyBoy memory view for type-safe memory access

        Returns:
            Dictionary with all processed tile data
        """
        # Get all tiles in one pass
        tile_categories = categorize_tiles(memory_view)
        all_tiles = analyze_screen(memory_view)

        return {
            "walkable_tiles": self._extract_tile_coordinates_with_distance(
                tile_categories["walkable"]
            ),
            "blocked_tiles": self._extract_tile_coordinates_with_distance(
                tile_categories["blocked"]
            ),
            "encounter_tiles": self._extract_tile_coordinates(
                tile_categories["encounters"]
            ),
            "warp_tiles": self._extract_tile_coordinates(tile_categories["warps"]),
            "interactive_tiles": self._extract_tile_coordinates(
                tile_categories["interactive"]
            ),
            "tile_type_counts": self._count_tile_types(all_tiles),
            "directions_available": self._check_immediate_directions(
                all_tiles, self.PLAYER_CENTER_X, self.PLAYER_CENTER_Y
            ),
        }

    def get_consolidated_game_state(
        self, memory_view: PyBoyMemoryView
    ) -> ConsolidatedGameState:
        """
        Get all game data in a single, optimized call.
        Returns all tiles without radius filtering.

        Args:
            memory_view: PyBoy memory view for type-safe memory access

        Returns:
            ConsolidatedGameState with all game data optimized for logging
        """
        # Parse base game state (with event_flags)
        game_state = self.parse_game_state(self.pyboy)

        # Process all tile data using unified method
        tile_data = self._process_tile_data(memory_view)

        # Read memory state
        try:
            map_loading_status = memory_view[MemoryAddresses.map_loading_status]
            current_tileset = memory_view[MemoryAddresses.current_tileset]
        except Exception:
            map_loading_status = 0
            current_tileset = 0

        # Only include fields that exist in ConsolidatedGameState
        game_data = game_state.to_dict()
        filtered_game_data = {
            k: v
            for k, v in game_data.items()
            if k
            in [
                "player_name",
                "current_map",
                "player_x",
                "player_y",
                "party_count",
                "party_pokemon_levels",
                "party_pokemon_hp",
                "badges_obtained",
                "is_in_battle",
                "player_mon_hp",
                "enemy_mon_hp",
            ]
        }

        return ConsolidatedGameState(
            # Runtime fields (to be set by caller)
            step_counter=0,
            timestamp="",
            # Game state fields (excluding event_flags and badges_binary)
            **filtered_game_data,
            # Memory state
            map_loading_status=map_loading_status,
            current_tileset=current_tileset,
            # All tiles data
            **tile_data,
        )

    def _check_immediate_directions(
        self, all_tiles: list, player_center_x: int, player_center_y: int
    ) -> dict[str, bool]:
        """Check walkability of immediate neighboring tiles."""
        directions = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
        }

        directions_available = {}
        for direction, (dx, dy) in directions.items():
            check_x = player_center_x + dx
            check_y = player_center_y + dy
            # Find tile at this position
            tile = next(
                (t for t in all_tiles if t.x == check_x and t.y == check_y), None
            )
            directions_available[direction] = bool(tile and tile.is_walkable)

        return directions_available

    @staticmethod
    def _calculate_distance(tile_x: int, tile_y: int) -> int:
        """Calculate Manhattan distance from player center."""
        return abs(tile_x - PokemonRedMemoryReader.PLAYER_CENTER_X) + abs(
            tile_y - PokemonRedMemoryReader.PLAYER_CENTER_Y
        )

    @staticmethod
    def _extract_tile_coordinates(tiles: list) -> list[tuple[int, int]]:
        """Extract (x, y) coordinates from tiles."""
        return [(t.x, t.y) for t in tiles]

    @staticmethod
    def _extract_tile_coordinates_with_distance(
        tiles: list,
    ) -> list[tuple[int, int, int]]:
        """Extract (x, y, distance) coordinates from tiles."""
        return [
            (t.x, t.y, PokemonRedMemoryReader._calculate_distance(t.x, t.y))
            for t in tiles
        ]

    @staticmethod
    def _count_tile_types(all_tiles: list) -> dict[str, int]:
        """Count tiles by type."""
        tile_type_counts = {}
        for tile in all_tiles:
            tile_type_str = tile.tile_type.value
            tile_type_counts[tile_type_str] = tile_type_counts.get(tile_type_str, 0) + 1
        return tile_type_counts

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
