# Tile Extraction System Implementation Plan

## Overview

This plan outlines the complete implementation of the enhanced tile extraction system based on TILE_EXTRACTION_GUIDE.md, integrating it with the existing game state system using the MemoryAddresses pattern. The system will provide comprehensive tile analysis with 30+ properties per tile including collision, interaction, animation, and special behaviors for the Pokemon Red AI agent.

## Domain-Specific Terminology

### Pokemon Red Memory Architecture
- **wTileMap ($C3A0)**: 20×18 screen tile buffer containing current visible tiles
- **wOverworldMap ($C6E8)**: Map block buffer (1300 bytes max) with compressed map data
- **wSurroundingTiles ($C800)**: 24×20 tile buffer for area around player
- **wCurTileset ($FFD7)**: Current tileset ID determining tile behavior context
- **wTilesetCollisionPtr ($1878)**: Pointer to collision data list terminated by $FF

### Enhanced TileData Structure (30+ Properties)
- **Basic Identification**: tile_id, coordinates, tile_type, tileset_id
- **Movement/Collision**: is_walkable, is_ledge_tile, ledge_direction, movement_modifier
- **Environmental**: is_encounter_tile, is_warp_tile, is_animated, light_level
- **Interactions**: has_sign, has_bookshelf, strength_boulder, cuttable_tree, pc_accessible
- **Battle System**: trainer_sight_line, trainer_id, hidden_item_id, requires_itemfinder
- **Special Zones**: safari_zone_steps, game_corner_tile, is_fly_destination
- **Audio/Visual**: has_footstep_sound, sprite_priority, background_priority, elevation_pair

### Pokemon Red Tile System Concepts
- **Block-to-Tile Expansion**: 4×4 tile groups from map blocks (.blk files)
- **Tileset-Specific Collision**: Each tileset has unique collision table with walkable tile IDs
- **Coordinate Systems**: Screen coordinates (0-19, 0-17), Map coordinates (absolute), Block coordinates
- **Sprite Interactions**: NPC sprites override tile properties and affect walkability
- **Counter Tiles**: Special tiles that extend NPC interaction range (counters, desks)
- **Elevation Pairs**: Paired tiles for height differences and visual depth

## Implementation Steps

### Step 1: Extend MemoryAddresses with Complete Tile System Data

**File**: `open_llms_play_pokemon/game_state/data/memory_addresses.py`

**Objective**: Add comprehensive tile-related memory addresses from TILE_EXTRACTION_GUIDE following the existing MemoryAddresses IntEnum pattern for type safety and consistency.

**Requirements**:
- Add all memory addresses as IntEnum members following existing pattern
- Maintain existing IntEnum structure and naming conventions
- Include comprehensive comments for each address
- Ensure type safety with proper IntEnum inheritance

**Memory Addresses to Add to MemoryAddresses IntEnum**:
```python
class MemoryAddresses(IntEnum):
    # ... existing addresses ...
    
    # Map state variables (from TILE_EXTRACTION_GUIDE.md)
    current_map_width = 0xD369      # wCurMapWidth - Current map width in blocks
    current_map_height = 0xD368     # wCurMapHeight - Current map height in blocks
    
    # Tile data buffers
    overworld_map_buffer = 0xC6E8   # wOverworldMap - Map block buffer (1300 bytes max)
    surrounding_tiles_buffer = 0xC800  # wSurroundingTiles - 24×20 tile buffer
    tile_map_buffer = 0xC3A0        # wTileMap - 20×18 screen tile buffer
    vram_bg_map = 0x9800            # vBGMap0 - VRAM background map
    
    # Tileset information
    current_tileset = 0xFFD7        # wCurTileset - Current tileset ID
    tileset_collision_ptr = 0x1878  # wTilesetCollisionPtr - Pointer to collision data
    grass_tile_id = 0x1882          # wGrassTile - Grass tile ID for current tileset
    
    # Map loading and transition state
    map_loading_status = 0xD36A     # wMapLoadingStatus - Check during transitions
    sprite_state_data = 0xC100      # wSpriteStateData1 - Base address for sprite data
```

