import TracesNav from '~/components/ExperimentsNav';
import type { Route } from './+types/run.$runId';
import MLFlowClient from '~/MLFlowClient';

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
  return { runs, run, modelName };
}

export default function RunDetail({ loaderData }: Route.ComponentProps) {
  const { run } = loaderData;

  return (
    <div className="flex flex-row gap-1 h-full">
      <TracesNav runs={loaderData.runs} />
      <div className="grow px-2 bg-background1" box-="square" shear-="top">
        <span variant-="background">Run Details</span>

        <div className="flex flex-col mt-[1lh]">
          <div>
            <div className="">
              <div>
                <strong>Name:</strong> {run.info.run_name} ({run.info.run_id})
              </div>
              <div>
                <strong>Model:</strong> {loaderData.modelName ?? 'Unknown'}
              </div>
              <div>
                <strong>Status:</strong> {run.info.status}
              </div>
              <div>
                <strong>Start Time:</strong>{' '}
                {new Date(run.info.start_time).toLocaleString()}
              </div>
              {run.info.end_time && (
                <div>
                  <strong>End Time:</strong>{' '}
                  {new Date(run.info.end_time).toLocaleString()}
                </div>
              )}
            </div>
          </div>
          <div is-="separator" direction-="x" />
        </div>
      </div>
    </div>
  );
}
