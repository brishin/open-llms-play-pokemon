import { useState } from 'react';
import type { Route } from './+types/captures.$captureId';
import { getCaptureDetail, getCaptureListItems } from '~/captures/Captures';
import { BoxContainer, BoxContainerContent } from '~/components/BoxContainer';
import { AnnotatedScreenshot } from '~/components/AnnotatedScreenshot';
import { TileDetailsBox } from '~/components/TileDetailsBox';
import CapturesNav from '~/components/CapturesNav';
import type { TileData } from '~/game-state/GameState.types';

export async function loader({ params }: Route.LoaderArgs) {
  const [captureDetail, captures] = await Promise.all([
    getCaptureDetail(params.captureId),
    getCaptureListItems(),
  ]);

  if (!captureDetail) {
    throw new Response('Capture not found', { status: 404 });
  }

  return { captureDetail, captures };
}

export default function CaptureDetail({ loaderData }: Route.ComponentProps) {
  const { captureDetail, captures } = loaderData;
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [hoveredTile, setHoveredTile] = useState<TileData | null>(null);
  const [hoveredTilePosition, setHoveredTilePosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const formatGameStateStats = () => {
    const { gameState } = captureDetail;
    const stats = [];

    if (gameState.step_counter !== undefined) {
      stats.push(`Step: ${gameState.step_counter}`);
    }
    if (gameState.current_map !== undefined) {
      stats.push(`Map: ${gameState.current_map}`);
    }
    if (gameState.player_x !== undefined && gameState.player_y !== undefined) {
      stats.push(`Position: (${gameState.player_x}, ${gameState.player_y})`);
    }
    if (gameState.badges_obtained !== undefined) {
      stats.push(`Badges: ${gameState.badges_obtained}`);
    }
    if (gameState.party_count !== undefined) {
      stats.push(`Party: ${gameState.party_count} Pokemon`);
    }
    if (gameState.is_in_battle !== undefined) {
      stats.push(`Battle: ${gameState.is_in_battle ? 'Yes' : 'No'}`);
    }

    return stats;
  };

  const handleTileHover = (
    tile: TileData | null,
    position: { x: number; y: number } | null,
  ) => {
    setHoveredTile(tile);
    setHoveredTilePosition(position);
  };

  return (
    <div className="flex flex-row gap-1 h-screen">
      <CapturesNav captures={captures} />
      <div className="flex flex-col gap-[0.25lh] grow overflow-y-auto">
        {/* Header with controls */}
        <BoxContainer shear="top" title={`Capture ${captureDetail.captureId}`}>
          <BoxContainerContent>
            <div className="flex justify-between items-center">
              <div className="text-gray-600">
                {new Date(
                  captureDetail.timestamp.replace(
                    /(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/,
                    '$1-$2-$3T$4:$5:$6',
                  ),
                ).toLocaleString()}
              </div>

              <button type="button" onClick={() => setShowAnnotations(!showAnnotations)}>
                {showAnnotations ? 'Hide Annotations' : 'Show Annotations'}
              </button>
            </div>
          </BoxContainerContent>
        </BoxContainer>

        {/* Game state summary */}
        <BoxContainer shear="top" title="Game State Summary">
          <BoxContainerContent>
            <div className="flex flex-wrap gap-[4ch]">
              {formatGameStateStats().map((stat, index) => (
                <span key={`stat-${stat}`}>{stat}</span>
              ))}
            </div>
          </BoxContainerContent>
        </BoxContainer>

        {/* Main content area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-[0.25lh] flex-grow">
          {/* Screenshot with annotations */}
          <BoxContainer shear="top" title="Screenshot">
            <BoxContainerContent className="flex items-center justify-center min-h-[400px]">
              <AnnotatedScreenshot
                src={captureDetail.screenshotDataUrl}
                alt={`Capture ${captureDetail.captureId}`}
                gameState={captureDetail.gameState}
                showAnnotations={showAnnotations}
                maxWidth={800}
                maxHeight={600}
                className="max-w-full"
                onTileHover={handleTileHover}
              />
            </BoxContainerContent>
          </BoxContainer>

          {/* Game state details */}
          <div className="flex flex-col gap-[0.25lh]">
            <TileDetailsBox
              hoveredTile={hoveredTile}
              tilePosition={hoveredTilePosition}
            />
            {/* Movement directions */}
            {captureDetail.gameState.directions_available && (
              <BoxContainer shear="top" title="Available Directions">
                <BoxContainerContent>
                  <div className="grid grid-cols-2 gap-[2ch]">
                    {Object.entries(captureDetail.gameState.directions_available).map(
                      ([direction, available]) => (
                        <div
                          key={direction}
                          className={`flex items-center gap-2 ${available ? 'text-green-600' : 'text-red-600'}`}
                        >
                          <span>{available ? '✓' : '✗'}</span>
                          <span className="capitalize">{direction}</span>
                        </div>
                      ),
                    )}
                  </div>
                </BoxContainerContent>
              </BoxContainer>
            )}

            {/* Tile matrix info */}
            {captureDetail.gameState.tile_matrix && (
              <BoxContainer shear="top" title="Tile Matrix Info">
                <BoxContainerContent>
                  <div className="space-y-1">
                    <div>
                      <strong>Dimensions:</strong>{' '}
                      {captureDetail.gameState.tile_matrix.width} ×{' '}
                      {captureDetail.gameState.tile_matrix.height}
                    </div>
                    <div>
                      <strong>Total Tiles:</strong>{' '}
                      {captureDetail.gameState.tile_matrix.width *
                        captureDetail.gameState.tile_matrix.height}
                    </div>
                    {captureDetail.gameState.tile_matrix.current_map && (
                      <div>
                        <strong>Current Map:</strong>{' '}
                        {captureDetail.gameState.tile_matrix.current_map}
                      </div>
                    )}
                    {captureDetail.gameState.tile_matrix.player_x !== undefined &&
                      captureDetail.gameState.tile_matrix.player_y !== undefined && (
                        <div>
                          <strong>Player Position:</strong> (
                          {captureDetail.gameState.tile_matrix.player_x},{' '}
                          {captureDetail.gameState.tile_matrix.player_y})
                        </div>
                      )}
                  </div>
                </BoxContainerContent>
              </BoxContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
