import type { Route } from './+types/api.game-state';

export async function loader({ request }: Route.LoaderArgs) {
  const url = new URL(request.url);
  const runId = url.searchParams.get('runId');
  const artifactPath = url.searchParams.get('artifactPath');

  if (!runId || !artifactPath) {
    throw new Response('Missing runId or artifactPath', { status: 400 });
  }

  try {
    // Fetch the game state data from MLflow
    const response = await fetch(
      `http://localhost:8080/get-artifact?path=${encodeURIComponent(artifactPath)}&run_uuid=${runId}`,
    );

    if (!response.ok) {
      throw new Response('Failed to fetch game state data', { status: response.status });
    }

    const gameData = await response.json();
    return gameData;
  } catch (error) {
    console.error('Failed to load game data:', error);
    throw new Response('Internal server error', { status: 500 });
  }
}
