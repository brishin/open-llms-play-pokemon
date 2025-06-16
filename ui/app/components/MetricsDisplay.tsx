import type { MLFlowRun } from '~/MLFlowClient';
import { BoxContainer, BoxContainerContent } from './BoxContainer';

interface MetricsDisplayProps {
  run: MLFlowRun;
}

export function MetricsDisplay({ run }: MetricsDisplayProps) {
  const metrics = run.data.metrics || [];
  const tags = run.data.tags || [];

  // Get latest values for each metric
  const latestMetrics = metrics.reduce(
    (acc, metric) => {
      if (!acc[metric.key] || metric.timestamp > acc[metric.key].timestamp) {
        acc[metric.key] = metric;
      }
      return acc;
    },
    {} as Record<string, (typeof metrics)[0]>,
  );

  const maxSteps = tags.find((tag) => tag.key === 'max_steps')?.value;

  return (
    <BoxContainer shear="top" title="Game Metrics">
      <BoxContainerContent>
        <div className="mt-[0.5lh] grid grid-cols-2 gap-[4ch]">
          <div className="space-y-[0.5lh]">
            <h1 className="font-semibold">Progress Metrics</h1>
            <div className="space-y-[0.25lh]">
              <div className="flex justify-between">
                <span>Badges Obtained:</span>
                <span className="font-mono">{latestMetrics.badges?.value ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Party Count:</span>
                <span className="font-mono">{latestMetrics.party_count?.value ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Current Map:</span>
                <span className="font-mono">{latestMetrics.current_map?.value ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>In Battle:</span>
                <span className="font-mono">
                  {latestMetrics.is_in_battle?.value ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-[0.5lh]">
            <h1 className="font-semibold">Run Configuration</h1>
            <div className="space-y-[0.25lh]">
              <div className="flex justify-between">
                <span>Max Steps:</span>
                <span className="font-mono">{maxSteps ?? 'Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span>Steps Taken:</span>
                <span className="font-mono">
                  {metrics.length > 0 ? Math.max(...metrics.map((m) => m.step)) : 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Duration:</span>
                <span className="font-mono">
                  {run.info.end_time
                    ? `${Math.round((run.info.end_time - run.info.start_time) / 1000)}s`
                    : 'Running...'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {metrics.length > 0 && (
          <div className="mt-[1lh]">
            <h1 className="font-semibold mb-[0.5lh]">Metric History</h1>
            <div className="max-h-[8lh] overflow-y-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-[0.25ch]">Step</th>
                    <th className="text-left p-[0.25ch]">Badges</th>
                    <th className="text-left p-[0.25ch]">Party</th>
                    <th className="text-left p-[0.25ch]">Map</th>
                    <th className="text-left p-[0.25ch]">Battle</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics
                    .filter((m) => m.key === 'badges')
                    .sort((a, b) => b.step - a.step)
                    .slice(0, 10)
                    .map((metric) => {
                      const sameStepMetrics = metrics.filter(
                        (m) => m.step === metric.step,
                      );
                      const badges =
                        sameStepMetrics.find((m) => m.key === 'badges')?.value ?? 0;
                      const party =
                        sameStepMetrics.find((m) => m.key === 'party_count')?.value ?? 0;
                      const map =
                        sameStepMetrics.find((m) => m.key === 'current_map')?.value ?? 0;
                      const battle =
                        sameStepMetrics.find((m) => m.key === 'is_in_battle')?.value ?? 0;

                      return (
                        <tr key={metric.step} className="border-b">
                          <td className="p-[0.25ch] font-mono">{metric.step}</td>
                          <td className="p-[0.25ch] font-mono">{badges}</td>
                          <td className="p-[0.25ch] font-mono">{party}</td>
                          <td className="p-[0.25ch] font-mono">{map}</td>
                          <td className="p-[0.25ch] font-mono">
                            {battle ? 'Yes' : 'No'}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </BoxContainerContent>
    </BoxContainer>
  );
}
