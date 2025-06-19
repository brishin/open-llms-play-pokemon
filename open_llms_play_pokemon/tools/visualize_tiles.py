#!/usr/bin/env python3
"""
Command-line tool for visualizing interactive tiles.

This tool can be used to generate visualizations of interactive tiles
from saved game states or live game analysis.
"""

import argparse
import json
from pathlib import Path

from ..game_state.tile_data import TileMatrix
from ..visualization.interactive_tile_visualizer import InteractiveTileVisualizer


def load_tile_matrix_from_json(json_path: Path) -> TileMatrix:
    """Load a TileMatrix from a JSON file."""
    with open(json_path) as f:
        data = json.load(f)
    
    # Look for tile_matrix in the JSON structure
    if "tile_matrix" in data:
        return TileMatrix.from_dict(data["tile_matrix"])
    elif "tiles" in data:
        # Direct tile matrix data
        return TileMatrix.from_dict(data)
    else:
        raise ValueError("No tile matrix data found in JSON file")


def main():
    """Main entry point for the tile visualization tool."""
    parser = argparse.ArgumentParser(
        description="Visualize interactive tiles from Pokemon Red game states"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to JSON file containing tile matrix data"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to save visualization files (default: output)"
    )
    parser.add_argument(
        "--tile-size",
        type=int,
        default=16,
        help="Size of each tile in pixels for image output (default: 16)"
    )
    parser.add_argument(
        "--show-all-tiles",
        action="store_true",
        help="Show all tiles with base colors, not just interactive ones"
    )
    parser.add_argument(
        "--no-player",
        action="store_true",
        help="Don't highlight the player position"
    )
    parser.add_argument(
        "--format",
        choices=["png", "txt", "both"],
        default="both",
        help="Output format: png image, txt map, or both (default: both)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Print analysis of interactive elements"
    )
    
    args = parser.parse_args()
    
    # Load tile matrix
    try:
        tile_matrix = load_tile_matrix_from_json(args.input_file)
        print(f"Loaded tile matrix: {tile_matrix.width}x{tile_matrix.height}")
    except Exception as e:
        print(f"Error loading tile matrix: {e}")
        return 1
    
    # Create visualizer
    visualizer = InteractiveTileVisualizer(tile_size=args.tile_size)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate base filename
    base_name = args.input_file.stem
    
    # Generate visualizations
    if args.format in ["png", "both"]:
        image_path = args.output_dir / f"{base_name}_interactive_tiles.png"
        image = visualizer.visualize_interactive_tiles(
            tile_matrix,
            output_path=image_path,
            show_all_tiles=args.show_all_tiles,
            highlight_player=not args.no_player
        )
        print(f"Saved image visualization: {image_path}")
    
    if args.format in ["txt", "both"]:
        text_path = args.output_dir / f"{base_name}_interactive_tiles.txt"
        text_map = visualizer.create_text_map(
            tile_matrix,
            output_path=text_path,
            show_coordinates=True
        )
        print(f"Saved text visualization: {text_path}")
        
        # Also save legend
        legend_path = args.output_dir / "legend.txt"
        legend = visualizer.create_legend()
        legend_path.write_text(legend)
        print(f"Saved legend: {legend_path}")
    
    # Analyze interactive elements if requested
    if args.analyze:
        analysis = visualizer.analyze_interactive_elements(tile_matrix)
        print("\nInteractive Elements Analysis:")
        print(f"Total interactive elements: {analysis['total_interactive']}")
        
        for element_type, positions in analysis["elements"].items():
            if positions:
                print(f"\n{element_type.replace('_', ' ').title()}: {len(positions)}")
                for x, y in positions:
                    print(f"  ({x}, {y})")
    
    return 0


if __name__ == "__main__":
    exit(main())