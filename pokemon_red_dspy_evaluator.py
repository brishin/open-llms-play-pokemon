"""
Pokemon Red DSPy Evaluator

This module implements a comprehensive DSPy-based evaluator for Pokemon Red agents,
adapting metrics from the PWhiddy/PokemonRedExperiments research and using memory
symbols from pokered.sym for accurate game state assessment.

Based on research from:
- https://github.com/PWhiddy/PokemonRedExperiments/blob/master/v2/red_gym_env_v2.py
- Pokemon Red RL research papers showing key metrics like HP ratios, badges, levels, exploration

Key Pokemon Red Memory Addresses (from pokered.sym):
- 0xd158: wPlayerName
- 0xd163: wPartyCount  
- 0xd16b: wPartyMons (party Pokemon data)
- 0xd16c: wPartyMon1HP
- 0xd18c: wPartyMon1Level
- 0xd356: wObtainedBadges
- 0xd35e: wCurMap
- 0xd361: wYCoord
- 0xd362: wXCoord
- 0xcfe6: wEnemyMonHP  
- 0xd015: wBattleMonHP
- 0xd05a: wBattleType
"""

# Conditional dspy import
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    # Create a mock dspy module for when it's not available
    class MockDSpyEvaluate:
        def __init__(self, devset, metric, **kwargs):
            self.devset = devset
            self.metric = metric
            self.kwargs = kwargs
            print(f"Mock DSPy Evaluate created with {len(devset)} examples")
        
        def __call__(self, module):
            print("Mock evaluation - DSPy not available")
            return {"overall_score": 0.0}
    
    class MockDSpy:
        Evaluate = MockDSpyEvaluate
    
    dspy = MockDSpy()
    DSPY_AVAILABLE = False
    print("Warning: DSPy not available. Using mock implementation.")

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
import struct


class GameStateContext(Enum):
    """Different contexts in Pokemon Red for evaluation"""
    OVERWORLD = "overworld"
    BATTLE = "battle"
    MENU = "menu"
    DIALOGUE = "dialogue"


@dataclass
class PokemonRedGameState:
    """Represents the current state of Pokemon Red game"""
    
    # Core Game State
    player_name: str
    current_map: int
    player_x: int
    player_y: int
    
    # Party Information
    party_count: int
    party_pokemon_levels: List[int]
    party_pokemon_hp: List[tuple]  # [(current_hp, max_hp), ...]
    
    # Progress Metrics
    badges_obtained: int
    badges_binary: int  # Binary representation of badges
    
    # Battle State (when applicable)
    battle_type: int
    player_mon_hp: Optional[tuple] = None  # (current, max)
    enemy_mon_hp: Optional[tuple] = None   # (current, max)
    
    # Context
    context: GameStateContext = GameStateContext.OVERWORLD


@dataclass 
class PokemonRedExample:
    """Example for Pokemon Red evaluation"""
    
    initial_state: PokemonRedGameState
    final_state: PokemonRedGameState
    actions_taken: List[str]
    time_elapsed: float
    success_criteria: Dict[str, Any]


class PokemonRedMemoryReader:
    """Utility class to read Pokemon Red game state from memory/symbols"""
    
    # Memory addresses from pokered.sym
    MEMORY_ADDRESSES = {
        'player_name': 0xd158,
        'party_count': 0xd163,
        'party_mon_1_hp': 0xd16c,
        'party_mon_1_level': 0xd18c,
        'obtained_badges': 0xd356,
        'current_map': 0xd35e,
        'y_coord': 0xd361,
        'x_coord': 0xd362,
        'battle_mon_hp': 0xd015,
        'enemy_mon_hp': 0xcfe6,
        'battle_type': 0xd05a,
    }
    
    @staticmethod
    def parse_game_state(memory_data: Dict[str, Any]) -> PokemonRedGameState:
        """Parse raw memory data into structured game state"""
        
        # Extract basic info
        party_count = memory_data.get('party_count', 0)
        badges_binary = memory_data.get('obtained_badges', 0)
        badges_count = bin(badges_binary).count('1')
        
        # Parse party Pokemon data
        party_levels = []
        party_hp = []
        
        for i in range(min(party_count, 6)):  # Max 6 Pokemon
            level_key = f'party_mon_{i+1}_level'
            hp_key = f'party_mon_{i+1}_hp'
            max_hp_key = f'party_mon_{i+1}_max_hp'
            
            if level_key in memory_data:
                party_levels.append(memory_data[level_key])
            
            if hp_key in memory_data and max_hp_key in memory_data:
                party_hp.append((memory_data[hp_key], memory_data[max_hp_key]))
        
        # Determine context based on battle_type
        battle_type = memory_data.get('battle_type', 0)
        context = GameStateContext.BATTLE if battle_type > 0 else GameStateContext.OVERWORLD
        
        # Battle state
        player_mon_hp = None
        enemy_mon_hp = None
        
        if context == GameStateContext.BATTLE:
            if 'battle_mon_hp' in memory_data and 'battle_mon_max_hp' in memory_data:
                player_mon_hp = (memory_data['battle_mon_hp'], memory_data['battle_mon_max_hp'])
            
            if 'enemy_mon_hp' in memory_data and 'enemy_mon_max_hp' in memory_data:
                enemy_mon_hp = (memory_data['enemy_mon_hp'], memory_data['enemy_mon_max_hp'])
        
        return PokemonRedGameState(
            player_name=memory_data.get('player_name', ''),
            current_map=memory_data.get('current_map', 0),
            player_x=memory_data.get('x_coord', 0),
            player_y=memory_data.get('y_coord', 0),
            party_count=party_count,
            party_pokemon_levels=party_levels,
            party_pokemon_hp=party_hp,
            badges_obtained=badges_count,
            badges_binary=badges_binary,
            battle_type=battle_type,
            player_mon_hp=player_mon_hp,
            enemy_mon_hp=enemy_mon_hp,
            context=context
        )


