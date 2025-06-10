"""
Pokemon Red Game State Representations

This module defines the data structures for representing Pokemon Red game states
and evaluation examples.
"""

from dataclasses import dataclass


@dataclass
class PokemonRedGameState:
    """Represents the current state of Pokemon Red game"""

    player_name: str
    current_map: int
    player_x: int
    player_y: int

    # Party Information
    party_count: int
    party_pokemon_levels: list[int]
    party_pokemon_hp: list[tuple]  # [(current_hp, max_hp), ...]

    badges_obtained: int
    badges_binary: int  # Binary representation of badges
    event_flags: list[int]  # Event flags as list of bits (0 or 1)

    is_in_battle: int
    player_mon_hp: tuple | None = None  # (current, max)
    enemy_mon_hp: tuple | None = None  # (current, max)
