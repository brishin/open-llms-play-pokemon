import { useEffect } from 'react';
import { BoxContainer } from './BoxContainer';
import { AnnotatedScreenshot } from './AnnotatedScreenshot';

interface ScreenshotSliderProps {
  artifacts: any[];
  runId: string;
  currentIndex: number;
  setCurrentIndex: (index: number) => void;
}

export function ScreenshotSlider({
  artifacts,
  runId,
  currentIndex,
  setCurrentIndex,
}: ScreenshotSliderProps) {
  // Filter for screenshot artifacts and sort by step number
  const screenshots = artifacts
    .filter(
      (artifact) =>
        artifact?.path?.startsWith('screenshot_') && artifact?.path?.endsWith('.png'),
    )
    .sort((a, b) => {
      const stepA = Number.parseInt(a.path.match(/screenshot_(\d+)\.png/)?.[1] || '0');
      const stepB = Number.parseInt(b.path.match(/screenshot_(\d+)\.png/)?.[1] || '0');
      return stepA - stepB;
    });

  const getArtifactUrl = (artifactPath: string) => {
    return `/api/mlflow/artifact?runId=${encodeURIComponent(runId)}&artifactPath=${encodeURIComponent(artifactPath)}`;
  };

  const getCurrentScreenshot = () => {
    if (screenshots.length === 0) return null;
    return screenshots[currentIndex];
  };

  const getCurrentStepNumber = () => {
    const screenshot = getCurrentScreenshot();
    if (!screenshot) return 0;
    const stepMatch = screenshot.path.match(/screenshot_(\d+)\.png/);
    return stepMatch ? Number.parseInt(stepMatch[1]) : currentIndex + 1;
  };

  const handleSliderChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentIndex(Number.parseInt(event.target.value));
  };

  const handlePrevious = () => {
    setCurrentIndex(Math.max(0, currentIndex - 1));
  };

  const handleNext = () => {
    setCurrentIndex(Math.min(screenshots.length - 1, currentIndex + 1));
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        setCurrentIndex(Math.max(0, currentIndex - 1));
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        setCurrentIndex(Math.min(screenshots.length - 1, currentIndex + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, screenshots.length, setCurrentIndex]);

  if (screenshots.length === 0) {
    return (
      <BoxContainer shear="top" title="Screenshots" className="px-[1ch] pb-[1ch]">
        <div className="mt-[0.5lh] text-sm text-gray-500">
          No screenshots found for this run.
        </div>
      </BoxContainer>
    );
  }

  const currentScreenshot = getCurrentScreenshot();
  const currentStepNumber = getCurrentStepNumber();

  return (
    <BoxContainer
      shear="top"
      title={`Screenshots - Step ${currentStepNumber} (${currentIndex + 1}/${screenshots.length})`}
      className="px-[1ch] pb-[1ch]"
    >
      <div className="mt-[0.5lh] flex flex-col gap-[0.5lh]">
        {/* Main screenshot display */}
        <div className="flex justify-center min-h-[20lh]">
          {currentScreenshot && (
            <AnnotatedScreenshot
              src={getArtifactUrl(currentScreenshot.path)}
              alt={`Screenshot ${currentStepNumber}`}
              className="max-w-[60ch] min-w-3/4"
              maxWidth={480}
              maxHeight={320}
            />
          )}
        </div>

        {/* Controls */}
        <div className="flex flex-col gap-[0.25lh]">
          {/* Slider */}
          <div className="flex items-center gap-[1ch]">
            <div box-="square">
              <button
                type="button"
                onClick={handlePrevious}
                disabled={currentIndex === 0}
              >
                ←
              </button>
            </div>

            <div className="flex-grow flex items-center gap-[1ch]">
              <span className="text-sm text-gray-600 min-w-[3ch]">1</span>
              <input
                type="range"
                min="0"
                max={screenshots.length - 1}
                value={currentIndex}
                onChange={handleSliderChange}
                className="flex-grow h-[0.5lh] bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <span className="text-sm text-gray-600 min-w-[3ch]">
                {screenshots.length}
              </span>
            </div>

            <div box-="square">
              <button
                type="button"
                onClick={handleNext}
                disabled={currentIndex === screenshots.length - 1}
              >
                →
              </button>
            </div>
          </div>

          {/* Step info */}
          <div className="text-center text-sm text-gray-600">
            Step {currentStepNumber} • Use arrow keys or slider to navigate
          </div>
        </div>
      </div>
    </BoxContainer>
  );
}
