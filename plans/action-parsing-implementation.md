# Action Parsing Implementation Plan

## Overview

Implement robust action parsing for the Pokemon Red AI player while maintaining the existing `buttons(sequence='')` action format defined in `main.py:77`. The current placeholder action execution (`main.py:130`) needs to be replaced with proper parsing and execution of AI-generated actions.

## Current State Analysis

### Existing Action Format
- **Format**: `buttons(sequence='')` with space-separated button names
- **Valid Buttons**: 'a', 'b', 'start', 'select', 'up', 'down', 'left', 'right'
- **Examples**: 'a', 'up up a', 'left b', 'start down a'

### Current Implementation Gap
- AI responses contain structured `Thought: ... Action: ...` format
- Actions are added to history but not parsed or executed (`main.py:126`)
- Placeholder button press ('a') used instead of actual action execution (`main.py:130`)

## Implementation Strategy

### Phase 1: Action Parser Development

#### 1.1 Create Action Parser Class
**Location**: `open-llms-play-pokemon/action_parser.py`

**Core Components**:
- `ActionParser` class with regex-based parsing
- Support for both single and multi-step button sequences
- Robust error handling for malformed actions
- Validation against allowed button names

**Key Methods**:
- `parse_ai_response(response: str) -> ParsedAction`
- `validate_button_sequence(sequence: str) -> bool`
- `extract_action_from_response(response: str) -> str`

#### 1.2 Action Execution Engine
**Location**: Same file as ActionParser

**Features**:
- Execute button sequences with configurable timing
- Handle rapid sequences vs. individual button presses  
- Integration with PyBoy's button press and tick system
- Logging for debugging action execution

### Phase 2: Integration with Main Player

#### 2.1 Replace Placeholder Action Execution
**Location**: `open-llms-play-pokemon/main.py`

**Changes**:
- Import and instantiate ActionParser
- Replace `main.py:130` placeholder with parsed action execution
- Maintain existing action history format
- Add action execution logging

#### 2.2 Error Handling and Fallbacks
**Fallback Strategy**:
- If action parsing fails, log error and try again
- Implement retry logic for malformed responses
- Graceful degradation to ensure game continues running

### Phase 3: Testing and Validation

#### 3.1 Unit Tests for Action Parser
**Test Cases**:
- Valid single button actions: `buttons(sequence='a')`
- Valid multi-button sequences: `buttons(sequence='up up a')`
- Mixed valid sequences: `buttons(sequence='left b start')`
- Invalid button names and malformed syntax
- Edge cases: empty sequences, extra whitespace

## Technical Specifications

### Action Format Constraints
- **Button Names**: Must match exactly: 'a', 'b', 'start', 'select', 'up', 'down', 'left', 'right'
- **Sequence Parsing**: Space-separated button names within `buttons(sequence='...')`
- **Case Sensitivity**: Enforce lowercase button names for consistency
- **Whitespace Handling**: Trim and normalize whitespace in sequences

### PyBoy Integration Requirements
- **Button Press Duration**: Use PyBoy's default button press behavior
- **Inter-button Timing**: Configure tick count between sequential button presses
- **Render Control**: Maintain existing render behavior during action execution
- **State Preservation**: Ensure action execution doesn't interfere with game state management

### Error Recovery Mechanisms
- **Parse Failures**: Log error, skip action, continue game loop
- **Invalid Buttons**: Log warning, filter invalid buttons, execute valid ones
- **Empty Actions**: Treat as no-op, continue to next AI response
- **Timeout Protection**: Prevent infinite loops in action parsing

## Implementation Priorities

### High Priority (Core Functionality)
1. Basic action parsing for `buttons(sequence='...')` format
2. Integration with main game loop replacing placeholder execution
3. Essential error handling to prevent crashes

### Medium Priority (Robustness)
1. Comprehensive input validation and sanitization  
2. Detailed logging for debugging and monitoring
3. Unit tests for parser reliability

### Low Priority (Enhancements)
1. Performance optimizations for action parsing
2. Advanced error recovery strategies
3. Action execution analytics and metrics

## Dependencies and Constraints

### External Dependencies
- **PyBoy**: Existing button press and game state APIs
- **UI-TARS Model**: Response format consistency (structured Thought/Action)
- **OpenAI Client**: No changes required to AI integration

### Technical Constraints
- **Action Format**: Must maintain exact compatibility with existing format specification
- **Game Performance**: Action parsing must not impact 6x emulation speed
- **Memory Usage**: Parser should be lightweight and not accumulate excessive state

### Development Constraints  
- **Backward Compatibility**: Existing game state files and ROM loading must continue working
- **Code Organization**: New code should follow existing module structure
- **Testing Environment**: Must work with Modal-deployed LLM server setup