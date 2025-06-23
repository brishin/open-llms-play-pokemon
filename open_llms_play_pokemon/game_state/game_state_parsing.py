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


def format_game_state_text(game_state: dict[str, Any]) -> str:
    """
    Format game state data into a concise, high-information-density text format
    optimized for LLM consumption and human readability.

    Args:
        game_state: Game state dictionary from get_game_state_json()

    Returns:
        Formatted text representation of the game state
    """
    lines = []

    # Header with step counter
    step = game_state.get("step_counter", "?")
    lines.append(f"=== POKEMON RED STATE (Step {step}) ===")

    # Location and position info
    current_map = game_state.get("current_map", "?")
    player_x = game_state.get("player_x", "?")
    player_y = game_state.get("player_y", "?")
    lines.append(f"Location: Map {current_map} at ({player_x},{player_y})")

    # Movement options
    directions = game_state.get("directions_available", {})
    if directions:
        movement_symbols = []
        if directions.get("north", False):
            movement_symbols.append("↑N")
        if directions.get("south", False):
            movement_symbols.append("↓S")
        if directions.get("east", False):
            movement_symbols.append("→E")
        if directions.get("west", False):
            movement_symbols.append("←W")

        blocked = []
        if not directions.get("north", True):
            blocked.append("North")
        if not directions.get("south", True):
            blocked.append("South")
        if not directions.get("east", True):
            blocked.append("East")
        if not directions.get("west", True):
            blocked.append("West")

        movement_text = (
            " ".join(movement_symbols) if movement_symbols else "No movement"
        )
        if blocked:
            movement_text += f" ({', '.join(blocked)} blocked)"
        lines.append(f"Movement: {movement_text}")

    lines.append("")  # Blank line

    # Player info
    player_name = game_state.get("player_name", "PLAYER")
    party_count = game_state.get("party_count", 0)
    badges = game_state.get("badges_obtained", 0)
    is_in_battle = game_state.get("is_in_battle", False)
    battle_status = "Yes" if is_in_battle else "No"

    lines.append(
        f"PLAYER: {player_name} | Party: {party_count}/6 | Badges: {badges}/8 | Battle: {battle_status}"
    )
    lines.append("")

    # Pokemon party info
    if party_count > 0:
        lines.append("POKEMON PARTY:")
        party_levels = game_state.get("party_pokemon_levels", [])
        party_hp = game_state.get("party_pokemon_hp", [])

        for i in range(min(party_count, len(party_levels))):
            level = party_levels[i] if i < len(party_levels) else "?"

            # Handle HP data
            if i < len(party_hp) and isinstance(party_hp[i], dict):
                current_hp = party_hp[i].get("current", "?")
                max_hp = party_hp[i].get("max", "?")
                hp_text = f"[{current_hp}/{max_hp} HP]"

                # Health status
                if (
                    isinstance(current_hp, int)
                    and isinstance(max_hp, int)
                    and max_hp > 0
                ):
                    hp_percent = current_hp / max_hp
                    if hp_percent > 0.75:
                        status = "Healthy"
                    elif hp_percent > 0.25:
                        status = "Injured"
                    elif hp_percent > 0:
                        status = "Critical"
                    else:
                        status = "Fainted"
                else:
                    status = "Unknown"
            else:
                hp_text = "[? HP]"
                status = "Unknown"

            species = (
                f"Pokemon #{i + 1}"  # Default since we don't have species mapping yet
            )
            lines.append(f"• {species} Lv.{level} {hp_text} {status}")
        lines.append("")

    # Battle status
    if is_in_battle:
        lines.append("BATTLE STATUS:")
        player_mon_hp = game_state.get("player_mon_hp")
        enemy_mon_hp = game_state.get("enemy_mon_hp")

        if player_mon_hp and isinstance(player_mon_hp, dict):
            p_current = player_mon_hp.get("current", "?")
            p_max = player_mon_hp.get("max", "?")
            lines.append(f"Your Pokemon: {p_current}/{p_max} HP")

        if enemy_mon_hp and isinstance(enemy_mon_hp, dict):
            e_current = enemy_mon_hp.get("current", "?")
            e_max = enemy_mon_hp.get("max", "?")
            lines.append(f"Enemy Pokemon: {e_current}/{e_max} HP")
        lines.append("")

    # Environment analysis from tile matrix
    tile_matrix = game_state.get("tile_matrix")
    if tile_matrix and isinstance(tile_matrix, dict):
        tiles = tile_matrix.get("tiles", [])
        if tiles:
            # Analyze nearby tiles for environmental features
            interaction_options = []

            # Count tile types in immediate vicinity
            tile_counts = {}
            total_tiles = 0

            for row in tiles:
                if isinstance(row, list):
                    for tile in row:
                        if isinstance(tile, dict):
                            total_tiles += 1
                            tile_type = tile.get("tile_type", "unknown")
                            # Convert enum to string if needed
                            if hasattr(tile_type, "name"):
                                tile_type = tile_type.name.lower()
                            elif hasattr(tile_type, "value"):
                                tile_type = str(tile_type.value).lower()
                            else:
                                tile_type = str(tile_type).lower()
                            tile_counts[tile_type] = tile_counts.get(tile_type, 0) + 1

                            # Check for interactive features
                            if tile.get("has_sign"):
                                interaction_options.append("Sign (read)")
                            if tile.get("pc_accessible"):
                                interaction_options.append("PC (access)")
                            if tile.get("is_warp_tile"):
                                interaction_options.append("Door/Warp")
                            if tile.get("cuttable_tree"):
                                interaction_options.append("Tree (cut)")
                            if tile.get("strength_boulder"):
                                interaction_options.append("Boulder (push)")
                            if tile.get("trainer_sight_line"):
                                interaction_options.append("Trainer nearby")

            # Determine dominant environment
            if tile_counts:
                dominant_terrain = []
                for tile_type, count in tile_counts.items():
                    if count / total_tiles > 0.1:  # More than 10% of visible area
                        if tile_type == "grass":
                            dominant_terrain.append("Tall grass (wild Pokemon)")
                        elif tile_type == "water":
                            dominant_terrain.append("Water (surf needed)")
                        elif tile_type == "ledge":
                            dominant_terrain.append("Ledges (one-way)")
                        elif tile_type != "walkable":
                            dominant_terrain.append(tile_type.title())

                if dominant_terrain or interaction_options:
                    lines.append("ENVIRONMENT:")
                    if dominant_terrain:
                        lines.append(f"Terrain: {', '.join(dominant_terrain)}")
                    if interaction_options:
                        unique_interactions = list(
                            dict.fromkeys(interaction_options)
                        )  # Remove duplicates
                        lines.append(
                            f"Actions: {', '.join(unique_interactions[:5])}"
                        )  # Limit to 5 most important
                    lines.append("")

    # Map loading status - only show if actively transitioning (1-3 are transition states)
    map_loading = game_state.get("map_loading_status")
    if map_loading is not None and 1 <= map_loading <= 3:
        lines.append(f"Status: Map transition in progress (status: {map_loading})")
        lines.append("")

    return "\n".join(lines).strip()


def get_game_state_text(state_file_path: str) -> str:
    """
    Extract game state data from a Pokemon Red .state file and format as text.

    This function loads a PyBoy .state file, parses it into comprehensive JSON format,
    and then formats it as a concise text representation suitable for LLM consumption.

    Args:
        state_file_path: Relative path to the .state file from project root
                        (e.g., "game/init.state", "captures/gamestate_20250620_110159.state")

    Returns:
        Formatted text representation of the game state

    Raises:
        FileNotFoundError: If the state file doesn't exist
        RuntimeError: If there's an error loading or parsing the state
    """
    try:
        # Get the JSON data first
        game_state_dict = get_game_state_json(state_file_path)

        # Format as text
        text_output = format_game_state_text(game_state_dict)

        return text_output

    except Exception as e:
        error_msg = f"Error creating text output from {state_file_path}: {str(e)}"
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
