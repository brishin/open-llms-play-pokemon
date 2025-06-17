# DSPy Trace UI Implementation Plan

## Overview

This plan outlines the implementation of a TraceViewer component for displaying DSPy trace data within the Game State UI. The component will filter and display spans from MLflow traces, focusing on `Predict.forward_{X}` spans and their associated prediction data.

## Technical Background

### DSPy Trace Structure

Based on analysis of `ExampleTrace.json`, the trace data contains:

- **Root Structure**: `{ spans: [], request, response }`
- **Span Hierarchy**: Parent-child relationships via `parent_id` field
- **Span Types**: Identified by `mlflow.spanType` attribute
  - `AGENT`: Top-level operations (e.g., `start_game`)
  - `LLM`: DSPy predictions (e.g., `Predict.forward_1`)
  - `PARSER`: Format/parse operations (e.g., `ChatAdapter.format_1`)
  - `CHAT_MODEL`: LLM API calls (e.g., `LM.__call___1`)

### Key Span Name Pattern

Target spans follow the pattern: `Predict.forward_{X}` where X is the step count (1, 2, 3, etc.)

### Critical Data Fields

Within `Predict.forward_{X}` spans, the `mlflow.spanOutputs` contains JSON with:
- `next_thought`: AI reasoning about current situation
- `next_tool_name`: Selected tool (typically "press_buttons" or "finish")
- `next_tool_args`: Tool arguments (typically `{"sequence": "button_sequence"}`)

## Implementation Architecture

### Component Structure

```
TraceViewer
├── TraceSpanFilter (utility function)
├── PredictionStepCard (component)
├── ToolActionDisplay (component)
└── TraceHierarchyView (component)
```

### Data Flow

1. **Trace Loading**: MLFlowClient fetches trace data via `getTraces()` method
2. **Span Filtering**: Filter spans matching `Predict.forward_{X}` pattern
3. **Data Extraction**: Parse `mlflow.spanOutputs` JSON for prediction data
4. **UI Rendering**: Display filtered spans with key prediction fields

### Integration Points

- **Location**: Integrate into existing Game State UI in `routes/run.$runId.tsx`
- **Data Source**: Use existing MLFlowClient for trace fetching
- **Styling**: Follow existing UI patterns with BoxContainer and TailwindCSS

## Component Design Specifications

### TraceViewer Component

**Props Interface**:
```typescript
interface TraceViewerProps {
  runId: string;
  experimentId: string;
}
```

**Features**:
- Load trace data for specific run
- Filter `Predict.forward_{X}` spans
- Display prediction steps in chronological order
- Show hierarchical span relationships
- Handle loading/error states

### PredictionStepCard Component

**Props Interface**:
```typescript
interface PredictionStepCardProps {
  span: MLFlowSpan;
  stepNumber: number;
}
```

**Display Fields**:
- **Step Header**: "Prediction Step {X}" with timing info
- **Next Thought**: Display `next_thought` field prominently
- **Tool Action**: Merged display of `next_tool_name` and `next_tool_args`
- **Timing**: Show span duration and timestamp
- **Status**: Display span status (OK, ERROR, etc.)

### ToolActionDisplay Component

**Purpose**: Merge and format tool-related fields into single display

**Input Processing**:
- Extract `next_tool_name` and `next_tool_args` from span outputs
- Merge into readable format: `"press_buttons: right"` or `"finish"`
- Handle various tool argument structures

**Display Format**:
```
🎮 press_buttons: "right right a"
✅ finish
```

### TraceSpanFilter Utility

**Function Signature**:
```typescript
function filterPredictionSpans(spans: MLFlowSpan[]): MLFlowSpan[]
```

**Logic**:
1. Filter spans where `name` matches `/^Predict\.forward_\d+$/`
2. Sort by step number (extracted from name)
3. Validate span contains required output fields
4. Return ordered array of prediction spans

## Data Processing Requirements

### Span Output Parsing

The `mlflow.spanOutputs` field contains JSON strings that need parsing:

```typescript
interface PredictionOutput {
  next_thought: string;
  next_tool_name: "press_buttons" | "finish";
  next_tool_args: Record<string, any>;
}
```

