# Unified Tile Data System for Pokemon Red

This document describes the comprehensive tile data system that transforms raw PyBoy `game_area()` numbers into structured, serializable data suitable for AI analysis and decision-making.

## Overview

The unified tile data system addresses the challenge of understanding what the numbers from PyBoy's `game_area()` method actually represent. Instead of working with raw tile IDs, this system provides:

- **Structured tile data** with type classification and properties
- **Collision detection** integrated with Pokemon Red's actual collision tables
- **Serializable formats** for data persistence and analysis
- **Rich analysis tools** for understanding the game world

## Core Components

### 1. TileData Class

A frozen dataclass representing a single tile with all its properties:

```python
@dataclass(frozen=True)
class TileData:
    tile_id: int                 # PyBoy tile identifier (0-383)
    x: int                       # X coordinate in game area matrix
    y: int                       # Y coordinate in game area matrix  
    map_x: int                   # Absolute X coordinate on current map
    map_y: int                   # Absolute Y coordinate on current map
    tile_type: TileType          # Categorized tile type (grass, tree, etc.)
    is_walkable: bool            # Whether player can walk through
    is_encounter_tile: bool      # Whether wild Pokemon can appear
    is_warp_tile: bool           # Whether this is a door/warp entrance
    sprite_offset: int           # Sprite offset if applicable
    raw_value: int               # Original tile value from game_area()
```

### 2. TileType Enumeration

Semantic classification of tiles:

```python
class TileType(Enum):
    UNKNOWN = "unknown"
    WALKABLE = "walkable"
    BLOCKED = "blocked"
    GRASS = "grass"           # Wild Pokemon encounters
    WATER = "water"           # Requires surfing
    WARP = "warp"            # Doors, cave entrances
    LEDGE = "ledge"          # Can jump down
    BUILDING = "building"     # Solid structures
    ROAD = "road"            # Walkable paths
    TREE = "tree"            # Natural obstacles
    ROCK = "rock"            # Stone obstacles
    NPC = "npc"              # Non-player characters
    ITEM = "item"            # Collectible items
```

### 3. TileMatrix Class

Container for a complete game area with analysis methods:

```python
@dataclass
class TileMatrix:
    tiles: List[List[TileData]]  # 2D matrix of tile data
    width: int                   # Matrix width
    height: int                  # Matrix height
    current_map: int             # Map ID where captured
    player_x: int                # Player X position
    player_y: int                # Player Y position
    timestamp: Optional[int]     # When captured
```

## Key Features

### Serialization Support

All data structures support JSON serialization:

```python
# Convert to JSON
json_data = tile_matrix.to_json()

# Load from JSON
reconstructed = TileMatrix.from_json(json_data)

# Dictionary format for custom serialization
data_dict = tile_matrix.to_dict()
```

### Collision Detection

Integrated with Pokemon Red's actual collision system:

```python
# Check if a tile is walkable
is_walkable = is_tile_walkable(tile_id, tileset_id)

# Get all walkable positions
walkable_positions = tile_matrix.get_walkable_tiles()
```

### Analysis Tools

Rich analysis capabilities:

```python
# Find specific tile types
grass_tiles = tile_matrix.get_tiles_by_type(TileType.GRASS)

# Get numpy arrays for ML algorithms
walkability_matrix = tile_matrix.get_walkability_matrix()
encounter_matrix = tile_matrix.get_encounter_matrix()

# Analyze area around player
analysis = tile_reader.analyze_area_around_player(game_state, radius=3)
```

## Usage Examples

### Basic Usage

```python
from pyboy import PyBoy
from open_llms_play_pokemon.game_state import PokemonRedMemoryReader

# Initialize
pyboy = PyBoy("Pokemon Red.gb", window="null")
memory_reader = PokemonRedMemoryReader(pyboy)

# Get comprehensive data
game_state, tile_matrix = memory_reader.parse_game_state_with_tiles(pyboy.memory)

# Analyze the current area
if tile_matrix:
    print(f"Matrix size: {tile_matrix.width}x{tile_matrix.height}")
    
    # Find encounter areas
    grass_tiles = tile_matrix.get_tiles_by_type(TileType.GRASS)
    print(f"Found {len(grass_tiles)} grass tiles for encounters")
    
    # Check movement options
    center_x, center_y = tile_matrix.width // 2, tile_matrix.height // 2
    player_tile = tile_matrix.get_tile(center_x, center_y)
    print(f"Player is on: {player_tile.tile_type.value}")
```

### Comprehensive Analysis

```python
# Get full analysis
comprehensive_data = memory_reader.get_comprehensive_game_data(pyboy.memory)

# Access different data components
game_state = comprehensive_data['game_state']
tile_data = comprehensive_data['tile_data']
analysis = comprehensive_data['analysis']

# Movement analysis
if analysis:
    directions = analysis['directions_available']
    can_go_north = directions['north']
    nearby_encounters = len(analysis['encounter_tiles'])
```

