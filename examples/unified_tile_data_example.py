"""
Example: Using the Unified Tile Data System

This example shows how to use the comprehensive tile data structures
to analyze Pokemon Red's game world, including collision detection,
tile classification, and serialization.
"""

import json
import os
import sys
from typing import Dict, List

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyboy import PyBoy
from open_llms_play_pokemon.game_state import (
    PokemonRedMemoryReader,
    TileData,
    TileMatrix,
    TileType,
    TileReader,
)


def analyze_game_area(pyboy: PyBoy) -> Dict:
    """
    Comprehensive analysis of the current game area.
    
    Returns:
        Dictionary with detailed analysis
    """
    # Initialize the memory reader with PyBoy for tile reading
    memory_reader = PokemonRedMemoryReader(pyboy)
    
    # Get comprehensive game data
    comprehensive_data = memory_reader.get_comprehensive_game_data(pyboy.memory)
    
    print("=== GAME STATE ===")
    game_state = comprehensive_data['game_state']
    print(f"Current Map: {game_state['current_map']}")
    print(f"Player Position: ({game_state['player_x']}, {game_state['player_y']})")
    print(f"Party Count: {game_state['party_count']}")
    print(f"Badges: {game_state['badges_obtained']}")
    print(f"In Battle: {bool(game_state['is_in_battle'])}")
    
    if comprehensive_data['tile_data'] is not None:
        print("\n=== TILE MATRIX ===")
        tile_matrix = TileMatrix.from_dict(comprehensive_data['tile_data'])
        
        print(f"Matrix Size: {tile_matrix.width}x{tile_matrix.height}")
        print(f"Total Tiles: {tile_matrix.width * tile_matrix.height}")
        
        # Analyze tile types
        tile_type_counts = {}
        walkable_count = 0
        encounter_count = 0
        
        for row in tile_matrix.tiles:
            for tile in row:
                tile_type = tile.tile_type.value
                tile_type_counts[tile_type] = tile_type_counts.get(tile_type, 0) + 1
                
                if tile.is_walkable:
                    walkable_count += 1
                if tile.is_encounter_tile:
                    encounter_count += 1
        
        print(f"Walkable Tiles: {walkable_count}")
        print(f"Encounter Tiles: {encounter_count}")
        print("Tile Type Distribution:")
        for tile_type, count in sorted(tile_type_counts.items()):
            print(f"  {tile_type}: {count}")
        
        # Get specific tile information
        center_x, center_y = tile_matrix.width // 2, tile_matrix.height // 2
        center_tile = tile_matrix.get_tile(center_x, center_y)
        if center_tile:
            print(f"\nCenter Tile (Player Position):")
            print(f"  Tile ID: {center_tile.tile_id}")
            print(f"  Type: {center_tile.tile_type.value}")
            print(f"  Walkable: {center_tile.is_walkable}")
            print(f"  Encounter: {center_tile.is_encounter_tile}")
        
        # Movement analysis
        if comprehensive_data['analysis'] is not None:
            print("\n=== MOVEMENT ANALYSIS ===")
            analysis = comprehensive_data['analysis']
            directions = analysis['directions_available']
            print("Available Directions:")
            for direction, available in directions.items():
                status = "✓" if available else "✗"
                print(f"  {direction.capitalize()}: {status}")
            
            print(f"Nearby Walkable Tiles: {len(analysis['walkable_nearby'])}")
            print(f"Nearby Blocked Tiles: {len(analysis['blocked_nearby'])}")
            print(f"Nearby Encounter Tiles: {len(analysis['encounter_tiles'])}")
            print(f"Nearby Warp Tiles: {len(analysis['warp_tiles'])}")
    
    return comprehensive_data


def save_tile_data_to_file(tile_matrix: TileMatrix, filename: str) -> None:
    """Save tile matrix data to a JSON file."""
    with open(filename, 'w') as f:
        f.write(tile_matrix.to_json())
    print(f"Tile data saved to {filename}")


