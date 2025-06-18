/**
 * Note: The source of truth for these types is from
 * `open_llms_play_pokemon/game_state/game_state.py`.
 * Please use the Python as the source of truth for these types.
 */
export interface TileData {
  tile_id: number;
  x: number;
  y: number;
  map_x: number;
  map_y: number;
  tile_type: string;
  is_walkable: boolean;
  is_ledge_tile: boolean;
  ledge_direction: string | null;
  movement_modifier: number;
  is_encounter_tile: boolean;
  is_warp_tile: boolean;
  is_animated: boolean;
  light_level: number;
  has_sign: boolean;
  has_bookshelf: boolean;
  strength_boulder: boolean;
  cuttable_tree: boolean;
  pc_accessible: boolean;
  trainer_sight_line: boolean;
  trainer_id: number | null;
  hidden_item_id: number | null;
  requires_itemfinder: boolean;
  safari_zone_steps: boolean;
  game_corner_tile: boolean;
  is_fly_destination: boolean;
  has_footstep_sound: boolean;
  sprite_priority: number;
  background_priority: number;
  elevation_pair: number | null;
  sprite_offset: number;
  blocks_light: boolean;
  water_current_direction: string | null;
  warp_destination_map: number | null;
  warp_destination_x: number | null;
  warp_destination_y: number | null;
}

export interface TileMatrix {
  tiles: TileData[][];
  width: number;
  height: number;
  current_map: number;
  player_x: number;
  player_y: number;
  timestamp: string | null;
}

export interface GameState {
  step_counter?: number;
  timestamp?: string;
  player_name?: number;
  current_map?: number;
  player_x?: number;
  player_y?: number;
  party_count?: number;
  party_pokemon_levels?: number[];
  party_pokemon_hp?: number[];
  badges_obtained?: number;
  is_in_battle?: boolean;
  player_mon_hp?: number | null;
  enemy_mon_hp?: number | null;
  map_loading_status?: number;
  current_tileset?: number;
  tile_matrix?: TileMatrix;
  directions_available?: {
    north: boolean;
    south: boolean;
    east: boolean;
    west: boolean;
  };
  player_position?: { x: number; y: number };
  party_pokemon?: Array<{
    species?: string;
    level?: number;
    current_hp?: number;
    max_hp?: number;
    status?: string;
  }>;
  inventory?: Array<{
    item?: string;
    quantity?: number;
  }>;
  [key: string]: any;
}

export interface GameStateFile {
  path: string;
  step: number;
}