class PokemonRedProgressMetrics:
    """Core metrics for evaluating Pokemon Red progress"""
    
    @staticmethod
    def calculate_exploration_score(initial_state: PokemonRedGameState, 
                                  final_state: PokemonRedGameState) -> float:
        """
        Calculate exploration progress score
        Based on map changes and coordinate movement
        """
        map_change_bonus = 100.0 if final_state.current_map != initial_state.current_map else 0.0
        
        # Distance moved (Manhattan distance)
        if final_state.current_map == initial_state.current_map:
            distance_moved = abs(final_state.player_x - initial_state.player_x) + \
                           abs(final_state.player_y - initial_state.player_y)
            movement_score = min(distance_moved * 2.0, 50.0)  # Cap at 50
        else:
            movement_score = 25.0  # Baseline for map change
        
        return map_change_bonus + movement_score
    
    @staticmethod
    def calculate_party_improvement_score(initial_state: PokemonRedGameState,
                                        final_state: PokemonRedGameState) -> float:
        """
        Calculate party improvement score
        Based on party size, level gains, and HP management
        """
        score = 0.0
        
        # Party size improvement
        party_size_gain = final_state.party_count - initial_state.party_count
        score += party_size_gain * 200.0  # Big bonus for catching Pokemon
        
        # Level improvements
        initial_levels = initial_state.party_pokemon_levels
        final_levels = final_state.party_pokemon_levels
        
        total_level_gain = 0
        for i in range(min(len(initial_levels), len(final_levels))):
            level_gain = final_levels[i] - initial_levels[i]
            total_level_gain += max(0, level_gain)
        
        score += total_level_gain * 25.0  # 25 points per level gained
        
        # HP management (penalty for fainting)
        if final_state.party_pokemon_hp:
            total_hp_ratio = sum(hp[0] / max(hp[1], 1) for hp in final_state.party_pokemon_hp) / len(final_state.party_pokemon_hp)
            score += total_hp_ratio * 50.0  # Bonus for keeping Pokemon healthy
        
        return score
    
    @staticmethod
    def calculate_badge_score(initial_state: PokemonRedGameState,
                            final_state: PokemonRedGameState) -> float:
        """
        Calculate badge acquisition score
        Badges are the primary objective markers in Pokemon Red
        """
        badges_gained = final_state.badges_obtained - initial_state.badges_obtained
        return badges_gained * 1000.0  # Very high reward for badges
    
    @staticmethod
    def calculate_battle_performance_score(state: PokemonRedGameState) -> float:
        """
        Calculate battle performance score
        Based on HP ratios during battle
        """
        if state.context != GameStateContext.BATTLE:
            return 0.0
        
        score = 0.0
        
        # Player Pokemon HP ratio
        if state.player_mon_hp:
            player_hp_ratio = state.player_mon_hp[0] / max(state.player_mon_hp[1], 1)
            score += player_hp_ratio * 100.0
        
        # Enemy Pokemon HP ratio (lower is better for player)
        if state.enemy_mon_hp:
            enemy_hp_ratio = state.enemy_mon_hp[0] / max(state.enemy_mon_hp[1], 1)
            score += (1.0 - enemy_hp_ratio) * 150.0  # Bonus for damaging enemy
        
        return score
    
    @staticmethod
    def calculate_efficiency_score(actions_taken: List[str], time_elapsed: float, 
                                 progress_score: float) -> float:
        """
        Calculate efficiency score based on progress per action/time
        """
        if len(actions_taken) == 0 or time_elapsed <= 0:
            return 0.0
        
        # Progress per action
        progress_per_action = progress_score / len(actions_taken)
        
        # Progress per time unit
        progress_per_time = progress_score / time_elapsed
        
        return (progress_per_action * 0.7 + progress_per_time * 0.3) * 10.0


