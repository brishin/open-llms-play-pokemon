import type { Route } from './+types/_index';
import MLFlowClient from '~/MLFlowClient';
import TracesNav from '~/components/ExperimentsNav';

export async function loader() {
  const mlflow = new MLFlowClient('http://localhost:8080');
  const experiment = await mlflow.getExperiment('open-llms-play-pokemon');
  const runs = await mlflow.listRuns(experiment.experiment_id);
  return { runs };
}

export default function Home({ loaderData }: Route.ComponentProps) {
  return (
    <div className="flex-row gap-1 h-full">
      <TracesNav runs={loaderData.runs} />
    </div>
  );
}
