"""
Pokemon Red Game State Representations

This module defines the data structures for representing Pokemon Red game states
and evaluation examples.
"""

from dataclasses import asdict, dataclass, field
from typing import Any


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
    event_flags: list[int] = field(repr=False)  # Event flags as list of bits (0 or 1)

    is_in_battle: bool
    player_mon_hp: tuple | None = None  # (current, max)
    enemy_mon_hp: tuple | None = None  # (current, max)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary, always excluding event_flags for serialization.

        Returns:
            Dictionary representation of game state without event_flags
        """
        data = asdict(self)
        data.pop("event_flags", None)  # Remove event_flags if present
        return data


@dataclass
class PokemonRedExample:
    """Represents an example for Pokemon Red evaluation."""

    initial_state: PokemonRedGameState
    final_state: PokemonRedGameState
    actions_taken: list[str]
    time_elapsed: float
    success_criteria: dict[str, Any]
