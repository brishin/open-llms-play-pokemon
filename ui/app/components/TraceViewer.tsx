import { useMemo } from 'react';
import { BoxContainer } from '~/components/BoxContainer';
import type { MLFlowSpan, MLFlowTraceArtifact } from '~/mflow/MLFlowTraces';

interface TraceViewerProps {
  trace: MLFlowTraceArtifact | undefined;
}

interface PredictionOutput {
  next_thought: string;
  next_tool_name: 'press_buttons' | 'finish';
  next_tool_args: Record<string, any>;
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

function PredictionStepCard({
  span,
  stepNumber,
}: { span: MLFlowSpan; stepNumber: number }) {
  const prediction = parsePredictionOutput(span);
  const duration =
    span.end_time && span.start_time
      ? Math.round((span.end_time - span.start_time) / 1000000)
      : null;

  if (!prediction) {
    return (
      <div className="border border-surface0 rounded p-[1ch] mb-[0.5lh]">
        <div className="text-subtext0 text-sm">
          Step {stepNumber}: Unable to parse prediction data
        </div>
      </div>
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
    <div className="border border-surface0 rounded p-[1ch] mb-[0.5lh]">
      <div className="flex justify-between items-center mb-[0.5lh]">
        <h3 className="font-semibold text-text">Step {stepNumber}</h3>
        <div className="text-subtext0">
          {duration && `${duration}ms`}
          {span.status_code && ` • ${span.status_code}`}
        </div>
      </div>

      <div className="mb-[0.5lh]">
        <div className="font-medium text-subtext1 mb-[0.25lh]">Thought:</div>
        <div className="text-text">{prediction.next_thought}</div>
      </div>

      <div>
        <div className="font-medium text-subtext1 mb-[0.25lh]">Action:</div>
        <div className="font-mono text-text">
          {formatToolAction(prediction.next_tool_name, prediction.next_tool_args)}
        </div>
      </div>
    </div>
  );
}

export default function TraceViewer({ trace }: TraceViewerProps) {
  const spans = useMemo(() => {
    if (!trace?.spans) return [];
    return filterPredictionSpans(trace.spans);
  }, [trace]);

  return (
    <BoxContainer title="DSPy Predictions">
      <div className="max-h-[20lh] overflow-y-auto">
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
          <div className="space-y-[0.5lh]">
            {spans.map((span, index) => (
              <PredictionStepCard
                key={span.context?.span_id || index}
                span={span}
                stepNumber={index + 1}
              />
            ))}
          </div>
        )}
      </div>
    </BoxContainer>
  );
}
