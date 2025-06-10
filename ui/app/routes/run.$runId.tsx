import TracesNav from '~/components/TracesNav';
import type { Route } from './+types/run.$runId';
import MLFlowClient from '~/MLFlowClient';

export async function loader({ params }: Route.LoaderArgs) {
  const mlflow = new MLFlowClient('http://localhost:8080');
  const experiment = await mlflow.getExperiment('open-llms-play-pokemon');
  const runs = await mlflow.listRuns(experiment.experiment_id);
  const run = await mlflow.getRun(params.runId);
  return { runs, run };
}

export default function RunDetail({ loaderData }: Route.ComponentProps) {
  const { run } = loaderData;
  console.log(run);

  return (
    <div className="flex flex-row gap-1 h-full">
      <TracesNav runs={loaderData.runs} />
      <div className="grow px-2 gap-[1lh]" box-="square" shear-="top">
        <span variant-="background">Run Details</span>

        <div className="flex flex-col my-[1lh] gap-[1lh]">
          <div>
            <h2 className="mb-[1lh]">Run Information</h2>
            <div className="">
              <div>
                <strong>Name:</strong> {run.info.run_name}
              </div>
              <div>
                <strong>ID:</strong> {run.info.run_id}
              </div>
              <div>
                <strong>Status:</strong> {run.info.status}
              </div>
              <div>
                <strong>User:</strong> {run.info.user_id}
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

          <div>
            <h2 className="mb-2">Parameters</h2>
            <div className="space-y-1">
              {Object.entries(run.data.params ?? {}).map(([key, value]) => (
                <div key={key}>
                  <strong>{key}:</strong> {value}
                </div>
              ))}
            </div>
          </div>
        </div>

        {run.data.metrics?.length && (
          <div className="mt-6">
            <h2 className="mb-2">Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {run.data.metrics?.map((metric, index) => (
                <div key={`${metric.key}-${index}`} className="border p-3 rounded">
                  <div>
                    <strong>{metric.key}:</strong> {metric.value}
                  </div>
                  <div className="text-sm text-gray-600">Step: {metric.step}</div>
                  <div className="text-sm text-gray-600">
                    Time: {new Date(metric.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
