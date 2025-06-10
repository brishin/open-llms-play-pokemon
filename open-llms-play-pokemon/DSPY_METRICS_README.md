# DSPy Metrics for Pokemon Red Gameplay Evaluation

This implementation provides comprehensive DSPy-based metrics for evaluating AI agent performance in Pokemon Red gameplay scenarios. The metrics follow DSPy patterns and integrate with the existing evaluation infrastructure.

## Overview

The DSPy metrics implementation includes:

1. **Simple Metrics**: Basic exact match and partial match metrics
2. **Complex Multi-Criteria Metrics**: Composite metrics evaluating multiple aspects
3. **AI-Feedback Metrics**: Using LLMs to assess gameplay quality
4. **Progress-Based Metrics**: Evaluating game progression effectiveness
5. **Advanced DSPy Program Metrics**: Full DSPy modules for comprehensive evaluation
6. **Trace-Based Metrics**: Leveraging DSPy traces for optimization

## Files

- `dspy_metrics.py`: Core DSPy metrics implementation
- `dspy_evaluation_example.py`: Example usage and demonstration
- `integrated_dspy_evaluation.py`: Integration with existing MLflow evaluation system
- `DSPY_METRICS_README.md`: This documentation file

## Quick Start

### Basic Usage

```python
from dspy_metrics import (
    GameplayExample, 
    GameplayPrediction,
    gameplay_effectiveness_metric,
    create_pokemon_evaluator
)

# Create example data
example = GameplayExample(
    screen_base64="dummy_base64_data",
    context="Player is in Pallet Town and needs to visit Professor Oak's lab",
    expected_action="Move up to enter Professor Oak's lab",
    expected_buttons=["up", "a"]
)

prediction = GameplayPrediction(
    action="Move up to enter the lab and talk to Professor Oak",
    buttons=["up", "a"],
    reasoning="Need to meet Professor Oak to start Pokemon journey"
)

# Evaluate using metrics
score = gameplay_effectiveness_metric(example, prediction)
print(f"Gameplay effectiveness: {score:.3f}")
```

### Running Comprehensive Evaluation

```python
from dspy_evaluation_example import PokemonGameplayEvaluator

# Initialize evaluator
evaluator = PokemonGameplayEvaluator(
    model_name="gpt-4o",
    temperature=0.3
)

# Run comprehensive evaluation
results = evaluator.run_comprehensive_evaluation()
```

### Integrated Evaluation with MLflow

```python
from integrated_dspy_evaluation import IntegratedPokemonEvaluator

# Initialize integrated evaluator
evaluator = IntegratedPokemonEvaluator(
    model_name="gpt-4o",
    temperature=0.3,
    experiment_name="pokemon_dspy_evaluation"
)

# Run evaluation with MLflow tracking
results_df = evaluator.run_comprehensive_evaluation()
```

## Available Metrics

### 1. Simple Metrics

#### `action_exact_match(example, pred, trace=None)`
- **Purpose**: Exact string matching for predicted actions
- **Returns**: `bool` - True if actions match exactly
- **Use Case**: Basic validation of action prediction accuracy

#### `buttons_exact_match(example, pred, trace=None)`
- **Purpose**: Exact sequence matching for button inputs
- **Returns**: `bool` - True if button sequences match exactly
- **Use Case**: Validating precise input sequences

#### `buttons_partial_match(example, pred, trace=None)`
- **Purpose**: Partial matching allowing some flexibility in button sequences
- **Returns**: `float` (0.0-1.0) - Ratio of matching buttons
- **Use Case**: More forgiving evaluation of button sequences

### 2. Complex Multi-Criteria Metrics

#### `gameplay_effectiveness_metric(example, pred, trace=None)`
- **Purpose**: Evaluates multiple aspects of gameplay effectiveness
- **Criteria**:
  - Button validity (valid GameBoy buttons)
  - Action relevance (Pokemon-related terms)
  - Reasoning quality (substantial explanation)
  - Sequence length appropriateness
- **Returns**: `float` (0.0-1.0) for evaluation, `bool` for optimization
- **Use Case**: Comprehensive gameplay quality assessment

### 3. AI-Feedback Metrics

#### `ai_gameplay_assessment_metric(example, pred, trace=None)`
- **Purpose**: Uses AI feedback to assess gameplay decisions
- **Assessment Questions**:
  - Action appropriateness for context
  - Button validity and effectiveness
  - Strategic thinking quality
- **Returns**: `float` (0.0-1.0) - AI assessment score
- **Use Case**: Leveraging LLM judgment for nuanced evaluation

### 4. Progress-Based Metrics

#### `game_progress_metric(example, pred, trace=None)`
- **Purpose**: Evaluates likelihood of advancing game progress
- **Considers**:
  - Location-appropriate actions
  - Health-based decisions
  - Inventory management
  - Strategic progression
- **Returns**: `float` (0.0-1.0) - Progress likelihood score
- **Use Case**: Measuring strategic game advancement

### 5. Advanced DSPy Program Metrics

#### `advanced_gameplay_metric(example, pred, trace=None)`
- **Purpose**: Uses a full DSPy module for comprehensive validation
- **Components**:
  - Strategic assessment using Chain-of-Thought
  - Technical validation
  - Composite scoring
- **Returns**: `float` (0.0-1.0) - Comprehensive validation score
- **Use Case**: Most sophisticated evaluation using DSPy capabilities

### 6. Trace-Based Metrics

#### `validate_reasoning_steps(example, pred, trace=None)`
- **Purpose**: Validates intermediate reasoning steps using trace information
- **Requirements**: Only works during optimization (requires trace)
- **Validation**:
  - Pokemon concept mentions
  - Reasoning step quality
  - Logical progression
