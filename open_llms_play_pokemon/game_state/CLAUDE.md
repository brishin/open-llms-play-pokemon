# Game State Package - CLAUDE.md

## Overview

The `game_state` package provides comprehensive Pokemon Red game state reading and tile analysis capabilities. It extracts and structures game data from PyBoy emulator memory into type-safe, feature-rich objects for AI agents and game analysis.

## Core Architecture

### 🎮 **Game State Management**
- **PokemonRedGameState**: Unified data structure containing comprehensive game state with runtime metadata, tile data, and movement analysis - optimized for logging and AI agents
- **PokemonRedMemoryReader**: Main interface for reading game state from PyBoy memory with type-safe access

### 🗺️ **Tile System (Enhanced)**
- **TileData**: Comprehensive tile structure with 30+ properties (collision, interaction, animation, special behaviors)
- **TileMatrix**: 2D grid of tiles representing the visible screen (20x18)
- **TileType**: Enum categorizing tiles by game function (grass, water, warp, ledge, etc.)

### 🏭 **Factory & Detection Classes**
- **TileDataFactory**: Factory for creating common tile configurations (placeholder, walkable, blocked, water, ledge)
- **TilePropertyDetector**: Consolidated detector for all tile properties with static methods

### 📊 **Screen Analysis**
- **screen_analyzer.py**: Batch processing functions for analyzing entire screen areas
- **enhanced_tile_creator.py**: Core tile creation with full property detection

## Key Classes & Usage

### PokemonRedMemoryReader
```python
reader = PokemonRedMemoryReader(pyboy)

# Parse complete game state with all tile data and metadata
game_state = reader.parse_game_state(memory_view, step_counter=10, timestamp="2024-01-01T00:00:00")

# Game state structure includes:
# - Runtime metadata (step_counter, timestamp) 
# - Core game data (player info, party, badges, battle state)
# - Memory state (map_loading_status, current_tileset)
# - All tiles data (walkable, blocked, encounter, warp, interactive)
# - Tile type counts and movement analysis
```

### TileDataFactory
```python
# Create different tile types
placeholder = TileDataFactory.create_placeholder(x, y)
walkable_tile = TileDataFactory.create_walkable(tile_id, x, y, map_x, map_y)
blocked_tile = TileDataFactory.create_blocked(tile_id, x, y, map_x, map_y)
water_tile = TileDataFactory.create_water(tile_id, x, y, map_x, map_y, current_direction="north")
ledge_tile = TileDataFactory.create_ledge(tile_id, x, y, map_x, map_y, direction="down")
```

### TilePropertyDetector
```python
# Individual property detection
ledge_dir, is_ledge = TilePropertyDetector.detect_ledge_info(tileset_id, tile_id)
interactions = TilePropertyDetector.detect_interaction_properties(tileset_id, tile_id)
env_props = TilePropertyDetector.detect_environmental_properties(tileset_id, tile_id)

# All properties at once
all_props = TilePropertyDetector.detect_all_properties(
    memory_view, tileset_id, tile_id, map_x, map_y
)
```

### Screen Analysis Functions
```python
# Analyze entire screen
tiles = analyze_screen(memory_view)

# Get specific tile types
walkable_tiles = get_walkable_tiles(memory_view)
encounter_tiles = get_encounter_tiles(memory_view)
warp_tiles = get_warp_tiles(memory_view)

# Categorize all tiles
categories = categorize_tiles(memory_view)

# Movement analysis
movement_options = get_movement_options(memory_view)

# Comprehensive AI data
ai_data = get_comprehensive_game_data(memory_view)
```

## Tile Properties Reference

### Core Properties
- `tile_id`: Raw tile ID from memory
- `x, y`: Screen coordinates (0-19, 0-17)
- `map_x, map_y`: Absolute map coordinates
- `tile_type`: TileType enum classification
- `tileset_id`: Current tileset

### Movement & Collision
- `is_walkable`: Can player move through
- `is_ledge_tile`: Can jump down
- `ledge_direction`: Direction of ledge jump
- `movement_modifier`: Speed multiplier (1.0 = normal, 0.5 = surf)

