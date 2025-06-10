"""
Pokemon Red Memory Reader

This module provides utilities for reading Pokemon Red game state from memory/symbols.
Contains memory addresses from pokered.sym for accurate game state assessment.
"""

from pyboy import PyBoyMemoryView

from .game_state import PokemonRedGameState

MEMORY_ADDRESSES = {
    "player_name": 0xD158,
    "party_count": 0xD163,
    # Party Pokemon HP addresses (current HP)
    "party_mon_1_hp": 0xD16C,
    "party_mon_2_hp": 0xD198,
    "party_mon_3_hp": 0xD1C4,
    "party_mon_4_hp": 0xD1F0,
    "party_mon_5_hp": 0xD21C,
    "party_mon_6_hp": 0xD248,
    # Party Pokemon Max HP addresses
    "party_mon_1_max_hp": 0xD18D,
    "party_mon_2_max_hp": 0xD1B9,
    "party_mon_3_max_hp": 0xD1E5,
    "party_mon_4_max_hp": 0xD211,
    "party_mon_5_max_hp": 0xD23D,
    "party_mon_6_max_hp": 0xD269,
    # Party Pokemon Level addresses
    "party_mon_1_level": 0xD18C,
    "party_mon_2_level": 0xD1B8,
    "party_mon_3_level": 0xD1E4,
    "party_mon_4_level": 0xD210,
    "party_mon_5_level": 0xD23C,
    "party_mon_6_level": 0xD268,
    # Game state
    "obtained_badges": 0xD356,
    "current_map": 0xD35E,
    "y_coord": 0xD361,
    "x_coord": 0xD362,
    # Battle state
    "battle_mon_hp": 0xD015,
    "battle_mon_max_hp": 0xD017,  # Adding missing max HP
    "enemy_mon_hp": 0xCFE6,
    "enemy_mon_max_hp": 0xCFE8,  # Adding missing enemy max HP
    "is_in_battle": 0xD057,
    # Event flags range
    "event_flags_start": 0xD747,
    "event_flags_end": 0xD87E,
    # Opponent Pokemon levels (for difficulty tracking)
    "opp_mon_1_level": 0xD8C5,
    "opp_mon_2_level": 0xD8F1,
    "opp_mon_3_level": 0xD91D,
    "opp_mon_4_level": 0xD949,
    "opp_mon_5_level": 0xD975,
    "opp_mon_6_level": 0xD9A1,
}


class PokemonRedMemoryReader:
    """Utility class to read Pokemon Red game state from memory/symbols"""

    @staticmethod
    def parse_game_state(memory_view: PyBoyMemoryView) -> PokemonRedGameState:
        """Parse raw memory data into structured game state"""

        # Read basic game state values
        party_count = memory_view[MEMORY_ADDRESSES["party_count"]]
        badges_binary = memory_view[MEMORY_ADDRESSES["obtained_badges"]]
        badges_count = bin(badges_binary).count("1")
        is_in_battle = memory_view[MEMORY_ADDRESSES["is_in_battle"]]
        current_map = memory_view[MEMORY_ADDRESSES["current_map"]]
        player_x = memory_view[MEMORY_ADDRESSES["x_coord"]]
        player_y = memory_view[MEMORY_ADDRESSES["y_coord"]]

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

        # Read event flags using helper method
        event_flags = PokemonRedMemoryReader._read_event_bits(memory_view)

        # Battle state
        player_mon_hp = None
        enemy_mon_hp = None
        if is_in_battle == 1:
            # Read battle HP values using bulk method
            battle_addrs = [
                MEMORY_ADDRESSES["battle_mon_hp"],
                MEMORY_ADDRESSES["battle_mon_max_hp"],
                MEMORY_ADDRESSES["enemy_mon_hp"],
                MEMORY_ADDRESSES["enemy_mon_max_hp"],
            ]
            battle_hp_values = PokemonRedMemoryReader._read_multiple_16bit(
                memory_view, battle_addrs
            )

            player_mon_hp = (battle_hp_values[0], battle_hp_values[1])
            enemy_mon_hp = (battle_hp_values[2], battle_hp_values[3])

        return PokemonRedGameState(
            player_name=memory_view[MEMORY_ADDRESSES["player_name"]],
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

    @staticmethod
    def _read_16bit(memory_view: PyBoyMemoryView, start_addr: int) -> int:
        hp_bytes = memory_view[start_addr : start_addr + 2]
        return hp_bytes[0] + (hp_bytes[1] << 8)

    @staticmethod
    def _read_multiple_16bit(
        memory_view: PyBoyMemoryView, addresses: list[int]
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
        start_addr = MEMORY_ADDRESSES["event_flags_start"]
        end_addr = MEMORY_ADDRESSES["event_flags_end"]
        event_bytes = memory_view[start_addr:end_addr]

        # Convert all bytes to bits in one comprehension
        event_bits = [
            int(bin(256 + byte_val)[-bit_pos - 1])
            for byte_val in event_bytes
            for bit_pos in range(8)
        ]
        return event_bits
