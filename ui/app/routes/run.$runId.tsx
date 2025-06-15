import TracesNav from '~/components/ExperimentsNav';
import type { Route } from './+types/run.$runId';
import MLFlowClient from '~/MLFlowClient';
import { BoxContainer } from '~/components/BoxContainer';
import { MetricsDisplay } from '~/components/MetricsDisplay';
import { ScreenshotGallery } from '~/components/ScreenshotGallery';
import { GameDataViewer } from '~/components/GameDataViewer';

export async function loader({ params }: Route.LoaderArgs) {
  const mlflow = new MLFlowClient('http://localhost:8080');
  const experiment = await mlflow.getExperiment('open-llms-play-pokemon');
  const [runs, run, artifacts, traces] = await Promise.all([
    mlflow.listRuns(experiment.experiment_id),
    mlflow.getRun(params.runId),
    mlflow.getArtifacts(params.runId),
    mlflow.getTraces({
      experimentIds: [experiment.experiment_id],
      orderBy: 'timestamp_ms DESC',
      sourceRun: params.runId,
    }),
  ]);
  console.log(JSON.stringify(run, null, 2));
  const modelName = run.data.tags?.find((tag) => tag.key === 'llm_name')?.value;
  return { runs, run, artifacts, traces, modelName };
}

export default function RunDetail({ loaderData }: Route.ComponentProps) {
  const { run, artifacts, traces } = loaderData;

  return (
    <div className="flex flex-row gap-1 h-full">
      <TracesNav runs={loaderData.runs} />
      <div className="flex flex-col gap-[0.25lh] grow overflow-y-auto">
        {/* Basic run info */}
        <BoxContainer shear="top" className="px-[1ch] py-[0.5lh] flex-shrink-0">
          <span variant-="background">Run Details</span>
          <div className="mt-[0.5lh] grid grid-cols-2 gap-[4ch] text-sm">
            <div>
              <div>
                <strong>Name:</strong> {run.info.run_name}
              </div>
              <div>
                <strong>Model:</strong> {loaderData.modelName ?? 'Unknown'}
              </div>
              <div>
                <strong>Status:</strong> {run.info.status}
              </div>
            </div>
            <div>
              <div>
                <strong>Start:</strong> {new Date(run.info.start_time).toLocaleString()}
              </div>
              {run.info.end_time && (
                <div>
                  <strong>End:</strong> {new Date(run.info.end_time).toLocaleString()}
                </div>
              )}
              <div>
                <strong>Run ID:</strong>{' '}
                <span className="font-mono text-xs">{run.info.run_id}</span>
              </div>
            </div>
          </div>
        </BoxContainer>

        {/* Metrics display */}
        <MetricsDisplay run={run} />

        {/* Screenshots and game data in a grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-[0.25lh] flex-grow">
          <ScreenshotGallery artifacts={artifacts} runId={run.info.run_id} />
          <GameDataViewer artifacts={artifacts} runId={run.info.run_id} />
        </div>
      </div>
    </div>
  );
}
