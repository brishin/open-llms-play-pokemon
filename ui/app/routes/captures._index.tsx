import { capturesDirectoryExists, getCaptureListItems } from '~/captures/Captures';
import CapturesNav from '~/components/CapturesNav';
import type { Route } from './+types/captures._index';

export async function loader() {
  if (!capturesDirectoryExists()) {
    return { captures: [], directoryExists: false };
  }

  const captures = await getCaptureListItems();
  return { captures, directoryExists: true };
}

export default function CapturesIndex({ loaderData }: Route.ComponentProps) {
  return (
    <div className="flex-row gap-1 h-full">
      <CapturesNav captures={loaderData.captures} />
    </div>
  );
}
