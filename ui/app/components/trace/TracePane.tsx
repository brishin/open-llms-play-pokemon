import { useEffect, useMemo, useRef } from 'react';
import { BoxContainer } from '~/components/BoxContainer';
import type { MLFlowSpan, MLFlowTraceArtifact } from '~/mflow/MLFlowTraces';
import { PredictionStepCard } from './PredictionStepCard';

interface TracePaneProps {
  trace: MLFlowTraceArtifact | undefined;
  currentStep: number;
}

function filterPredictionSpans(spans: MLFlowSpan[]): MLFlowSpan[] {
  return spans
    .filter((span) => /^Predict\.forward_\d+$/.test(span.name))
    .sort((a, b) => {
      const stepA = Number.parseInt(a.name.match(/\d+$/)?.[0] || '0');
      const stepB = Number.parseInt(b.name.match(/\d+$/)?.[0] || '0');
      return stepA - stepB;
    });
}

export default function TracePane({ trace, currentStep }: TracePaneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const spans = useMemo(() => {
    if (!trace?.spans) return [];
    return filterPredictionSpans(trace.spans);
  }, [trace]);

  useEffect(() => {
    if (currentStep > 0 && containerRef.current) {
      const stepElement = containerRef.current.querySelector(`#step-${currentStep}`);
      if (stepElement) {
        stepElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [currentStep]);

  return (
    <BoxContainer title="Reasoning Traces" shear="top">
      <div ref={containerRef} className="max-h-[20lh] overflow-y-auto px-[1ch] pt-[1ch]">
        {!trace && (
          <div className="text-center text-subtext0 py-[2lh]">
            No trace data available for this run.
          </div>
        )}

        {trace && spans.length === 0 && (
          <div className="text-center text-subtext0 py-[2lh]">
            No DSPy prediction steps found in this run.
          </div>
        )}

        {spans.length > 0 && (
          <div className="space-y-[1lh]">
            {spans.map((span, index) => {
              const stepNumber = index + 1;
              const isAfterCurrentStep = stepNumber > currentStep;
              const isCurrentStep = stepNumber === currentStep;
              return (
                <PredictionStepCard
                  key={span.context?.span_id || index}
                  span={span}
                  stepNumber={stepNumber}
                  isAfterCurrentStep={isAfterCurrentStep}
                  isCurrentStep={isCurrentStep}
                />
              );
            })}
          </div>
        )}
      </div>
    </BoxContainer>
  );
}