def load_tile_data_from_file(filename: str) -> TileMatrix:
    """Load tile matrix data from a JSON file."""
    with open(filename, 'r') as f:
        return TileMatrix.from_json(f.read())


def find_path_to_tiles(tile_matrix: TileMatrix, target_type: TileType) -> List[TileData]:
    """
    Find all tiles of a specific type in the matrix.
    
    Args:
        tile_matrix: The tile matrix to search
        target_type: Type of tiles to find
        
    Returns:
        List of tiles matching the target type
    """
    return tile_matrix.get_tiles_by_type(target_type)


def create_walkability_map(tile_matrix: TileMatrix) -> str:
    """
    Create a visual representation of walkable areas.
    
    Args:
        tile_matrix: The tile matrix
        
    Returns:
        String representation of walkability
    """
    walkability_matrix = tile_matrix.get_walkability_matrix()
    
    result = []
    for row in walkability_matrix:
        row_str = ""
        for walkable in row:
            row_str += "." if walkable else "#"
        result.append(row_str)
    
    return "\n".join(result)


def demonstrate_serialization(tile_matrix: TileMatrix) -> None:
    """Demonstrate serialization and deserialization."""
    print("\n=== SERIALIZATION DEMO ===")
    
    # Convert to dictionary
    tile_dict = tile_matrix.to_dict()
    print(f"Dictionary keys: {list(tile_dict.keys())}")
    
    # Convert to JSON
    json_str = tile_matrix.to_json()
    print(f"JSON size: {len(json_str)} characters")
    
    # Demonstrate round-trip
    reconstructed = TileMatrix.from_json(json_str)
    print(f"Round-trip successful: {reconstructed.width == tile_matrix.width}")
    
    # Show compact numpy arrays
    tile_ids = tile_matrix.get_tile_id_matrix()
    walkability = tile_matrix.get_walkability_matrix()
    encounters = tile_matrix.get_encounter_matrix()
    
    print(f"Tile ID matrix shape: {tile_ids.shape}")
    print(f"Walkability matrix shape: {walkability.shape}")
    print(f"Encounter matrix shape: {encounters.shape}")


def main():
    """Main example function."""
    # Initialize PyBoy
    game_path = "game/Pokemon Red.gb"
    if not os.path.exists(game_path):
        print(f"Game ROM not found at {game_path}")
        return
    
    pyboy = PyBoy(
        game_path,
        window="null",  # Headless mode
        debug=False,
        symbols="game/pokered.sym"
    )
    
    try:
        # Load initial state
        state_path = "game/init.state"
        if os.path.exists(state_path):
            with open(state_path, "rb") as f:
                pyboy.load_state(f)
            print("Loaded initial game state")
        
        # Run analysis
        comprehensive_data = analyze_game_area(pyboy)
        
        # Demonstrate features if tile data is available
        if comprehensive_data['tile_data'] is not None:
            tile_matrix = TileMatrix.from_dict(comprehensive_data['tile_data'])
            
            # Create walkability map
            print("\n=== WALKABILITY MAP ===")
            print("Legend: . = walkable, # = blocked")
            walkability_map = create_walkability_map(tile_matrix)
            print(walkability_map)
            
            # Find specific tile types
            grass_tiles = find_path_to_tiles(tile_matrix, TileType.GRASS)
            if grass_tiles:
                print(f"\nFound {len(grass_tiles)} grass tiles for encounters")
            
            # Demonstrate serialization
            demonstrate_serialization(tile_matrix)
            
            # Save data to file
            save_tile_data_to_file(tile_matrix, "example_tile_data.json")
            
            # Load it back
            loaded_matrix = load_tile_data_from_file("example_tile_data.json")
            print(f"Successfully loaded tile matrix: {loaded_matrix.width}x{loaded_matrix.height}")
        
    finally:
        pyboy.stop()


if __name__ == "__main__":
    main()