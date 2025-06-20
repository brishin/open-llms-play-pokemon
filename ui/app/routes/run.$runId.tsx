import { useState } from 'react';
import { BoxContainer, BoxContainerContent } from '~/components/BoxContainer';
import TracesNav from '~/components/ExperimentsNav';
import { GameDataPane } from '~/components/GameDataPane';
import { MetricsDisplay } from '~/components/MetricsDisplay';
import { ScreenshotsPane } from '~/components/ScreenshotsPane';
import TracePane from '~/components/trace/TracePane';
import MLFlowClient from '~/mflow/MLFlowClient';
import type { Route } from './+types/run.$runId';

export async function loader({ params }: Route.LoaderArgs) {
  const mlflow = new MLFlowClient('http://localhost:8080');
  const experiment = await mlflow.getExperiment('open-llms-play-pokemon');
  const [runs, run, artifacts, trace] = await Promise.all([
    mlflow.listRuns(experiment.experiment_id),
    mlflow.getRun(params.runId),
    mlflow.getArtifacts(params.runId),
    mlflow.getTraceForRun(experiment.experiment_id, params.runId),
  ]);
  const modelName = run.data.tags?.find((tag) => tag.key === 'llm_name')?.value;
  return { runs, run, artifacts, trace, modelName };
}

export default function RunDetail({ loaderData }: Route.ComponentProps) {
  const { run, artifacts, trace } = loaderData;
  const [currentSliderIndex, setCurrentSliderIndex] = useState(0);

  // Extract screenshot step number from slider index
  const screenshots = (artifacts as any[])
    .filter(
      (artifact) =>
        artifact?.path?.startsWith('screenshot_') && artifact?.path?.endsWith('.png'),
    )
    .sort((a, b) => {
      const stepA = Number.parseInt(a?.path?.match(/screenshot_(\d+)\.png/)?.[1] || '0');
      const stepB = Number.parseInt(b?.path?.match(/screenshot_(\d+)\.png/)?.[1] || '0');
      return stepA - stepB;
    });

  const getCurrentStepNumber = () => {
    if (screenshots.length === 0) return 0;
    const screenshot = screenshots[currentSliderIndex];
    if (!screenshot?.path) return 0;
    const stepMatch = screenshot.path.match(/screenshot_(\d+)\.png/);
    return stepMatch ? Number.parseInt(stepMatch[1]) : currentSliderIndex + 1;
  };

  return (
    <div className="flex flex-row gap-1 h-screen">
      <TracesNav runs={loaderData.runs} />
      <div className="flex flex-col gap-[0.25lh] grow overflow-y-auto">
        {/* Basic run info */}
        <BoxContainer shear="top" title="Run Details">
          <BoxContainerContent className="grid grid-cols-2 gap-[4ch]">
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
                <strong>Run ID:</strong> <span>{run.info.run_id}</span>
              </div>
            </div>
          </BoxContainerContent>
        </BoxContainer>

        {/* Metrics display */}
        <MetricsDisplay run={run} />

        {/* Screenshots and game data in a grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-[0.25lh] flex-grow">
          <ScreenshotsPane
            artifacts={artifacts}
            runId={run.info.run_id}
            currentIndex={currentSliderIndex}
            setCurrentIndex={setCurrentSliderIndex}
          />
          <div className="flex flex-col gap-[0.25lh]">
            <GameDataPane
              artifacts={artifacts}
              runId={run.info.run_id}
              currentSliderStep={getCurrentStepNumber()}
            />
            <TracePane trace={trace} currentStep={getCurrentStepNumber()} />
          </div>
        </div>
      </div>
    </div>
  );
}
