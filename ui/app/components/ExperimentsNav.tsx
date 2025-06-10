import { NavLink } from 'react-router';
import type { MLFlowRun } from '~/MLFlowClient';

export default function ExperimentsNav({ runs }: { runs: MLFlowRun[] }) {
  return (
    <nav box-="square" shear-="top" className="max-w-32 h-full px-2 bg-background1">
      <span variant-="background">Experiments</span>
      <div className="my-[1lh] px-1">
        <div className="flex-col gap-[1lh] overflow-y-auto">
          <ul>
            {runs.map((run) => (
              <li key={run.info.run_id}>
                <NavLink to={`/run/${run.info.run_id}`}>{run.info.run_name}</NavLink>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </nav>
  );
}