**Type Safety Benefits**:
- Import and usage: `from open_llms_play_pokemon.game_state.data.memory_addresses import MemoryAddresses`
- Type-safe access: `memory_view[MemoryAddresses.tile_map_buffer]`
- IDE autocompletion and validation
- Runtime value checking with IntEnum

### Step 2: Implement Enhanced TileData Structure

**File**: `open_llms_play_pokemon/game_state/tile_data.py` (replace existing)

**Objective**: Replace existing TileData with complete enhanced structure from TILE_EXTRACTION_GUIDE containing 30+ properties.

**Key Components**:
- **Enhanced TileData**: Complete structure with all fields from guide
- **TileType Enum**: Comprehensive tile categories (unknown, walkable, blocked, grass, water, warp, ledge, building, road, tree, rock, npc, item)
- **Tileset Data Tables**: All tileset-specific data mappings from guide
- **Coordinate Conversion**: Screen ↔ Map ↔ Block coordinate transformations

**Domain-Specific Requirements**:
- Support for all 30+ TileData properties from TILE_EXTRACTION_GUIDE
- Tileset-specific collision, door, water, tree, ledge, and special tile mappings
- Proper handling of sprite interactions and elevation pairs
- Audio/visual properties and interaction detection

### Step 3: Core Tile Reading and Memory Access Functions

**File**: `open_llms_play_pokemon/game_state/tile_reader.py` (replace existing)

**Objective**: Implement core functions from TILE_EXTRACTION_GUIDE using PyBoy's memory API for reading tile data from Pokemon Red memory buffers.

**Core Functions Using PyBoy Memory API with Type-Safe MemoryAddresses**:
- **get_tile_id()**: Read tile ID from wTileMap using `memory_view[MemoryAddresses.tile_map_buffer + (y * 20) + x]`
- **get_map_coordinates()**: Convert screen coordinates using player position from `memory_view[MemoryAddresses.x_coord]`
- **is_collision_tile()**: Read collision table pointer and iterate until $FF termination using PyBoy slice reads
- **get_sprite_at_position()**: Detect sprites using PyBoy memory access to sprite data slots

**Type-Safe PyBoy Memory Access Patterns with MemoryAddresses IntEnum**:
```python
# Import for type safety
from open_llms_play_pokemon.game_state.data.memory_addresses import MemoryAddresses

# Single byte reads using IntEnum members
tile_id = memory_view[MemoryAddresses.tile_map_buffer + offset]
current_tileset = memory_view[MemoryAddresses.current_tileset]
player_x = memory_view[MemoryAddresses.x_coord]
player_y = memory_view[MemoryAddresses.y_coord]

# Multi-byte reads for collision tables using type-safe addresses
collision_ptr = memory_view[MemoryAddresses.tileset_collision_ptr]
collision_data = memory_view[collision_ptr:collision_ptr + 50]  # Read until FF found

# Sprite data access with IntEnum type safety (16 bytes per sprite)
sprite_base = MemoryAddresses.sprite_state_data + (sprite_id * 16)
sprite_x = memory_view[sprite_base + 6]  # SPRITESTATEDATA1_XPIXELS
sprite_y = memory_view[sprite_base + 4]  # SPRITESTATEDATA1_YPIXELS

# Map state reading with type-safe enum access
map_width = memory_view[MemoryAddresses.current_map_width]
map_height = memory_view[MemoryAddresses.current_map_height]
loading_status = memory_view[MemoryAddresses.map_loading_status]
```

**Performance Optimizations with Type-Safe Memory Access**:
- Use PyBoy's slice reading for bulk collision table data
- Cache collision table data using PyBoy memory reads  
- Validate coordinate bounds before PyBoy memory access
- Handle map transitions by checking `memory_view[MemoryAddresses.map_loading_status]`
- Leverage IntEnum for compile-time address validation

### Step 4: Complete TileData Creation System

**File**: `open_llms_play_pokemon/game_state/enhanced_tile_creator.py` (new)

**Objective**: Implement the complete create_tile_data() function from TILE_EXTRACTION_GUIDE using PyBoy memory API that generates TileData with all 30+ properties.

