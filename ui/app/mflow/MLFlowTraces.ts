/**
 * TypeScript types for MLFlow traces and span artifact data
 */

export type MLFlowSpanStatus = 'OK' | 'ERROR' | 'CANCELLED';

export type MLFlowSpanType = 'AGENT' | 'LLM' | 'PARSER' | 'CHAT_MODEL' | 'TOOL';

export interface MLFlowSpanEvent {
  name: string;
  timestamp: number;
  attributes?: Record<string, unknown>;
}

export interface MLFlowSpanAttributes {
  [key: string]: string | number | boolean | null | undefined;
  'mlflow.traceRequestId'?: string;
  'mlflow.spanType'?: string;
  'mlflow.spanFunctionName'?: string;
  'mlflow.spanInputs'?: string;
  'mlflow.spanOutputs'?: string;
  'mlflow.chat.messages'?: string;
  signature?: string;
  temperature?: string | number;
  max_tokens?: string | number;
  api_base?: string;
  api_key?: string;
  model?: string;
  model_type?: string;
  cache?: string | boolean;
  name?: string;
  description?: string;
  args?: string;
}

export interface MLFlowSpan {
  name: string;
  context: {
    span_id: string;
    trace_id: string;
  };
  parent_id: string | null;
  start_time: number;
  end_time: number;
  status_code: MLFlowSpanStatus;
  status_message: string;
  attributes: MLFlowSpanAttributes;
  events: MLFlowSpanEvent[];
}

export interface MLFlowSpanArtifact {
  spans: MLFlowSpan[];
  request: string;
  response: string | null;
}

// Utility types for specific span types
export interface MLFlowAgentSpan extends MLFlowSpan {
  attributes: MLFlowSpanAttributes & {
    'mlflow.spanType': 'AGENT';
    'mlflow.spanFunctionName': string;
  };
}

export interface MLFlowLLMSpan extends MLFlowSpan {
  attributes: MLFlowSpanAttributes & {
    'mlflow.spanType': 'LLM';
    signature: string;
  };
}

export interface MLFlowChatModelSpan extends MLFlowSpan {
  attributes: MLFlowSpanAttributes & {
    'mlflow.spanType': 'CHAT_MODEL';
    temperature: string | number;
    max_tokens: string | number;
    model: string;
    model_type: 'chat';
  };
}

export interface MLFlowParserSpan extends MLFlowSpan {
  attributes: MLFlowSpanAttributes & {
    'mlflow.spanType': 'PARSER';
  };
}

export interface MLFlowToolSpan extends MLFlowSpan {
  attributes: MLFlowSpanAttributes & {
    'mlflow.spanType': 'TOOL';
    name: string;
    description: string;
    args: string;
  };
}

// Type guards for span types
export function isAgentSpan(span: MLFlowSpan): span is MLFlowAgentSpan {
  return span.attributes['mlflow.spanType'] === 'AGENT';
}

export function isLLMSpan(span: MLFlowSpan): span is MLFlowLLMSpan {
  return span.attributes['mlflow.spanType'] === 'LLM';
}

export function isChatModelSpan(span: MLFlowSpan): span is MLFlowChatModelSpan {
  return span.attributes['mlflow.spanType'] === 'CHAT_MODEL';
}

export function isParserSpan(span: MLFlowSpan): span is MLFlowParserSpan {
  return span.attributes['mlflow.spanType'] === 'PARSER';
}

export function isToolSpan(span: MLFlowSpan): span is MLFlowToolSpan {
  return span.attributes['mlflow.spanType'] === 'TOOL';
}

/**
 * A trace artifact contains the actual spans for a trace.
 */
export interface MLFlowTraceArtifact {
  spans: MLFlowSpan[];
}
