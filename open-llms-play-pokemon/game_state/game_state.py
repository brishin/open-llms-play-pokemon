"""
Pokemon Red Game State Representations

This module defines the data structures for representing Pokemon Red game states
and evaluation examples.
"""

from dataclasses import dataclass
from typing import Any

import dspy


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


class PokemonRedExample(dspy.Example):
    """Example for Pokemon Red evaluation"""

    def __init__(
        self,
        initial_state: PokemonRedGameState,
        final_state: PokemonRedGameState,
        actions_taken: list[str],
        time_elapsed: float,
        success_criteria: dict[str, Any],
    ):
        super().__init__(
            initial_state=initial_state,
            final_state=final_state,
            actions_taken=actions_taken,
            time_elapsed=time_elapsed,
            success_criteria=success_criteria,
        )