**Core Implementation with PyBoy API**:
- **create_tile_data()**: Main function using `memory_view: PyBoyMemoryView` parameter for all memory access
- **Property Detection Functions**: All helper functions from guide using PyBoy memory reads (ledge_info, audio_properties, trainer_sight_line, special_properties, animation_info)
- **Tileset Data Integration**: Access current tileset using `memory_view[MemoryAddresses.current_tileset]`
- **Sprite Override Logic**: Read sprite positions using PyBoy memory API with proper offset calculations

**Property Detection Using Type-Safe PyBoy Memory Access**:
```python
from open_llms_play_pokemon.game_state.data.memory_addresses import MemoryAddresses

def create_tile_data(memory_view: PyBoyMemoryView, x: int, y: int) -> TileData:
    # Basic tile reading with type-safe enum addresses
    tile_id = memory_view[MemoryAddresses.tile_map_buffer + (y * 20) + x]
    tileset_id = memory_view[MemoryAddresses.current_tileset]
    
    # Player position for coordinate conversion using IntEnum
    player_x = memory_view[MemoryAddresses.x_coord]
    player_y = memory_view[MemoryAddresses.y_coord]
    
    # Map dimensions using type-safe addresses
    map_width = memory_view[MemoryAddresses.current_map_width]
    map_height = memory_view[MemoryAddresses.current_map_height]
    
    # Collision detection with type-safe collision pointer
    is_walkable = not is_collision_tile(memory_view, tile_id)
    
    # Sprite detection using PyBoy memory API with IntEnum base address
    sprite_offset = get_sprite_at_position(memory_view, x, y)
    
    # Map loading state check for stability
    loading_status = memory_view[MemoryAddresses.map_loading_status]
```

**Property Detection Systems with Type-Safe Memory Access**:
- **Interaction Detection**: Use PyBoy memory with MemoryAddresses enum to read map data for signs, bookshelves, strength boulders, cuttable trees
- **Battle System Integration**: Access trainer data and hidden object tables via type-safe PyBoy memory reads
- **Environmental Properties**: Read animation states and tileset properties using MemoryAddresses IntEnum
- **Special Zones**: Check map ID and special flags using type-safe memory access patterns

### Step 5: Screen Analysis and Batch Processing

**File**: `open_llms_play_pokemon/game_state/screen_analyzer.py` (new)

**Objective**: Implement batch screen analysis functions from TILE_EXTRACTION_GUIDE using PyBoy memory API for processing entire 20×18 screen areas.

**Core Functions with Type-Safe PyBoy Memory Access**:
```python
from open_llms_play_pokemon.game_state.data.memory_addresses import MemoryAddresses

def analyze_screen(memory_view: PyBoyMemoryView) -> list[TileData]:
    """Process entire visible screen using type-safe PyBoy memory access."""
    # Check if map is stable before analysis
    loading_status = memory_view[MemoryAddresses.map_loading_status]
    if loading_status != 0:  # Map is transitioning
        return []
    
    tiles = []
    for y in range(18):  # Screen height
        for x in range(20):  # Screen width
            tile_data = create_tile_data(memory_view, x, y)
            tiles.append(tile_data)
    return tiles

def categorize_tiles(memory_view: PyBoyMemoryView) -> dict:
    """Group tiles by type using efficient type-safe PyBoy memory reads."""
    # Validate memory state before processing
    current_map = memory_view[MemoryAddresses.current_map]
    tileset_id = memory_view[MemoryAddresses.current_tileset]
    
    screen_tiles = analyze_screen(memory_view)
    return {
        'water': [t for t in screen_tiles if t.tile_type == TileType.WATER],
        'trees': [t for t in screen_tiles if t.tile_type == TileType.TREE],
        'walkable': [t for t in screen_tiles if t.is_walkable],
        'blocked': [t for t in screen_tiles if not t.is_walkable],
        # ... other categories
        'metadata': {
            'current_map': current_map,
            'tileset_id': tileset_id,
            'total_tiles': len(screen_tiles)
        }
    }
```

