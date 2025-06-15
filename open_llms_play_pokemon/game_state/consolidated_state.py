"""
Consolidated game state model optimized for logging.

This module provides a streamlined data structure for capturing the complete
game state in a format optimized for JSON serialization and logging.
"""

from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class ConsolidatedGameState:
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
    party_pokemon_hp: list[tuple[int, int]]
    badges_obtained: int
    is_in_battle: bool
    player_mon_hp: tuple[int, int] | None
    enemy_mon_hp: tuple[int, int] | None

    # Memory state
    map_loading_status: int
    current_tileset: int

    # All tiles data (no radius filtering)
    walkable_tiles: list[tuple[int, int, int]]  # [(x, y, distance), ...]
    blocked_tiles: list[tuple[int, int, int]]  # [(x, y, distance), ...]
    encounter_tiles: list[tuple[int, int]]  # [(x, y), ...]
    warp_tiles: list[tuple[int, int]]  # [(x, y), ...]
    interactive_tiles: list[tuple[int, int]]  # [(x, y), ...]

    # Tile type counts (all tiles on screen)
    tile_type_counts: dict[str, int]

    # Movement options (immediate neighbors only)
    directions_available: dict[str, bool]

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for MLFlow logging
        """
        return asdict(self)
