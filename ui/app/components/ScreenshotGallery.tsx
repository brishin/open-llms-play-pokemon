import { useState } from 'react';
import { BoxContainer } from './BoxContainer';

interface ScreenshotGalleryProps {
  artifacts: any[];
  runId: string;
}

export function ScreenshotGallery({ artifacts, runId }: ScreenshotGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  
  // Filter for screenshot artifacts and sort by step number
  const screenshots = artifacts
    .filter(artifact => 
      artifact.path && 
      artifact.path.startsWith('screenshot_') && 
      artifact.path.endsWith('.png')
    )
    .sort((a, b) => {
      const stepA = Number.parseInt(a.path.match(/screenshot_(\d+)\.png/)?.[1] || '0');
      const stepB = Number.parseInt(b.path.match(/screenshot_(\d+)\.png/)?.[1] || '0');
      return stepA - stepB;
    });

  const getArtifactUrl = (artifactPath: string) => {
    return `http://localhost:8080/get-artifact?path=${encodeURIComponent(artifactPath)}&run_uuid=${runId}`;
  };

  return (
    <BoxContainer shear="top" className="p-4">
      <span variant-="background">Screenshots ({screenshots.length})</span>
      
      {screenshots.length === 0 ? (
        <div className="mt-[1lh] text-sm text-gray-500">
          No screenshots found for this run.
        </div>
      ) : (
        <>
          <div className="mt-[1lh] grid grid-cols-4 gap-[0.5ch] max-h-[24lh] overflow-y-auto">
            {screenshots.map((screenshot, index) => {
              const stepMatch = screenshot.path.match(/screenshot_(\d+)\.png/);
              const stepNumber = stepMatch ? stepMatch[1] : index + 1;
              const imageUrl = getArtifactUrl(screenshot.path);
              
              return (
                <div 
                  key={screenshot.path}
                  className="relative cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setSelectedImage(imageUrl)}
                >
                  <img
                    src={imageUrl}
                    alt={`Screenshot ${stepNumber}`}
                    className="w-full h-auto border border-gray-300 rounded"
                    loading="lazy"
                  />
                  <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs px-[0.25ch] py-[0.125lh] rounded-b">
                    Step {stepNumber}
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Modal for enlarged image */}
          {selectedImage && (
            <div 
              className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
              onClick={() => setSelectedImage(null)}
            >
              <div className="relative max-w-[100ch] max-h-full p-[1ch]">
                <img
                  src={selectedImage}
                  alt="Enlarged screenshot"
                  className="max-w-full max-h-full"
                />
                <button
                  onClick={() => setSelectedImage(null)}
                  className="absolute top-[0.5lh] right-[0.5ch] text-white bg-black bg-opacity-50 rounded-full w-[2ch] h-[2lh] flex items-center justify-center hover:bg-opacity-75"
                >
                  ×
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </BoxContainer>
  );
}