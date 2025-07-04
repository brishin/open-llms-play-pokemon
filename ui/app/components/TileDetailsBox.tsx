import type { TileData } from '~/game-state/GameState.types';
import { formatMapDisplay } from '~/utils/mapNames';
import { BoxContainer, BoxContainerContent } from './BoxContainer';

interface TileDetailsBoxProps {
  hoveredTile: TileData | null;
  tilePosition: { x: number; y: number } | null;
}

export function TileDetailsBox({ hoveredTile, tilePosition }: TileDetailsBoxProps) {
  if (!hoveredTile || !tilePosition) {
    return (
      <BoxContainer shear="top" title="Tile Details">
        <BoxContainerContent>
          <div className="text-muted">
            Hover over a tile in the screenshot to see details
          </div>
        </BoxContainerContent>
      </BoxContainer>
    );
  }

  const formatTileType = (tile: TileData) => {
    if (tile.is_warp_tile) return 'Warp/Door';
    if (tile.is_encounter_tile) return 'Encounter/Grass';
    if (tile.is_ledge_tile) return 'Ledge';
    if (tile.trainer_sight_line) return 'Trainer Sight';
    if (tile.is_walkable) return 'Walkable';
    return 'Blocked';
  };

  const getSpecialProperties = (tile: TileData) => {
    const props = [];
    if (tile.has_sign) props.push('Sign');
    if (tile.has_bookshelf) props.push('Bookshelf');
    if (tile.strength_boulder) props.push('Boulder');
    if (tile.cuttable_tree) props.push('Tree');
    if (tile.pc_accessible) props.push('PC');
    if (tile.hidden_item_id !== null) props.push('Hidden Item');
    if (tile.game_corner_tile) props.push('Game Corner');
    if (tile.is_fly_destination) props.push('Fly Destination');
    if (tile.ledge_direction) props.push(`Ledge ${tile.ledge_direction}`);
    return props;
  };

  const specialProps = getSpecialProperties(hoveredTile);

  return (
    <BoxContainer shear="top" title="Tile Details">
      <BoxContainerContent>
        <div>
          <div className="flex gap-[4ch]">
            <div className="flex-1">
              <strong>Position:</strong> ({tilePosition.x}, {tilePosition.y})
            </div>
            <div className="flex-1">
              <strong>Type:</strong> {formatTileType(hoveredTile)}
            </div>
          </div>

          <div className="flex gap-[4ch]">
            <div className="flex-1">
              <strong>Tile ID:</strong> {hoveredTile.tile_id}
            </div>
            <div className="flex-1">
              <strong>Raw Type:</strong> {hoveredTile.tile_type}
            </div>
          </div>

          {(hoveredTile.map_x !== hoveredTile.x ||
            hoveredTile.map_y !== hoveredTile.y) && (
            <div className="flex-1">
              <strong>Map Position:</strong> ({hoveredTile.map_x}, {hoveredTile.map_y})
            </div>
          )}

          {hoveredTile.hidden_item_id !== null && (
            <div className="flex gap-[4ch]">
              <div className="flex-1">
                <strong>Hidden Item ID:</strong> {hoveredTile.hidden_item_id}
              </div>
              {hoveredTile.requires_itemfinder && (
                <div className="flex-1">
                  <strong>Needs Itemfinder:</strong> Yes
                </div>
              )}
            </div>
          )}

          {specialProps.length > 0 && (
            <div className="flex-1">
              <strong>Properties:</strong> {specialProps.join(', ')}
            </div>
          )}

          {hoveredTile.warp_destination_map !== null && (
            <div className="flex-1">
              <strong>Warp To:</strong>{' '}
              {formatMapDisplay(hoveredTile.warp_destination_map)} (
              {hoveredTile.warp_destination_x}, {hoveredTile.warp_destination_y})
            </div>
          )}

          {hoveredTile.trainer_id !== null && (
            <div className="flex-1">
              <strong>Trainer ID:</strong> {hoveredTile.trainer_id}
            </div>
          )}

          {hoveredTile.water_current_direction && (
            <div className="flex-1">
              <strong>Water Current:</strong> {hoveredTile.water_current_direction}
            </div>
          )}
        </div>
      </BoxContainerContent>
    </BoxContainer>
  );
}
