import { useState, useEffect } from 'react';
import { useFetcher } from 'react-router';
import { BoxContainer } from './BoxContainer';

interface GameDataViewerProps {
  artifacts: any[];
  runId: string;
}

interface GameStateData {
  step_counter?: number;
  timestamp?: string;
  badges_obtained?: number;
  party_count?: number;
  current_map?: number;
  is_in_battle?: boolean;
  player_position?: { x: number; y: number };
  directions_available?: string[];
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

export function GameDataViewer({ artifacts, runId }: GameDataViewerProps) {
  const [selectedArtifactPath, setSelectedArtifactPath] = useState<string>('');
  const fetcher = useFetcher<GameStateData>();

  // Filter for game state JSON artifacts and sort by step number
  const gameStateFiles = artifacts
    .filter(
      (artifact) =>
        artifact.path?.startsWith('game_state_step_') && artifact.path?.endsWith('.json'),
    )
    .sort((a, b) => {
      const stepA = Number.parseInt(a.path.match(/game_state_step_(\d+)\.json/)?.[1] || '0');
      const stepB = Number.parseInt(b.path.match(/game_state_step_(\d+)\.json/)?.[1] || '0');
      return stepB - stepA; // Latest first
    });

  const loadGameData = (artifactPath: string) => {
    setSelectedArtifactPath(artifactPath);
    fetcher.load(`/api/game-state?runId=${encodeURIComponent(runId)}&artifactPath=${encodeURIComponent(artifactPath)}`);
  };

  // Load the latest game state by default
  useEffect(() => {
    if (gameStateFiles.length > 0 && !selectedArtifactPath) {
      loadGameData(gameStateFiles[0].path);
    }
  }, [gameStateFiles, selectedArtifactPath]);

  return (
    <BoxContainer shear="top" className="p-4">
      <span variant-="background">Game State Data ({gameStateFiles.length})</span>

      {gameStateFiles.length === 0 ? (
        <div className="mt-[1lh] text-sm text-gray-500">
          No game state data found for this run.
        </div>
      ) : (
        <div className="mt-[1lh] space-y-[1lh]">
          {/* File selector */}
          <div>
            <label htmlFor="game-state-selector" className="block text-sm font-medium mb-[0.5lh]">Select Game State:</label>
            <select
              id="game-state-selector"
              className="w-full p-[0.5ch] border rounded text-sm"
              onChange={(e) => loadGameData(e.target.value)}
              value={selectedArtifactPath}
            >
              {gameStateFiles.map((file) => {
                const stepMatch = file.path.match(/game_state_step_(\d+)\.json/);
                const stepNumber = stepMatch ? stepMatch[1] : 'Unknown';
                return (
                  <option key={file.path} value={file.path}>
                    Step {stepNumber}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Game data display */}
          {fetcher.state === 'loading' ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : fetcher.data ? (
            <div className="space-y-[1lh]">
              {/* Key metrics */}
              <div className="grid grid-cols-2 gap-[4ch]">
                <div>
                  <h4 className="font-semibold text-sm mb-[0.5lh]">Basic Info</h4>
                  <div className="space-y-[0.25lh] text-sm">
                    <div className="flex justify-between">
                      <span>Step:</span>
                      <span className="font-mono">{fetcher.data.step_counter}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Badges:</span>
                      <span className="font-mono">{fetcher.data.badges_obtained}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Party Count:</span>
                      <span className="font-mono">{fetcher.data.party_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Current Map:</span>
                      <span className="font-mono">{fetcher.data.current_map}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>In Battle:</span>
                      <span className="font-mono">
                        {fetcher.data.is_in_battle ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-sm mb-[0.5lh]">Position & Movement</h4>
                  <div className="space-y-[0.25lh] text-sm">
                    {fetcher.data.player_position && (
                      <div className="flex justify-between">
                        <span>Position:</span>
                        <span className="font-mono">
                          ({fetcher.data.player_position.x},{' '}
                          {fetcher.data.player_position.y})
                        </span>
                      </div>
                    )}
                    {fetcher.data.directions_available && Array.isArray(fetcher.data.directions_available) && (
                      <div>
                        <span>Available Directions:</span>
                        <div className="font-mono text-xs mt-[0.25lh]">
                          {fetcher.data.directions_available.join(', ')}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Party Pokemon */}
              {fetcher.data.party_pokemon && Array.isArray(fetcher.data.party_pokemon) && fetcher.data.party_pokemon.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-[0.5lh]">Party Pokemon</h4>
                  <div className="grid grid-cols-1 gap-[0.5lh]">
                    {fetcher.data.party_pokemon.map((pokemon, index) => (
                      <div key={`pokemon-${pokemon.species || 'unknown'}-${index}`} className="border rounded p-[0.5ch] text-sm">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">
                            {pokemon.species || 'Unknown'}
                          </span>
                          <span className="text-xs">Level {pokemon.level || '?'}</span>
                        </div>
                        {pokemon.current_hp !== undefined &&
                          pokemon.max_hp !== undefined && (
                            <div className="text-xs text-gray-600">
                              HP: {pokemon.current_hp}/{pokemon.max_hp}
                              {pokemon.status && ` (${pokemon.status})`}
                            </div>
                          )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Inventory */}
              {fetcher.data.inventory && Array.isArray(fetcher.data.inventory) && fetcher.data.inventory.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-[0.5lh]">Inventory</h4>
                  <div className="max-h-[8lh] overflow-y-auto">
                    <div className="grid grid-cols-2 gap-[0.25ch] text-xs">
                      {fetcher.data.inventory.map((item, index) => (
                        <div key={`item-${item.item || 'unknown'}-${index}`} className="flex justify-between border-b py-[0.25lh]">
                          <span>{item.item || 'Unknown Item'}</span>
                          <span className="font-mono">{item.quantity || 0}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Raw JSON (collapsible) */}
              <details className="mt-[1lh]">
                <summary className="cursor-pointer font-semibold text-sm">
                  Raw JSON Data
                </summary>
                <pre className="mt-[0.5lh] p-[0.5ch] bg-gray-100 rounded text-xs overflow-auto max-h-[16lh]">
                  {JSON.stringify(fetcher.data, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <div className="text-sm text-gray-500">Failed to load game data.</div>
          )}
        </div>
      )}
    </BoxContainer>
  );
}