def pokemon_red_comprehensive_metric(example: PokemonRedExample, 
                                   prediction: Any, 
                                   trace: Optional[Any] = None) -> float:
    """
    Comprehensive Pokemon Red evaluation metric
    
    Combines multiple aspects of Pokemon Red gameplay:
    - Exploration and map progression
    - Party development (catching, leveling)
    - Badge acquisition
    - Battle performance
    - Action efficiency
    
    Args:
        example: PokemonRedExample with initial/final states
        prediction: Agent's prediction/actions (can be various types)
        trace: Optional execution trace
        
    Returns:
        Float score representing overall performance
    """
    
    initial_state = example.initial_state
    final_state = example.final_state
    actions_taken = example.actions_taken
    time_elapsed = example.time_elapsed
    
    metrics = PokemonRedProgressMetrics()
    
    # Core progress metrics
    exploration_score = metrics.calculate_exploration_score(initial_state, final_state)
    party_score = metrics.calculate_party_improvement_score(initial_state, final_state)
    badge_score = metrics.calculate_badge_score(initial_state, final_state)
    
    # Context-specific metrics
    battle_score = 0.0
    if final_state.context == GameStateContext.BATTLE:
        battle_score = metrics.calculate_battle_performance_score(final_state)
    
    # Calculate total progress
    total_progress = exploration_score + party_score + badge_score + battle_score
    
    # Efficiency metric
    efficiency_score = metrics.calculate_efficiency_score(actions_taken, time_elapsed, total_progress)
    
    # Weighted final score
    final_score = (
        exploration_score * 0.20 +    # 20% weight to exploration
        party_score * 0.25 +          # 25% weight to party development  
        badge_score * 0.35 +          # 35% weight to badge acquisition
        battle_score * 0.10 +         # 10% weight to battle performance
        efficiency_score * 0.10       # 10% weight to efficiency
    )
    
    return max(0.0, final_score)  # Ensure non-negative


def pokemon_red_badge_focused_metric(example: PokemonRedExample, 
                                   prediction: Any, 
                                   trace: Optional[Any] = None) -> float:
    """
    Badge-focused evaluation metric for Pokemon Red
    
    Prioritizes badge acquisition as the primary success criterion,
    with secondary focus on party strength and exploration.
    """
    
    initial_state = example.initial_state
    final_state = example.final_state
    
    # Badge progression is primary
    badges_gained = final_state.badges_obtained - initial_state.badges_obtained
    if badges_gained > 0:
        return 1000.0 * badges_gained  # Very high reward for badge progress
    
    # Secondary metrics for badge preparation
    metrics = PokemonRedProgressMetrics()
    
    party_score = metrics.calculate_party_improvement_score(initial_state, final_state)
    exploration_score = metrics.calculate_exploration_score(initial_state, final_state)
    
    # Return weighted secondary score
    return (party_score * 0.6 + exploration_score * 0.4) * 0.1  # Reduced weight when no badge


def pokemon_red_exploration_metric(example: PokemonRedExample, 
                                 prediction: Any, 
                                 trace: Optional[Any] = None) -> float:
    """
    Exploration-focused evaluation metric for Pokemon Red
    
    Prioritizes map exploration and movement over other objectives.
    Useful for early game or when testing navigation capabilities.
    """
    
    initial_state = example.initial_state
    final_state = example.final_state
    
    metrics = PokemonRedProgressMetrics()
    exploration_score = metrics.calculate_exploration_score(initial_state, final_state)
    
    # Add bonus for reaching specific important maps
    important_maps = {
        1: 50,    # Pallet Town  
        2: 100,   # Viridian City
        3: 150,   # Pewter City
        4: 200,   # Cerulean City
        # Add more important locations
    }
    
    map_bonus = important_maps.get(final_state.current_map, 0)
    
    return exploration_score + map_bonus