**Efficient Type-Safe Memory Access Patterns**:
- **Bulk Tile Reading**: Read entire wTileMap buffer using PyBoy slice access with `MemoryAddresses.tile_map_buffer`
- **Cached Property Detection**: Cache tileset and collision data during screen analysis using IntEnum addresses
- **Optimized Sprite Detection**: Read all sprite data once from `MemoryAddresses.sprite_state_data` and check positions during tile processing
- **Memory State Validation**: Use `MemoryAddresses.map_loading_status` to ensure stable memory state

**Analysis Categories**:
- **Tile Distribution**: Count tiles by type (water, trees, buildings, roads, ledges, grass, warps)
- **Interactive Objects**: Find cuttable trees, strength boulders, doors, signs, bookshelves
- **Battle Elements**: Locate trainer sight lines, hidden items, encounter zones
- **Navigation Analysis**: Walkable tiles, encounter zones, warp points, map borders
- **Environmental Features**: Water tiles, animated tiles, special footstep sounds

### Step 6: Integration with Existing Memory Reader

**File**: `open_llms_play_pokemon/game_state/memory_reader.py` (modify existing)

**Objective**: Integrate enhanced tile system with existing PokemonRedMemoryReader while maintaining PyBoy memory API consistency and backward compatibility.

**Integration Points with Type-Safe PyBoy API**:
```python
from open_llms_play_pokemon.game_state.data.memory_addresses import MemoryAddresses

class PokemonRedMemoryReader:
    def parse_game_state_with_tiles(self, memory_view: PyBoyMemoryView) -> tuple[PokemonRedGameState, TileMatrix]:
        """Enhanced version using type-safe PyBoy memory API."""
        # Validate memory state before processing
        loading_status = memory_view[MemoryAddresses.map_loading_status]
        if loading_status != 0:
            return self.parse_game_state(memory_view), None
        
        game_state = self.parse_game_state(memory_view)
        
        # Use enhanced tile system with same memory_view and type-safe addresses
        enhanced_tiles = analyze_screen(memory_view)
        tile_matrix = create_enhanced_tile_matrix(enhanced_tiles, game_state)
        
        return game_state, tile_matrix
    
    def get_comprehensive_game_data(self, memory_view: PyBoyMemoryView) -> dict:
        """Integrate enhanced screen analysis with type-safe memory access."""
        # ... existing code using MemoryAddresses enum ...
        
        # Add enhanced tile analysis using same memory_view and type-safe addresses
        enhanced_analysis = categorize_tiles(memory_view)
        data["enhanced_tile_analysis"] = enhanced_analysis
        
        # Include memory validation metadata
        data["memory_state"] = {
            "map_loading_status": memory_view[MemoryAddresses.map_loading_status],
            "current_map": memory_view[MemoryAddresses.current_map],
            "current_tileset": memory_view[MemoryAddresses.current_tileset]
        }
```

**PyBoy Memory API Consistency with Type Safety**:
- All functions receive the same `memory_view: PyBoyMemoryView` parameter
- No direct memory access outside of PyBoy API
- Consistent error handling for PyBoy memory exceptions
- Proper slice usage for bulk data reads
- Use MemoryAddresses IntEnum for all memory access to ensure type safety and prevent address typos

**Backward Compatibility with Type Safety**:
- Keep existing method signatures functional with PyBoy memory access using MemoryAddresses enum
- Gradually transition to enhanced system using same memory API and type-safe addresses
- Provide fallback to basic tile data if enhanced system fails, maintaining IntEnum usage
- Maintain existing TileMatrix structure with enhanced data populated via type-safe PyBoy memory access

### Step 7: Testing and Validation Framework

**File**: `tests/test_enhanced_tile_system.py` (new)

**Objective**: Comprehensive testing of enhanced tile extraction system accuracy and performance based on TILE_EXTRACTION_GUIDE examples.

**Test Categories**:
- **Memory Reading Tests**: Validate tile ID reading from wTileMap buffer
- **Coordinate Conversion Tests**: Test screen ↔ map coordinate transformations
- **Collision Detection Tests**: Verify collision table reading and walkability detection
- **Property Detection Tests**: Test all 30+ TileData property detection functions
- **Tileset Data Tests**: Validate tileset-specific data tables and mappings
- **Performance Benchmarks**: Measure tile extraction and analysis speed for 20×18 screen

