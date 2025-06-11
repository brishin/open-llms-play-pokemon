"""Game state reading and analysis for Pokemon Red."""

from .game_state import PokemonRedGameState
from .memory_reader import PokemonRedMemoryReader

# Try to import tile data classes
try:
    from .tile_data import TileData, TileMatrix, TileType
    from .tile_reader import TileReader
    TILE_CLASSES_AVAILABLE = True
except ImportError:
    TILE_CLASSES_AVAILABLE = False

__all__ = [
    "PokemonRedGameState",
    "PokemonRedMemoryReader",
]

if TILE_CLASSES_AVAILABLE:
    __all__.extend(["TileData", "TileMatrix", "TileType", "TileReader"])
