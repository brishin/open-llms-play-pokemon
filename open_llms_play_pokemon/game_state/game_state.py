"""
Pokemon Red Game State Representations

This module defines the data structures for representing Pokemon Red game states
and evaluation examples.
"""

from dataclasses import asdict, dataclass

from .tile_data import TileMatrix


@dataclass(slots=True, frozen=True)
class PokemonHp:
    """Represents Pokemon HP with current and max values."""

    current: int
    max: int


@dataclass(slots=True, frozen=True)
class DirectionsAvailable:
    """Represents available movement directions."""

    north: bool
    south: bool
    east: bool
    west: bool


@dataclass(slots=True, frozen=True)
class PokemonRedGameState:
    """Optimized state for logging - excludes event_flags for efficiency."""

    # Runtime metadata
    step_counter: int
    timestamp: str

    # Core game state
    player_name: str
    current_map: int
    player_x: int
    player_y: int
    party_count: int
    party_pokemon_levels: list[int]
    party_pokemon_hp: list[PokemonHp]
    badges_obtained: int
    is_in_battle: bool
    player_mon_hp: PokemonHp | None
    enemy_mon_hp: PokemonHp | None

    # Memory state
    map_loading_status: int
    current_tileset: int

    # Complete 2D tile matrix for spatial analysis
    tile_matrix: TileMatrix

    # Movement options (immediate neighbors only)
    directions_available: DirectionsAvailable

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for MLFlow logging
        """
        return asdict(self)
