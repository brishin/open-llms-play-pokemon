import { NavLink } from 'react-router';
import type { MLFlowRun } from '~/MLFlowClient';
import { BoxContainer } from './BoxContainer';
import dayjs from '~/dayjs';

export default function ExperimentsNav({ runs }: { runs: MLFlowRun[] }) {
  const getLatestMetric = (run: MLFlowRun, metricKey: string) => {
    const metrics = run.data.metrics || [];
    const metric = metrics.find((m) => m.key === metricKey);
    return metric?.value;
  };

  const getRunDuration = (run: MLFlowRun) => {
    if (!run.info.end_time) return 'Running...';
    const duration = (run.info.end_time - run.info.start_time) / 1000;
    return `${Math.round(duration)}s`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'FINISHED':
        return 'text-green-600';
      case 'FAILED':
        return 'text-red-600';
      case 'RUNNING':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <BoxContainer
      as="nav"
      shear="top"
      className="min-w-[16ch] h-full flex flex-col"
      title={`Runs (${runs.length})`}
    >
      <div className="my-[1lh] px-[1ch] flex-1 min-h-0">
        <div className="overflow-y-auto gap-[1lh">
          <ul>
            {runs.map((run) => {
              const badges = getLatestMetric(run, 'badges');
              const partyCount = getLatestMetric(run, 'party_count');

              return (
                <li key={run.info.run_id} className="border-b border-gray-200 pb-[0.5lh]">
                  <NavLink
                    to={`/run/${run.info.run_id}`}
                    className={({ isActive }) =>
                      `block hover:bg-gray-100 p-[0.5ch] transition-colors ${
                        isActive ? 'bg-blue-100' : ''
                      }`
                    }
                  >
                    <div className="font-medium truncate" title={run.info.run_name}>
                      {run.info.run_name}
                    </div>
                    <div className={`${getStatusColor(run.info.status)}`}>
                      {run.info.status}
                    </div>
                    <div className="text-gray-500 mt-[0.25lh]">{getRunDuration(run)}</div>
                    {(badges !== undefined || partyCount !== undefined) && (
                      <div className="text-gray-600 mt-[0.25lh] space-y-[0.125lh]">
                        {badges !== undefined && <div>🏆 {badges} badges</div>}
                        {partyCount !== undefined && <div>👥 {partyCount} pokemon</div>}
                      </div>
                    )}
                    <div className="text-gray-400 mt-[0.25lh]">
                      {dayjs
                        .duration(dayjs(run.info.end_time).diff(dayjs()))
                        .humanize(true)}
                    </div>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </BoxContainer>
  );
}
