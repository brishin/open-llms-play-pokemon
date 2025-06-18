import type { GameStateFile } from './GameState.types';

/**
 * Filters and sorts artifacts to find game state JSON files
 */
export function getGameStateFiles(artifacts: any[]): GameStateFile[] {
  return artifacts
    .filter(
      (artifact) =>
        artifact.path?.startsWith('game_state_step_') && artifact.path?.endsWith('.json'),
    )
    .map((artifact) => {
      const stepMatch = artifact.path.match(/game_state_step_(\d+)\.json/);
      return {
        path: artifact.path,
        step: stepMatch ? Number.parseInt(stepMatch[1]) : 0,
      };
    })
    .sort((a, b) => a.step - b.step); // Earliest first for closest step search
}

/**
 * Finds the closest valid step, preferring states prior to current state
 */
export function findClosestGameStateStep(
  gameStateFiles: GameStateFile[],
  targetStep: number,
): GameStateFile | null {
  if (gameStateFiles.length === 0) return null;

  // Find the closest step that is <= targetStep (preferring prior states)
  const priorSteps = gameStateFiles.filter((item) => item.step <= targetStep);
  if (priorSteps.length > 0) {
    // Return the highest step that is <= targetStep
    return priorSteps[priorSteps.length - 1];
  }

  // If no prior steps, return the earliest available step
  return gameStateFiles[0];
}

/**
 * Constructs the API URL for fetching game state data
 */
export function getGameStateApiUrl(runId: string, artifactPath: string): string {
  return `/api/game-state?runId=${encodeURIComponent(runId)}&artifactPath=${encodeURIComponent(artifactPath)}`;
}
