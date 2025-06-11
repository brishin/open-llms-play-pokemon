from collections.abc import Sequence

from pyboy import PyBoy, PyBoyMemoryView
from pyboy.plugins.game_wrapper_pokemon_gen1 import GameWrapperPokemonGen1

from .data import MemoryAddresses
from .game_state import PokemonRedGameState
from .tile_data import TileMatrix
from .tile_reader import TileReader


class PokemonRedMemoryReader:
    """Utility class to read Pokemon Red game state from memory/symbols"""

    def __init__(self, pyboy):
        self.tile_reader = TileReader(pyboy)
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
            is_in_battle=is_in_battle,
            player_mon_hp=player_mon_hp,
            enemy_mon_hp=enemy_mon_hp,
            event_flags=event_flags,
        )

    def parse_game_state_with_tiles(
        self, memory_view: PyBoyMemoryView
    ) -> tuple[PokemonRedGameState, TileMatrix]:
        """
        Parse game state and include tile data if available.

        Args:
            memory_view: PyBoy memory view

        Returns:
            Tuple of (game_state, tile_matrix)
            tile_matrix will be None if tile reading is not available
        """

        game_state = self.parse_game_state(self.pyboy)
        tile_matrix = self.tile_reader.get_tile_matrix(game_state)

        return game_state, tile_matrix

    def get_comprehensive_game_data(self, memory_view: PyBoyMemoryView) -> dict:
        game_state, tile_matrix = self.parse_game_state_with_tiles(memory_view)

        data = {
            "game_state": {
                "player_name": game_state.player_name,
                "current_map": game_state.current_map,
                "player_x": game_state.player_x,
                "player_y": game_state.player_y,
                "party_count": game_state.party_count,
                "party_pokemon_levels": game_state.party_pokemon_levels,
                "party_pokemon_hp": game_state.party_pokemon_hp,
                "badges_obtained": game_state.badges_obtained,
                "badges_binary": game_state.badges_binary,
                "is_in_battle": game_state.is_in_battle,
                "player_mon_hp": game_state.player_mon_hp,
                "enemy_mon_hp": game_state.enemy_mon_hp,
                "event_flags": game_state.event_flags,
            },
            "tile_data": None,
            "analysis": None,
        }

        if tile_matrix is not None:
            data["tile_data"] = tile_matrix.to_dict()

            # Add quick analysis
            try:
                analysis = self.tile_reader.analyze_area_around_player(game_state)
                data["analysis"] = analysis
            except Exception as e:
                print(f"Warning: Could not analyze area: {e}")

        return data

    def get_tile_matrix(self, memory_view: PyBoyMemoryView) -> TileMatrix | None:
        """
        Get just the tile matrix data.

        Args:
            memory_view: PyBoy memory view

        Returns:
            TileMatrix or None if not available
        """

        game_state = self.parse_game_state(self.pyboy)
        try:
            return self.tile_reader.get_tile_matrix(game_state)
        except Exception as e:
            print(f"Warning: Could not read tile matrix: {e}")
            return None

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
