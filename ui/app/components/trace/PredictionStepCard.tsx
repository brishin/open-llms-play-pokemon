import { twMerge } from 'tailwind-merge';
import type { MLFlowSpan } from '~/mflow/MLFlowTraces';

interface PredictionOutput {
  next_thought: string;
  next_tool_name: 'press_buttons' | 'finish';
  next_tool_args: Record<string, any>;
}

function parsePredictionOutput(span: MLFlowSpan): PredictionOutput | null {
  try {
    const outputsAttr = span.attributes?.['mlflow.spanOutputs'];
    if (!outputsAttr) return null;

    const outputs = JSON.parse(outputsAttr);
    if (typeof outputs === 'object' && outputs.next_thought) {
      return outputs as PredictionOutput;
    }
    return null;
  } catch {
    return null;
  }
}

export function PredictionStepCard({
  span,
  stepNumber,
  isAfterCurrentStep,
  isCurrentStep,
}: {
  span: MLFlowSpan;
  stepNumber: number;
  isAfterCurrentStep: boolean;
  isCurrentStep: boolean;
}) {
  const prediction = parsePredictionOutput(span);
  const duration =
    span.end_time && span.start_time
      ? Math.round((span.end_time - span.start_time) / 1000000)
      : null;

  const PredictionStepContainer = ({ children }: { children: React.ReactNode }) => {
    return (
      <div
        className={twMerge(
          'border border-surface0 px-[1ch] py-[1lh]',
          isAfterCurrentStep && 'opacity-40',
          isCurrentStep && 'scroll-mt-[2lh]',
        )}
        id={`step-${stepNumber}`}
      >
        {children}
      </div>
    );
  };

  if (!prediction) {
    return (
      <PredictionStepContainer>
        <div className="text-subtext0">
          Step {stepNumber}: Unable to parse prediction data
        </div>
      </PredictionStepContainer>
    );
  }

  const formatToolAction = (toolName: string, toolArgs: Record<string, any>) => {
    if (toolName === 'finish') {
      return '✅ finish';
    }
    if (toolName === 'press_buttons' && toolArgs.sequence) {
      return `🎮 press_buttons: "${toolArgs.sequence}"`;
    }
    return `🔧 ${toolName}: ${JSON.stringify(toolArgs)}`;
  };

  return (
    <PredictionStepContainer>
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-text">Step {stepNumber}</h3>
        <div className="text-subtext0">
          {duration && `${duration}ms`}
          {span.status_code && ` • ${span.status_code}`}
        </div>
      </div>

      <div>
        <span className="font-bold">Thought: </span>
        <span className="text-text">{prediction.next_thought}</span>
      </div>

      <div>
        <span className="font-bold">Action: </span>
        <span className="font-mono">
          {formatToolAction(prediction.next_tool_name, prediction.next_tool_args)}
        </span>
      </div>
    </PredictionStepContainer>
  );
}