def pokemon_red_battle_metric(example: PokemonRedExample, 
                            prediction: Any, 
                            trace: Optional[Any] = None) -> float:
    """
    Battle-focused evaluation metric for Pokemon Red
    
    Evaluates performance specifically during Pokemon battles.
    Returns 0 if not in battle context.
    """
    
    final_state = example.final_state
    
    if final_state.context != GameStateContext.BATTLE:
        return 0.0
    
    metrics = PokemonRedProgressMetrics()
    battle_score = metrics.calculate_battle_performance_score(final_state)
    
    # Add additional battle-specific bonuses
    if final_state.enemy_mon_hp and final_state.enemy_mon_hp[0] == 0:
        battle_score += 500.0  # Large bonus for defeating enemy Pokemon
    
    return battle_score


class PokemonRedEvaluator:
    """
    Main DSPy Evaluator for Pokemon Red agents
    
    Provides comprehensive evaluation capabilities using the adapted metrics
    from Pokemon Red experiments and game state symbols.
    """
    
    def __init__(self, 
                 metric_type: str = "comprehensive",
                 memory_reader: Optional[PokemonRedMemoryReader] = None):
        """
        Initialize the Pokemon Red evaluator
        
        Args:
            metric_type: Type of metric to use ('comprehensive', 'badge_focused', 
                        'exploration', 'battle')
            memory_reader: Optional custom memory reader for game state
        """
        self.metric_type = metric_type
        self.memory_reader = memory_reader or PokemonRedMemoryReader()
        self.logger = logging.getLogger(__name__)
        
        # Select appropriate metric function
        self.metric_functions = {
            "comprehensive": pokemon_red_comprehensive_metric,
            "badge_focused": pokemon_red_badge_focused_metric,
            "exploration": pokemon_red_exploration_metric,
            "battle": pokemon_red_battle_metric,
        }
        
        if metric_type not in self.metric_functions:
            raise ValueError(f"Unknown metric type: {metric_type}")
    
    def create_evaluator(self, examples: List[PokemonRedExample], 
                        **kwargs) -> dspy.Evaluate:
        """
        Create a DSPy Evaluate instance for Pokemon Red
        
        Args:
            examples: List of PokemonRedExample instances
            **kwargs: Additional arguments for dspy.Evaluate
            
        Returns:
            Configured dspy.Evaluate instance
        """
        
        metric_function = self.metric_functions[self.metric_type]
        
        # Default configuration optimized for Pokemon Red evaluation
        default_config = {
            'num_threads': 4,
            'display_progress': True,
            'display_table': 5,
            'max_errors': 3,
            'return_all_scores': True,
            'return_outputs': True,
        }
        
        # Update with user-provided config
        config = {**default_config, **kwargs}
        
        return dspy.Evaluate(
            devset=examples,
            metric=metric_function,
            **config
        )
    
    def evaluate_single(self, example: PokemonRedExample, 
                       prediction: Any = None) -> Dict[str, float]:
        """
        Evaluate a single Pokemon Red example
        
        Args:
            example: PokemonRedExample instance
            prediction: Agent prediction (optional)
            
        Returns:
            Dictionary with evaluation scores and breakdown
        """
        
        metric_function = self.metric_functions[self.metric_type]
        overall_score = metric_function(example, prediction)
        
        # Calculate individual component scores for analysis
        metrics = PokemonRedProgressMetrics()
        initial_state = example.initial_state
        final_state = example.final_state
        
        component_scores = {
            'overall_score': overall_score,
            'exploration_score': metrics.calculate_exploration_score(initial_state, final_state),
            'party_score': metrics.calculate_party_improvement_score(initial_state, final_state),
            'badge_score': metrics.calculate_badge_score(initial_state, final_state),
            'battle_score': metrics.calculate_battle_performance_score(final_state),
            'efficiency_score': metrics.calculate_efficiency_score(
                example.actions_taken, example.time_elapsed, overall_score),
        }
        
        return component_scores
    
    def create_benchmark_examples(self) -> List[PokemonRedExample]:
        """
        Create a set of benchmark examples for Pokemon Red evaluation
        
        Returns:
            List of standardized PokemonRedExample instances for testing
        """
        
        examples = []
        
        # Example 1: Early game exploration (Pallet Town to Viridian City)
        initial_state_1 = PokemonRedGameState(
            player_name="RED",
            current_map=1,  # Pallet Town
            player_x=10,
            player_y=10,
            party_count=1,
            party_pokemon_levels=[5],
            party_pokemon_hp=[(20, 20)],
            badges_obtained=0,
            badges_binary=0,
            battle_type=0,
        )
        
        final_state_1 = PokemonRedGameState(
            player_name="RED", 
            current_map=2,  # Viridian City
            player_x=15,
            player_y=20,
            party_count=1,
            party_pokemon_levels=[5],
            party_pokemon_hp=[(18, 20)],
            badges_obtained=0,
            badges_binary=0,
            battle_type=0,
        )
        
        examples.append(PokemonRedExample(
            initial_state=initial_state_1,
            final_state=final_state_1,
            actions_taken=["up", "up", "right", "a", "up", "up"],
            time_elapsed=30.0,
            success_criteria={"reached_new_map": True}
        ))
        
        # Example 2: Pokemon capture scenario
        initial_state_2 = PokemonRedGameState(
            player_name="RED",
            current_map=2,
            player_x=15,
            player_y=20,
            party_count=1,
            party_pokemon_levels=[6],
            party_pokemon_hp=[(22, 22)],
            badges_obtained=0,
            badges_binary=0,
            battle_type=0,
        )
        
        final_state_2 = PokemonRedGameState(
            player_name="RED",
            current_map=2,
            player_x=15,
            player_y=20,
            party_count=2,
            party_pokemon_levels=[6, 3],
            party_pokemon_hp=[(22, 22), (10, 10)],
            badges_obtained=0,
            badges_binary=0,
            battle_type=0,
        )
        
        examples.append(PokemonRedExample(
            initial_state=initial_state_2,
            final_state=final_state_2,
            actions_taken=["a", "down", "a", "a", "down", "a"],
            time_elapsed=60.0,
            success_criteria={"caught_pokemon": True}
        ))
        
        # Example 3: Badge acquisition scenario
        initial_state_3 = PokemonRedGameState(
            player_name="RED",
            current_map=3,  # Pewter City (Gym)
            player_x=10,
            player_y=10,
            party_count=2,
            party_pokemon_levels=[12, 8],
            party_pokemon_hp=[(35, 35), (25, 25)],
            badges_obtained=0,
            badges_binary=0,
            battle_type=1,  # Trainer battle
            player_mon_hp=(35, 35),
            enemy_mon_hp=(30, 30),
        )
        
        final_state_3 = PokemonRedGameState(
            player_name="RED",
            current_map=3,
            player_x=10,
            player_y=10,
            party_count=2,
            party_pokemon_levels=[13, 8],
            party_pokemon_hp=[(25, 38), (25, 25)],
            badges_obtained=1,
            badges_binary=1,  # First badge
            battle_type=0,
        )
        
        examples.append(PokemonRedExample(
            initial_state=initial_state_3,
            final_state=final_state_3,
            actions_taken=["a", "down", "a", "a", "down", "a", "a"],
            time_elapsed=120.0,
            success_criteria={"won_gym_battle": True, "earned_badge": True}
        ))
        
        return examples