### Error Handling

- **Invalid JSON**: Handle malformed `spanOutputs` gracefully
- **Missing Fields**: Provide defaults for missing prediction fields
- **Network Errors**: Show loading states and error messages
- **Empty Traces**: Handle runs without prediction spans

## UI Layout Integration

### Current Game State UI Structure

Based on `run.$runId.tsx`, the current layout includes:
- Left sidebar: TracesNav (run navigation)
- Main content: Grid with MetricsDisplay, ScreenshotGallery, GameDataViewer

### Proposed Integration

Add TraceViewer as a new section in the main content grid:

```typescript
<div className="flex flex-row gap-1 h-screen">
  <TracesNav runs={loaderData.runs} />
  <div className="flex flex-col gap-[0.25lh] grow overflow-y-auto">
    <MetricsDisplay run={loaderData.currentRun} />
    <div className="grid grid-cols-2 gap-[0.25lh] grow min-h-0">
      <ScreenshotGallery artifacts={screenshots} />
      <div className="flex flex-col gap-[0.25lh]">
        <GameDataViewer artifacts={gameStates} />
        <TraceViewer runId={params.runId} experimentId={loaderData.currentRun.info.experiment_id} />
      </div>
    </div>
  </div>
</div>
```

## Styling Guidelines

### Design Consistency

- **Container**: Use `BoxContainer` component with `title="DSPy Predictions"`
- **Typography**: Follow existing font weight patterns (no font-size changes)
- **Spacing**: Use `ch` units for horizontal, `lh` units for vertical spacing
- **Colors**: Follow Catppuccin theme via existing CSS classes

### Responsive Behavior

- **Overflow**: Handle long thought text with proper wrapping
- **Scrolling**: Enable vertical scroll for multiple prediction steps
- **Collapse**: Consider collapsible step cards for space efficiency

## Implementation Steps

### Phase 1: Core Component Structure
1. Create `TraceViewer.tsx` component with basic layout
2. Implement `filterPredictionSpans` utility function
3. Add basic span display with placeholder data
4. Integrate into Game State UI layout

### Phase 2: Data Integration
1. Enhance MLFlowClient with trace fetching if needed
2. Implement trace data loading in TraceViewer
3. Add span output JSON parsing
4. Handle loading and error states

### Phase 3: Enhanced Display
1. Create `PredictionStepCard` component
2. Implement `ToolActionDisplay` component
3. Add timing and status information
4. Polish styling and responsive behavior

### Phase 4: Testing and Refinement
1. Test with various trace data structures
2. Handle edge cases and error conditions
3. Optimize performance for large traces
4. Gather feedback and iterate

## Technical Considerations

### Performance

- **Lazy Loading**: Consider virtualizing large trace lists
- **Memoization**: Cache parsed span data to avoid re-processing
- **Debouncing**: Handle rapid component updates efficiently

### Accessibility

- **Keyboard Navigation**: Ensure step cards are keyboard accessible
- **Screen Readers**: Provide appropriate ARIA labels
- **Focus Management**: Handle focus states for collapsible content

### Data Validation

- **Type Safety**: Use TypeScript interfaces for all data structures
- **Runtime Validation**: Validate span data structure at runtime
- **Fallback Values**: Provide sensible defaults for missing data

## Future Enhancements

### Advanced Features

- **Search/Filter**: Search within thoughts or filter by tool type
- **Span Relationships**: Show parent-child span relationships visually
- **Performance Metrics**: Display span timing and performance data
- **Export Options**: Allow exporting trace data or screenshots

### Integration Opportunities

- **Screenshot Correlation**: Link prediction steps to corresponding screenshots
- **Game State Correlation**: Connect predictions to game state changes
- **Error Analysis**: Highlight failed predictions and error patterns

## Success Criteria

1. **Functional**: Successfully displays filtered `Predict.forward_{X}` spans
2. **Usable**: Clear presentation of `next_thought` and tool actions
3. **Integrated**: Seamlessly fits within existing Game State UI
4. **Performant**: Handles large traces without UI blocking
5. **Maintainable**: Clean, typed code following project conventions