### Serialization and Persistence

```python
# Save tile data
with open('game_state.json', 'w') as f:
    json.dump(comprehensive_data, f, indent=2)

# Load tile data
with open('game_state.json', 'r') as f:
    loaded_data = json.load(f)

tile_matrix = TileMatrix.from_dict(loaded_data['tile_data'])
```

### Integration with ML/AI

```python
# Get numpy arrays for ML algorithms
tile_ids = tile_matrix.get_tile_id_matrix()          # Shape: (height, width)
walkability = tile_matrix.get_walkability_matrix()   # Shape: (height, width)
encounters = tile_matrix.get_encounter_matrix()      # Shape: (height, width)

# Use in pathfinding, decision making, etc.
import numpy as np

# Find shortest path to grass (for training)
grass_positions = np.where(encounters)
if len(grass_positions[0]) > 0:
    closest_grass = (grass_positions[0][0], grass_positions[1][0])
    print(f"Closest grass at: {closest_grass}")
```

## Architecture

### Data Flow

1. **PyBoy** provides raw `game_area()` matrix
2. **TileReader** combines with game state from memory
3. **Collision tables** determine walkability
4. **Classification system** assigns semantic types
5. **TileMatrix** structures everything for analysis
6. **JSON serialization** enables persistence

### Collision System Integration

The system uses Pokemon Red's actual collision tables:

```python
COLLISION_TABLES = {
    0: {32, 33, 34, 35, 36, 37, 38, 39},  # Overworld walkable tiles
    1: {20, 21, 22, 23, 24},               # Red's House walkable tiles
    2: {15, 16, 17, 18, 19},               # Pokemon Center walkable tiles
    3: {40, 41, 42, 43, 44},               # Viridian Forest walkable tiles
    # ... more tilesets
}
```

### Type Classification

Tiles are classified using multiple criteria:

1. **Special tile sets** (grass, water, warp tiles)
2. **Walkability status** (from collision tables)
3. **Tile ID ranges** (trees, rocks, buildings)
4. **Context information** (current tileset, map)

## Benefits for AI Agents

### Structured Decision Making

Instead of working with raw numbers, agents get semantic information:

```python
# Before: What does tile ID 147 mean?
raw_tile_id = 147

# After: Rich semantic information
tile = TileData(
    tile_id=147,
    tile_type=TileType.TREE,
    is_walkable=False,
    is_encounter_tile=False,
    # ... full context
)
```

### Efficient Analysis

Pre-computed matrices for common operations:

```python
# Quickly find all valid moves
walkable_matrix = tile_matrix.get_walkability_matrix()
valid_moves = walkable_matrix[player_y-1:player_y+2, player_x-1:player_x+2]

# Find encounter opportunities
encounter_matrix = tile_matrix.get_encounter_matrix()
training_spots = np.where(encounter_matrix & walkable_matrix)
```

### Serializable Game State

Complete game world representation that can be:
- Saved and loaded
- Transmitted over networks
- Analyzed offline
- Used for replay and training

## Performance Considerations

- **Frozen dataclasses** ensure immutability and hashability
- **Numpy array exports** provide efficient matrix operations
- **Lazy evaluation** where possible to avoid unnecessary computation
- **Caching** of collision table lookups

## Extension Points

### Adding New Tile Types

```python
# Add to TileType enum
class TileType(Enum):
    # ... existing types
    CHECKPOINT = "checkpoint"    # Custom type

# Update classification function
def classify_tile_type(tile_id, is_walkable, tileset_id):
    if tile_id in CHECKPOINT_TILES:
        return TileType.CHECKPOINT
    # ... rest of logic
```

### Custom Collision Tables

```python
# Add collision data for new maps/tilesets
COLLISION_TABLES[new_tileset_id] = {
    # Set of walkable tile IDs for this tileset
}
```

### Enhanced Analysis

```python
# Add custom analysis methods to TileMatrix
def find_optimal_path(self, start, goal):
    # Custom pathfinding using walkability matrix
    pass

def evaluate_area_safety(self, center, radius):
    # Custom safety analysis
    pass
```

## Files in the System

- `tile_data.py` - Core data structures and utilities
- `tile_reader.py` - PyBoy integration and tile extraction
- `memory_reader.py` - Enhanced memory reader with tile support
- `examples/unified_tile_data_example.py` - Complete usage example
- `tests/test_unified_tile_data.py` - Comprehensive tests

## Dependencies

- **PyBoy** - Game emulation and `game_area()` access
- **NumPy** - Efficient matrix operations
- **JSON** (built-in) - Serialization support
- **Enum, dataclasses** (built-in) - Type safety and structure

This unified tile data system transforms the raw numerical output of PyBoy into a rich, structured representation that enables sophisticated AI decision-making and analysis of the Pokemon Red game world.