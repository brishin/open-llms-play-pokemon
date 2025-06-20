import MLFlowClient from '~/mflow/MLFlowClient';
import type { Route } from './+types/api.game-state';

export async function loader({ request }: Route.LoaderArgs) {
  const url = new URL(request.url);
  const runId = url.searchParams.get('runId');
  const artifactPath = url.searchParams.get('artifactPath');

  if (!runId || !artifactPath) {
    throw new Response('Missing runId or artifactPath', { status: 400 });
  }

  try {
    const mlflowClient = new MLFlowClient('http://localhost:8080');
    const gameData = await mlflowClient.getArtifactJSON(runId, artifactPath);
    return gameData;
  } catch (error) {
    console.error('Failed to load game data:', error);
    throw new Response('Internal server error', { status: 500 });
  }
}
