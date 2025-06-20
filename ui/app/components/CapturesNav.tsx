import { NavLink } from 'react-router';
import type { CaptureListItem } from '~/captures/Capture.types';
import { BoxContainer } from './BoxContainer';

export default function CapturesNav({ captures }: { captures: CaptureListItem[] }) {
  const getStatusColor = (isComplete: boolean) => {
    return isComplete ? 'text-success' : 'text-info';
  };

  const getStatusIcon = (isComplete: boolean) => {
    return isComplete ? '✓' : '⚠';
  };

  return (
    <BoxContainer
      as="nav"
      shear="top"
      className="min-w-[20ch] h-full flex flex-col"
      title={`Captures (${captures.length})`}
    >
      <div className="my-[1lh] px-[1ch] flex-1 min-h-0">
        <div className="overflow-y-auto gap-[1lh] h-full">
          {captures.length === 0 ? (
            <div className="text-center py-4 text-muted">
              <p>No captures found</p>
              <p className="mt-[2lh]">
                Press 'Q' in the interactive player to create captures
              </p>
            </div>
          ) : (
            <ul>
              {captures.map((capture) => (
                <NavLink
                  to={`/captures/${capture.captureId}`}
                  className={({ isActive }) =>
                    `block hover:bg-hover p-[0.5ch] transition-colors ${
                      isActive ? 'bg-active' : ''
                    }`
                  }
                >
                  <div
                    className="font-medium truncate"
                    title={`Capture ${capture.captureId}`}
                  >
                    {capture.captureId}
                  </div>
                  <div className="text-muted">{capture.formattedTimestamp}</div>
                </NavLink>
              ))}
            </ul>
          )}
        </div>
      </div>
    </BoxContainer>
  );
}