**Validation Data**:
- Use known Pokemon Red save states for consistent testing
- Test against documented collision tables and tileset data from guide
- Validate sprite detection and interaction systems
- Test edge cases like map transitions and sprite movements

### Step 8: Integration with AI Agents

**Files**: 
- `open_llms_play_pokemon/agents/main.py` (modify)
- `open_llms_play_pokemon/agents/main_dspy.py` (modify)

**Objective**: Integrate enhanced tile system with existing AI agents for comprehensive game world understanding.

**Agent Enhancements**:
- **Enhanced Vision Analysis**: Provide detailed tile analysis to LLM prompts including interactables, hazards, and movement options
- **Movement Validation**: Use enhanced collision detection and trainer sight lines for action validation
- **Strategic Context**: Include tile-based analysis in decision making (avoid trainer sight lines, find shortcuts via ledges, locate items)
- **Interaction Planning**: Use tile properties to plan interactions with signs, doors, cuttable trees, strength boulders

**LLM Integration**:
- Add enhanced tile context to vision prompts with categorized analysis
- Include walkability maps and hazard detection in action planning
- Use encounter tile and trainer sight line data for exploration strategies
- Provide interactive element detection for objective-based gameplay

## Technical Implementation Constraints

### PyBoy Memory API Integration with Type Safety
- **PyBoyMemoryView Access**: Use `memory_view[MemoryAddresses.address_name]` for type-safe single byte reads and `memory_view[start:end]` for slices
- **Memory Address Validation**: PyBoy handles bounds checking, but validate addresses are within expected ranges using IntEnum constraints
- **Slice Reading Performance**: Use PyBoy's efficient slice reading for bulk data (collision tables, sprite data) with type-safe base addresses
- **Memory View Consistency**: Always use the same PyBoyMemoryView instance with MemoryAddresses enum for consistency
- **Compile-Time Safety**: IntEnum provides compile-time address validation and IDE autocompletion

### Pokemon Red Memory Architecture with Type-Safe Addresses
- **Tile Buffer Access**: Read from wTileMap using `MemoryAddresses.tile_map_buffer` with PyBoy memory indexing and proper offset calculations
- **Collision Table Reading**: Use PyBoy slice reads from `MemoryAddresses.tileset_collision_ptr` until $FF termination
- **Coordinate Bounds**: Validate screen coordinates (0-19, 0-17) before PyBoy memory access
- **Map Transition Handling**: Check using `MemoryAddresses.map_loading_status` with PyBoy memory reads
- **Sprite Detection**: Access sprite data using `MemoryAddresses.sprite_state_data` with PyBoy API and calculated offsets for 16-byte sprite structures

### Tileset-Specific Data Requirements
- **Collision Tables**: Each tileset has unique collision data tables from guide
- **Tile Mappings**: All tileset-specific tile ID mappings (DOOR_TILES, WATER_TILES, etc.)
- **Property Detection**: 30+ tile properties require extensive tileset context
- **Bank Management**: Some tileset data may be in different ROM banks requiring proper switching

## Implementation Notes

1. **Data Validation**: Extensive testing against TILE_EXTRACTION_GUIDE examples and Pokemon Red documentation using type-safe memory access
2. **Error Handling**: Robust error handling for map transitions, invalid coordinates, and memory access failures with IntEnum validation
3. **Type Safety**: All memory access uses MemoryAddresses IntEnum for compile-time validation and runtime safety
4. **IDE Support**: IntEnum provides full IDE autocompletion, refactoring support, and typo prevention for memory addresses

## Type Safety Benefits Summary

The MemoryAddresses IntEnum pattern provides:
- **Compile-time validation** of memory addresses
- **IDE autocompletion** and refactoring support  
- **Prevention of address typos** that could cause crashes
- **Consistent naming** across the entire codebase
- **Easy maintenance** when addresses need to be updated
- **Self-documenting code** with descriptive address names
- **Runtime value validation** with IntEnum constraints

This implementation plan provides a comprehensive roadmap for integrating the complete enhanced tile extraction system based on TILE_EXTRACTION_GUIDE.md while maintaining compatibility with existing code and following the established MemoryAddresses IntEnum pattern for maximum type safety and maintainability.