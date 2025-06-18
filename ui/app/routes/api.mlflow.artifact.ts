import type { Route } from './+types/api.mlflow.artifact';
import MLFlowClient from '~/mflow/MLFlowClient';

export async function loader({ request }: Route.LoaderArgs) {
  const url = new URL(request.url);
  const runId = url.searchParams.get('runId');
  const artifactPath = url.searchParams.get('artifactPath');

  if (!runId || !artifactPath) {
    throw new Response('Missing runId or artifactPath', { status: 400 });
  }

  try {
    const mlflowClient = new MLFlowClient('http://localhost:8080');
    const artifact = await mlflowClient.getArtifactBinary(runId, artifactPath);
    
    // Return the artifact as a binary response with appropriate headers
    return new Response(artifact, {
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (error) {
    console.error('Failed to load artifact:', error);
    throw new Response('Internal server error', { status: 500 });
  }
}