### Environmental
- `is_encounter_tile`: Wild Pokemon encounters possible
- `is_warp_tile`: Triggers map transition
- `is_animated`: Has animation frames
- `light_level`: Brightness (0-15)
- `water_current_direction`: Water flow direction

### Interactions
- `has_sign`: Readable sign
- `has_bookshelf`: Bookshelf to read
- `strength_boulder`: Moveable boulder
- `cuttable_tree`: Tree that can be cut
- `pc_accessible`: Pokemon Center PC

### Special Features
- `trainer_sight_line`: In trainer's view
- `hidden_item_id`: Hidden item present
- `safari_zone_steps`: Safari Zone mechanics
- `sprite_offset`: NPC/sprite present
- `blocks_light`: Casts shadow

## Memory Addresses

The package uses type-safe memory access through `MemoryAddresses` IntEnum:

### Player State
- `x_coord, y_coord`: Player position
- `current_map`: Map ID
- `current_tileset`: Tileset ID
- `party_count`: Number of Pokemon

### Battle System
- `is_in_battle`: Battle state flag
- `battle_mon_hp`: Player Pokemon HP
- `enemy_mon_hp`: Enemy Pokemon HP

### Tile System
- `tile_map_buffer`: Screen tile data (20x18)
- `tileset_collision_ptr`: Collision table pointer
- `map_loading_status`: Map transition state

## Best Practices

### For AI Agents
1. Use `get_comprehensive_game_data()` for complete environmental analysis
2. Check `map_loading_status` before tile analysis
3. Use categorized tile functions for specific needs
4. Leverage movement analysis for pathfinding

### For Development
1. Use TileDataFactory for consistent tile creation
2. Extend TilePropertyDetector for new detection logic
3. Test with both real game states and mocks
4. Follow the existing type-safe memory access patterns

### Performance Considerations
1. Screen analysis processes 360 tiles - cache results when possible
2. Memory validation is included but adds overhead
3. Batch processing is optimized for full screen analysis
4. Use specific tile queries (`get_walkable_tiles`) when you don't need everything

## Error Handling

The package gracefully handles:
- **Map transitions**: Returns empty results during loading
- **Memory read failures**: Fallback to safe defaults
- **Invalid coordinates**: Raises ValueError with clear messages
- **Missing tiles**: Creates placeholders automatically

## Testing

### Test Files
- `test_enhanced_tile_creator.py`: Core tile creation and property detection
- `test_game_state.py`: Memory reader integration and comprehensive analysis

### Mock Patterns
```python
# Mock memory view for testing
mock_memory_view = Mock()
mock_memory_view.__getitem__ = Mock(side_effect=lambda addr: test_data.get(addr, 0))

# Test tile creation
tile = create_tile_data(mock_memory_view, x, y)

# Test with real game state
pyboy = PyBoy("game/Pokemon Red.gb", window="null")
with open("game/init.state", "rb") as f:
    pyboy.load_state(f)
```

## Integration Points

### With PyBoy
- Direct memory access through PyBoyMemoryView
- Symbol file support for accurate addresses
- Game wrapper integration for additional data

### With AI Agents
- Structured data ready for decision-making
- Comprehensive environmental context
- Movement and interaction possibilities pre-analyzed

### With Game Logic
- Battle state integration
- Event flag tracking
- Map transition handling

## Recent Improvements

✅ **Unified Game State**: Migrated ConsolidatedGameState functionality into PokemonRedGameState for single source of truth
✅ **Enhanced Data Structures**: PokemonHp, TilePosition, TileWithDistance, DirectionsAvailable dataclasses for type safety
✅ **Optimized Logging**: Game state optimized for MLFlow logging without event_flags
✅ **Factory Pattern**: TileDataFactory eliminates code duplication
✅ **Consolidated Detection**: TilePropertyDetector organizes all detection logic  
✅ **Enhanced Testing**: Comprehensive test coverage with mocking
✅ **Type Safety**: Full type annotations and enum usage
✅ **Performance**: Optimized batch processing and caching
✅ **Documentation**: Clear interfaces and usage examples