- **Returns**: `bool` - Whether reasoning steps are valid
- **Use Case**: Optimization and fine-tuning of reasoning processes

## Data Structures

### GameplayExample
```python
@dataclass
class GameplayExample:
    screen_base64: str                              # Base64 encoded game screen
    context: str                                    # Current game situation
    expected_action: Optional[str] = None           # Expected action description
    expected_buttons: Optional[List[str]] = None    # Expected button sequence
    game_progress_indicators: Optional[Dict] = None # Progress state info
    success_criteria: Optional[Dict] = None         # Success conditions
```

### GameplayPrediction
```python
@dataclass
class GameplayPrediction:
    action: str                           # Predicted action description
    buttons: List[str]                    # Predicted button sequence
    reasoning: Optional[str] = None       # Reasoning explanation
    confidence: Optional[float] = None    # Confidence score
```

## Integration with Existing System

The DSPy metrics integrate seamlessly with the existing evaluation infrastructure:

### MLflow Integration
- All metrics are tracked in MLflow experiments
- Individual and aggregate metrics are logged
- Results are saved as artifacts
- Compatible with existing MLflow workflows

### Existing Evaluation System
- Extends `BoundingBoxEvaluator` patterns
- Maintains compatibility with `EvalConfig`
- Integrates with existing result formats
- Preserves MLflow tracking capabilities

## Example Scenarios

The implementation includes comprehensive test scenarios covering:

1. **Starting Scenarios**: Beginning the Pokemon journey
2. **Exploration**: Route navigation and wild Pokemon encounters
3. **Battle Scenarios**: Combat decisions and strategy
4. **Strategic Decisions**: Health management and resource allocation
5. **Healing**: Pokemon Center interactions
6. **Shopping**: Item purchasing and inventory management
7. **Gym Challenges**: Gym leader battles
8. **Navigation**: Complex area traversal
9. **Trainer Battles**: NPC trainer encounters
10. **Item Usage**: Strategic item deployment

## Running the Examples

### Simple Example
```bash
cd open-llms-play-pokemon
python dspy_evaluation_example.py
```

### Comprehensive Evaluation
```bash
cd open-llms-play-pokemon
python integrated_dspy_evaluation.py
```

### Custom Evaluation
```python
from dspy_metrics import create_pokemon_evaluator

# Create custom dataset
dataset = [...]  # Your GameplayExample instances

# Create evaluator with specific metric
evaluator = create_pokemon_evaluator(
    devset=dataset,
    metric_name="gameplay_effectiveness",
    display_progress=True
)

# Evaluate your DSPy program
score = evaluator(your_dspy_program)
```

## Configuration

### Model Configuration
```python
# Configure DSPy LLM
lm = dspy.LM(
    model="gpt-4o",           # or other supported models
    temperature=0.3,          # adjust for creativity vs consistency
    max_tokens=2048          # sufficient for gameplay reasoning
)

# Use in context
with dspy.context(lm=lm):
    # Run evaluations
    pass
```

### Metric Selection
```python
# Available metrics for create_pokemon_evaluator
metrics = [
    "action_exact_match",
    "buttons_exact_match", 
    "buttons_partial_match",
    "gameplay_effectiveness",
    "ai_assessment",
    "game_progress",
    "advanced_gameplay",
    "reasoning_validation"
]
```

## Best Practices

### 1. Metric Selection
- Use **simple metrics** for basic validation
- Use **gameplay_effectiveness** for general evaluation
- Use **ai_assessment** for nuanced judgment
- Use **game_progress** for strategic evaluation
- Use **advanced_gameplay** for comprehensive assessment

### 2. Dataset Creation
- Include diverse gameplay scenarios
- Provide clear expected outcomes
- Include relevant progress indicators
- Cover edge cases and strategic decisions

### 3. Evaluation Strategy
- Start with simple metrics for debugging
- Use multiple metrics for comprehensive evaluation
- Monitor both individual and aggregate scores
- Track evaluation performance and timing

### 4. Optimization
- Use trace-based metrics during compilation
- Leverage DSPy's optimization capabilities
- Iterate on metric definitions based on results
- Balance strictness with practical utility

## Troubleshooting

### Common Issues

1. **LLM API Errors**: Ensure proper API keys and model access
2. **Trace Errors**: Some metrics require trace=None for evaluation
3. **Data Format**: Ensure GameplayExample and GameplayPrediction formats
4. **MLflow Connection**: Verify MLflow server is running for integrated evaluation

### Performance Considerations

- AI-feedback metrics are slower due to LLM calls
- Batch evaluation is more efficient than individual calls
- Consider caching for repeated evaluations
- Monitor token usage for cost management

## Extension Points

The metrics system is designed for extension:

1. **Custom Metrics**: Add domain-specific evaluation criteria
2. **New Data Sources**: Integrate with different game states
3. **Advanced DSPy Programs**: Create more sophisticated evaluation modules
4. **Integration**: Connect with other evaluation frameworks

## Contributing

When adding new metrics:

1. Follow the DSPy metric signature: `metric(example, pred, trace=None)`
2. Return appropriate types based on trace parameter
3. Include comprehensive docstrings
4. Add test cases and examples
5. Update this documentation

## References

- [DSPy Metrics Documentation](https://dspy.ai/learn/evaluation/metrics/)
- [DSPy Framework](https://github.com/stanfordnlp/dspy)
- [Pokemon Red Experiments](https://github.com/PWhiddy/PokemonRedExperiments)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

