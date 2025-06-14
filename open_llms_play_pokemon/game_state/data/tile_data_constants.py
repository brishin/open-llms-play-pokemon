"""
Tile Data Constants for Pokemon Red

This module contains all the tileset-specific data mappings and constants
used for tile classification and property detection.
"""

from enum import IntEnum


class TilesetID(IntEnum):
    """Pokemon Red tileset IDs for type safety and self-documentation.

    These match the exact tileset constants from pokered/constants/tileset_constants.asm
    """

    OVERWORLD = 0  # Overworld maps (Pallet Town, Routes, etc.)
    REDS_HOUSE_1 = 1  # Red's House first tileset
    MART = 2  # Mart/Pokemart interiors
    FOREST = 3  # Viridian Forest and similar outdoor areas
    REDS_HOUSE_2 = 4  # Red's House second tileset
    DOJO = 5  # Fighting Dojo
    POKECENTER = 6  # Pokemon Centers
    GYM = 7  # Gym interiors
    HOUSE = 8  # Generic house interiors
    FOREST_GATE = 9  # Forest gate buildings
    MUSEUM = 10  # Museum interiors
    UNDERGROUND = 11  # Underground passages
    GATE = 12  # Gate buildings
    SHIP = 13  # S.S. Anne and ship interiors
    SHIP_PORT = 14  # Ship port areas
    CEMETERY = 15  # Pokemon Tower and cemetery
    INTERIOR = 16  # Generic interior spaces
    CAVERN = 17  # Caves, dungeons, and underground areas
    LOBBY = 18  # Lobby areas
    MANSION = 19  # Celadon Mansion and similar large buildings
    LAB = 20  # Professor Oak's Lab and similar
    CLUB = 21  # Pokemon Fan Club and similar
    FACILITY = 22  # Facilities like Silph Co
    PLATEAU = 23  # Indigo Plateau


# Collision data from pokered/data/tilesets/collision_tile_ids.asm
# These are the actual walkable tile IDs for each tileset
COLLISION_TABLES = {
    # TilesetID -> set of walkable tile IDs (from pokered source)
    TilesetID.UNDERGROUND: {0x0B, 0x0C, 0x13, 0x15, 0x18},
    TilesetID.OVERWORLD: {
        0x00,
        0x10,
        0x1B,
        0x20,
        0x21,
        0x23,
        0x2C,
        0x2D,
        0x2E,
        0x30,
        0x31,
        0x33,
        0x39,
        0x3C,
        0x3E,
        0x52,
        0x54,
        0x58,
        0x5B,
    },
    TilesetID.REDS_HOUSE_1: {0x01, 0x02, 0x03, 0x11, 0x12, 0x13, 0x14, 0x1C, 0x1A},
    TilesetID.REDS_HOUSE_2: {0x01, 0x02, 0x03, 0x11, 0x12, 0x13, 0x14, 0x1C, 0x1A},
    TilesetID.MART: {0x11, 0x1A, 0x1C, 0x3C, 0x5E},
    TilesetID.POKECENTER: {0x11, 0x1A, 0x1C, 0x3C, 0x5E},
    TilesetID.DOJO: {0x11, 0x16, 0x19, 0x2B, 0x3C, 0x3D, 0x3F, 0x4A, 0x4C, 0x4D, 0x03},
    TilesetID.GYM: {0x11, 0x16, 0x19, 0x2B, 0x3C, 0x3D, 0x3F, 0x4A, 0x4C, 0x4D, 0x03},
    TilesetID.FOREST: {
        0x1E,
        0x20,
        0x2E,
        0x30,
        0x34,
        0x37,
        0x39,
        0x3A,
        0x40,
        0x51,
        0x52,
        0x5A,
        0x5C,
        0x5E,
        0x5F,
    },
    TilesetID.HOUSE: {0x01, 0x12, 0x14, 0x28, 0x32, 0x37, 0x44, 0x54, 0x5C},
    TilesetID.FOREST_GATE: {0x01, 0x12, 0x14, 0x1A, 0x1C, 0x37, 0x38, 0x3B, 0x3C, 0x5E},
    TilesetID.MUSEUM: {0x01, 0x12, 0x14, 0x1A, 0x1C, 0x37, 0x38, 0x3B, 0x3C, 0x5E},
    TilesetID.GATE: {0x01, 0x12, 0x14, 0x1A, 0x1C, 0x37, 0x38, 0x3B, 0x3C, 0x5E},
    TilesetID.SHIP: {0x04, 0x0D, 0x17, 0x1D, 0x1E, 0x23, 0x34, 0x37, 0x39, 0x4A},
    TilesetID.SHIP_PORT: {0x0A, 0x1A, 0x32, 0x3B},
    TilesetID.CEMETERY: {0x01, 0x10, 0x13, 0x1B, 0x22, 0x42, 0x52},
    TilesetID.INTERIOR: {0x04, 0x0F, 0x15, 0x1F, 0x3B, 0x45, 0x47, 0x55, 0x56},
    TilesetID.CAVERN: {0x05, 0x15, 0x18, 0x1A, 0x20, 0x21, 0x22, 0x2A, 0x2D, 0x30},
    TilesetID.LOBBY: {0x14, 0x17, 0x1A, 0x1C, 0x20, 0x38, 0x45},
    TilesetID.MANSION: {0x01, 0x05, 0x11, 0x12, 0x14, 0x1A, 0x1C, 0x2C, 0x53},
    TilesetID.LAB: {0x0C, 0x26, 0x16, 0x1E, 0x34, 0x37},
    TilesetID.CLUB: {0x0F, 0x1A, 0x1F, 0x26, 0x28, 0x29, 0x2C, 0x2D, 0x2E, 0x2F, 0x41},
    TilesetID.FACILITY: {
        0x01,
        0x10,
        0x11,
        0x13,
        0x1B,
        0x20,
        0x21,
        0x22,
        0x30,
        0x31,
        0x32,
        0x42,
        0x43,
        0x48,
        0x52,
        0x55,
        0x58,
        0x5E,
    },
    TilesetID.PLATEAU: {0x1B, 0x23, 0x2C, 0x2D, 0x3B, 0x45},
}