# Usage example and testing functions
def demonstrate_pokemon_red_evaluator():
    """
    Demonstrate usage of the Pokemon Red DSPy Evaluator
    """
    
    print("Pokemon Red DSPy Evaluator Demonstration")
    print("=" * 50)
    
    # Create evaluator instances for different metric types
    evaluators = {
        "comprehensive": PokemonRedEvaluator("comprehensive"),
        "badge_focused": PokemonRedEvaluator("badge_focused"),
        "exploration": PokemonRedEvaluator("exploration"),
        "battle": PokemonRedEvaluator("battle"),
    }
    
    # Create benchmark examples
    examples = evaluators["comprehensive"].create_benchmark_examples()
    
    print(f"Created {len(examples)} benchmark examples")
    
    # Evaluate each example with different metrics
    for i, example in enumerate(examples):
        print(f"\nExample {i+1} Evaluation:")
        print(f"Initial State: Map {example.initial_state.current_map}, "
              f"Party: {example.initial_state.party_count}, "
              f"Badges: {example.initial_state.badges_obtained}")
        print(f"Final State: Map {example.final_state.current_map}, "
              f"Party: {example.final_state.party_count}, "
              f"Badges: {example.final_state.badges_obtained}")
        
        for metric_name, evaluator in evaluators.items():
            scores = evaluator.evaluate_single(example)
            print(f"  {metric_name}: {scores['overall_score']:.2f}")
    
    # Create DSPy Evaluate instance for comprehensive evaluation
    comprehensive_evaluator = evaluators["comprehensive"]
    dspy_evaluator = comprehensive_evaluator.create_evaluator(examples)
    
    print(f"\nCreated DSPy Evaluator with {len(examples)} examples")
    print("Ready for agent evaluation!")
    
    return dspy_evaluator, examples


if __name__ == "__main__":
    # Run demonstration
    evaluator, examples = demonstrate_pokemon_red_evaluator()
    print("\nPokemon Red DSPy Evaluator ready for use!")