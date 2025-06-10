# Pokemon Red DSPy Evaluator

A comprehensive DSPy-based evaluator for Pokemon Red AI agents, adapting metrics from the [PWhiddy/PokemonRedExperiments](https://github.com/PWhiddy/PokemonRedExperiments) research and using memory symbols from `pokered.sym` for accurate game state assessment.

## Features

### 🎯 Multiple Evaluation Metrics

1. **Comprehensive Metric** - Weighted combination of all aspects:
   - Exploration and map progression (20%)
   - Party development (25%) 
   - Badge acquisition (35%)
   - Battle performance (10%)
   - Action efficiency (10%)

2. **Badge-Focused Metric** - Prioritizes gym badge acquisition (primary Pokemon Red objective)

3. **Exploration Metric** - Focuses on map exploration and navigation

4. **Battle Metric** - Evaluates combat performance during Pokemon battles

### 🧠 Adapted from Research

Based on metrics from Pokemon Red reinforcement learning research:
- HP ratios (player vs opponent)
- Level progression and party strength
- Badge collection (8 gym badges)
- Map exploration and position tracking
- Battle vs overworld context detection

### 🎮 Game State Tracking

Uses actual Pokemon Red memory addresses from `pokered.sym`:
- `0xd158`: Player Name
- `0xd163`: Party Count  
- `0xd16c`: Pokemon HP
- `0xd18c`: Pokemon Level
- `0xd356`: Badges Obtained
- `0xd35e`: Current Map
- `0xd361/d362`: Player X/Y Position
- `0xcfe6/d015`: Battle HP (Enemy/Player)

## Usage

### Basic Usage

```python
from pokemon_red_dspy_evaluator import PokemonRedEvaluator, PokemonRedExample, PokemonRedGameState

# Create evaluator
evaluator = PokemonRedEvaluator(metric_type="comprehensive")

# Create example with initial and final game states
initial_state = PokemonRedGameState(
    player_name="RED",
    current_map=1,  # Pallet Town
    player_x=10, player_y=10,
    party_count=1,
    party_pokemon_levels=[5],
    party_pokemon_hp=[(20, 20)],
    badges_obtained=0,
    badges_binary=0,
    battle_type=0
)

final_state = PokemonRedGameState(
    player_name="RED",
    current_map=2,  # Viridian City
    player_x=15, player_y=20,
    party_count=1, 
    party_pokemon_levels=[5],
    party_pokemon_hp=[(18, 20)],
    badges_obtained=0,
    badges_binary=0,
    battle_type=0
)

example = PokemonRedExample(
    initial_state=initial_state,
    final_state=final_state,
    actions_taken=["up", "up", "right", "a", "up", "up"],
    time_elapsed=30.0,
    success_criteria={"reached_new_map": True}
)

# Evaluate single example
scores = evaluator.evaluate_single(example)
print(f"Overall Score: {scores['overall_score']:.2f}")
```

### DSPy Integration

```python
# Create DSPy Evaluate instance for agent optimization
examples = evaluator.create_benchmark_examples()
dspy_evaluator = evaluator.create_evaluator(examples)

# Use with DSPy optimization (when dspy is available)
if DSPY_AVAILABLE:
    # Optimize your Pokemon Red agent
    optimized_agent = dspy.BootstrapFewShot().compile(
        student=your_pokemon_agent,
        trainset=examples,
        metric=evaluator.metric_functions["comprehensive"]
    )
```

### Different Metric Types

```python
# Badge-focused evaluation (prioritizes gym badge progress)
badge_evaluator = PokemonRedEvaluator("badge_focused")

# Exploration-focused evaluation (good for navigation testing)
exploration_evaluator = PokemonRedEvaluator("exploration")

# Battle-focused evaluation (for combat scenarios)
battle_evaluator = PokemonRedEvaluator("battle")
```

## Example Scores

The demonstration shows typical scores for different scenarios:

**Exploration Example** (Pallet Town → Viridian City):
- Comprehensive: 57.78
- Badge-focused: 7.70
- Exploration: 225.00 ⭐ (highest due to map change)
- Battle: 0.00

**Pokemon Capture Example**:
- Comprehensive: 92.92
- Badge-focused: 15.00
- Exploration: 100.00
- Battle: 0.00

**Badge Acquisition Example** (winning gym battle):
- Comprehensive: 475.92
- Badge-focused: 1000.00 ⭐ (highest due to badge earned)
- Exploration: 150.00
- Battle: 0.00

## Memory Address Integration

The evaluator uses actual Pokemon Red memory symbols for accurate game state reading:

```python
# Memory addresses from pokered.sym
MEMORY_ADDRESSES = {
    'player_name': 0xd158,
    'party_count': 0xd163,
    'obtained_badges': 0xd356,
    'current_map': 0xd35e,
    'x_coord': 0xd362,
    'y_coord': 0xd361,
    'battle_mon_hp': 0xd015,
    'enemy_mon_hp': 0xcfe6,
    'battle_type': 0xd05a,
}
```

## Installation Requirements

- Python 3.7+
- DSPy (optional - mock implementation available if not installed)

```bash
# Install DSPy for full functionality
pip install dspy

# The evaluator works without DSPy but with limited functionality
```

## Research Background

This evaluator adapts metrics from Pokemon Red reinforcement learning research, particularly:

- [PWhiddy/PokemonRedExperiments](https://github.com/PWhiddy/PokemonRedExperiments) - red_gym_env_v2.py
- Academic papers on Pokemon Red RL showing key success metrics
- Memory mapping from the Pokemon reverse engineering community

The metrics reflect the core challenges of Pokemon Red:
- **Long episode length** (25+ hours average human completion)
- **Multi-modal gameplay** (overworld exploration + turn-based battles)
- **Clear objective hierarchy** (badges > party strength > exploration)
- **Complex state space** (map position, party state, progress flags)

## Contributing

To extend the evaluator:

1. Add new metric functions following the signature: `(example, prediction, trace) -> float`
2. Include new metrics in `PokemonRedEvaluator.metric_functions`
3. Add corresponding memory addresses for new game state features
4. Create benchmark examples for new scenarios

The evaluator is designed to be modular and extensible for different aspects of Pokemon Red gameplay evaluation.