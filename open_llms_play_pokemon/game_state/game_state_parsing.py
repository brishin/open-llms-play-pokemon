import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from open_llms_play_pokemon.emulation.game_emulator import GameEmulator
from open_llms_play_pokemon.game_state.memory_reader import PokemonRedMemoryReader

logger = logging.getLogger(__name__)


def get_game_state_json(state_file_path: str) -> dict[str, Any]:
    """
    Extract comprehensive game state data from a Pokemon Red .state file.

    This function loads a PyBoy .state file and parses it into comprehensive JSON format
    containing player data, party information, tile analysis, and environmental data.

    Args:
        state_file_path: Relative path to the .state file from project root
                        (e.g., "game/init.state", "captures/gamestate_20250620_110159.state")

    Returns:
        Dict containing comprehensive game state data including:
        - step_counter, timestamp: Runtime metadata
        - player_name, current_map, player_x, player_y: Player position data
        - party_count, party_pokemon_levels, party_pokemon_hp: Party information
        - badges_obtained, is_in_battle: Game progress data
        - player_mon_hp, enemy_mon_hp: Battle HP data
        - map_loading_status, current_tileset: Memory state data
        - tile_matrix: Comprehensive tile analysis (20x18 grid)
        - directions_available: Movement analysis
        - file_metadata: File information and load timestamp

    Raises:
        FileNotFoundError: If the state file doesn't exist
        RuntimeError: If there's an error loading or parsing the state
    """
    try:
        # Resolve the file path relative to project root
        project_root = _get_project_root()
        full_path = project_root / state_file_path

        if not full_path.exists():
            raise FileNotFoundError(f"State file not found: {full_path}")

        logger.info(f"Loading game state from: {full_path}")

        emulator = GameEmulator(headless=True)
        memory_reader = PokemonRedMemoryReader(emulator.pyboy)

        try:
            with open(full_path, "rb") as f:
                emulator.pyboy.load_state(f)

            # Let the emulator tick once to ensure state is fully loaded
            emulator.pyboy.tick()

            # Parse the game state
            memory_view = emulator.pyboy.memory
            game_state = memory_reader.parse_game_state(
                memory_view,
                step_counter=0,  # We don't know the original step counter from .state file
                timestamp=datetime.now().isoformat(),
            )

            # Convert to dictionary and add metadata about the file
            result = game_state.to_dict()
            result["file_metadata"] = {
                "source_file": str(state_file_path),
                "file_size_bytes": full_path.stat().st_size,
                "file_modified": datetime.fromtimestamp(
                    full_path.stat().st_mtime
                ).isoformat(),
                "loaded_at": datetime.now().isoformat(),
            }

            # Get tile count for logging
            tile_count = len(result.get("tile_matrix", {}).get("tiles", []))
            logger.info(f"Successfully parsed game state with {tile_count} tiles")
            return result

        finally:
            # Clean up the emulator
            emulator.cleanup()

    except FileNotFoundError as e:
        error_msg = f"State file not found: {state_file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg) from e

    except Exception as e:
        error_msg = f"Error loading game state from {state_file_path}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def _get_project_root() -> Path:
    """Get the project root directory."""
    current_dir = Path(__file__).parent
    # Navigate up to find the project root (where pyproject.toml is)
    while current_dir.parent != current_dir:
        if (current_dir / "pyproject.toml").exists():
            return current_dir
        current_dir = current_dir.parent
    raise RuntimeError("Could not find project root directory")