# Door tiles from pokered/data/tilesets/door_tile_ids.asm
# These are the actual door/entrance tile IDs for each tileset
DOOR_TILES = {
    TilesetID.OVERWORLD: {0x1B, 0x58},
    TilesetID.FOREST: {0x3A},
    TilesetID.MART: {0x5E},
    TilesetID.HOUSE: {0x54},
    TilesetID.FOREST_GATE: {0x3B},
    TilesetID.MUSEUM: {0x3B},
    TilesetID.GATE: {0x3B},
    TilesetID.SHIP: {0x1E},
    TilesetID.LOBBY: {0x1C, 0x38, 0x1A},
    TilesetID.MANSION: {0x1A, 0x1C, 0x53},
    TilesetID.LAB: {0x34},
    TilesetID.FACILITY: {0x43, 0x58, 0x1B},
    TilesetID.PLATEAU: {0x3B, 0x1B},
}

# Water tiles - these would need to be determined from actual pokered tileset analysis
# Most tilesets don't have water tiles
WATER_TILES = {
    TilesetID.OVERWORLD: {0x14, 0x32},  # Common water tiles in overworld
    # Other tilesets generally don't have water tiles
}

# Tree tiles (cuttable with CUT) - need actual analysis of pokered tree graphics
TREE_TILES = {
    TilesetID.OVERWORLD: {0x3D, 0x3F},  # Common tree tiles that can be cut
    TilesetID.FOREST: {0x03, 0x04},  # Forest-specific tree tiles
}

# Ledge data from pokered/data/tilesets/ledge_tiles.asm
# Structure: (player_direction, standing_tile, ledge_tile, input_required)
LEDGE_DATA = [
    # Format: (facing_direction, standing_tile_id, ledge_tile_id, required_input)
    ("SPRITE_FACING_DOWN", 0x2C, 0x37, "D_DOWN"),
    ("SPRITE_FACING_DOWN", 0x39, 0x36, "D_DOWN"),
    ("SPRITE_FACING_DOWN", 0x39, 0x37, "D_DOWN"),
    ("SPRITE_FACING_LEFT", 0x2C, 0x27, "D_LEFT"),
    ("SPRITE_FACING_LEFT", 0x39, 0x27, "D_LEFT"),
    ("SPRITE_FACING_RIGHT", 0x2C, 0x0D, "D_RIGHT"),
    ("SPRITE_FACING_RIGHT", 0x2C, 0x1D, "D_RIGHT"),
    ("SPRITE_FACING_RIGHT", 0x39, 0x0D, "D_RIGHT"),
]

# Derived ledge tiles by direction for backward compatibility
LEDGE_TILES = {
    TilesetID.OVERWORLD: {
        "down": {0x36, 0x37},  # Tiles you can jump down from
        "left": {0x27},  # Tiles you can jump left from
        "right": {0x0D, 0x1D},  # Tiles you can jump right from
    }
}

# Special tiles - these would need analysis of actual pokered graphics and behaviors
GRASS_TILES = {TilesetID.OVERWORLD: {0x52, 0x53}}  # Grass encounter tiles
SIGN_TILES = {TilesetID.OVERWORLD: {0x5A, 0x5D}}  # Readable sign tiles
BOOKSHELF_TILES = {
    TilesetID.REDS_HOUSE_1: {0x48, 0x49},
    TilesetID.MANSION: {0x4A, 0x4B},
}  # Readable bookshelf tiles
STRENGTH_BOULDER_TILES = {
    TilesetID.OVERWORLD: {0x15, 0x55},  # Movable boulder tiles
    TilesetID.CAVERN: {0x18, 0x19},
}  # Strength boulder tiles
PC_TILES = {
    TilesetID.REDS_HOUSE_1: {0x50, 0x51},
    TilesetID.POKECENTER: {0x52, 0x53},
}  # PC accessible tiles

# NOTE: The following tile categories are not directly represented in pokered source
# but could be derived from tileset analysis or are concepts for future expansion:

# Animated tiles - would need analysis of tileset animation data
# ANIMATED_TILES = {}  # Removed - not directly in pokered source

# Trainer sight line tiles - would need analysis of trainer interaction code
# TRAINER_SIGHT_TILES = {}  # Removed - not directly in pokered source

# Special zone tiles - would need analysis of map-specific behaviors
# SAFARI_ZONE_TILES = {}  # Removed - map-specific behavior, not tile-specific
# GAME_CORNER_TILES = {}  # Removed - map-specific behavior, not tile-specific
# FLY_DESTINATION_TILES = {}  # Removed - map-specific behavior, not tile-specific

# Audio tiles - would need analysis of footstep sound code
# FOOTSTEP_SOUND_TILES = {}  # Removed - not directly in pokered source
