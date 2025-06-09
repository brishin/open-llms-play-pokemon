"""
Integrated DSPy evaluation system for Pokemon Red gameplay.

This module integrates the DSPy metrics with the existing MLflow-based evaluation
system, providing a comprehensive evaluation framework that combines both
traditional metrics and DSPy-based assessments.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import dspy
import mlflow
import pandas as pd
from dspy.evaluate import Evaluate

from dspy_metrics import (
    GameplayExample,
    GameplayPrediction,
    gameplay_effectiveness_metric,
    ai_gameplay_assessment_metric,
    game_progress_metric,
    advanced_gameplay_metric,
    buttons_partial_match,
    create_pokemon_evaluator,
)
from main_dspy import PokemonRedDSPyAgent, GameState
from single_turn_evals import BoundingBoxEvaluator, EvalConfig


@dataclass
class DSPyEvaluationResult:
    """Extended evaluation result that includes DSPy metrics."""
    
    # Basic info
    example_id: str
    model_config: Dict[str, Any]
    
    # Predictions
    predicted_action: str
    predicted_buttons: List[str]
    predicted_reasoning: Optional[str]
    
    # Ground truth
    expected_action: Optional[str]
    expected_buttons: Optional[List[str]]
    
    # DSPy metric scores
    gameplay_effectiveness_score: float
    game_progress_score: float
    ai_assessment_score: float
    advanced_gameplay_score: float
    buttons_match_score: float
    
    # Overall scores
    dspy_composite_score: float
    success: bool
    
    # Metadata
    evaluation_time: float
    error: Optional[str] = None


class IntegratedPokemonEvaluator:
    """
    Integrated evaluator that combines DSPy metrics with existing evaluation infrastructure.
    
    This class extends the existing evaluation system to include DSPy-based metrics
    while maintaining compatibility with MLflow tracking and existing workflows.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.3,
        mlflow_tracking_uri: str = "http://localhost:8080",
        experiment_name: str = "pokemon_dspy_evaluation"
    ):
        """
        Initialize the integrated evaluator.
        
        Args:
            model_name: Name of the LLM to use
            temperature: Temperature for LLM generation
            mlflow_tracking_uri: MLflow tracking server URI
            experiment_name: Name of the MLflow experiment
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Setup DSPy
        self.lm = dspy.LM(
            model=model_name,
            temperature=temperature,
            max_tokens=2048
        )
        
        # Initialize agents
        self.dspy_agent = PokemonRedDSPyAgent()
        
        # Setup MLflow
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_gameplay_dataset_from_scenarios(self) -> List[GameplayExample]:
        """
        Create a comprehensive dataset of Pokemon Red gameplay scenarios.
        
        Returns:
            List of GameplayExample instances covering various game situations
        """
        scenarios = [
            # Starting scenarios
            {
                "screen_base64": "pallet_town_start",
                "context": "Game just started. Player is in Pallet Town, standing outside their house. Need to begin the Pokemon journey by visiting Professor Oak.",
                "expected_action": "Move up to Professor Oak's lab",
                "expected_buttons": ["up"],
                "game_progress_indicators": {
                    "current_location": "pallet_town",
                    "story_progress": "beginning",
                    "pokemon_count": 0,
                    "gym_badges": 0
                }
            },
            
            # Exploration scenarios
            {
                "screen_base64": "route1_exploration",
                "context": "Player is on Route 1, first route outside Pallet Town. This is where wild Pokemon can be encountered for the first time.",
                "expected_action": "Walk through tall grass to encounter wild Pokemon",
                "expected_buttons": ["up", "down"],
                "game_progress_indicators": {
                    "current_location": "route_1",
                    "pokemon_count": 1,
                    "has_pokeballs": True,
                    "wild_pokemon_available": True
                }
            },
            
            # Battle scenarios
            {
                "screen_base64": "wild_battle_start",
                "context": "A wild Pidgey appeared! Player has a level 5 Charmander with full health. This is a good opportunity to gain experience.",
                "expected_action": "Choose to battle the wild Pokemon",
                "expected_buttons": ["a"],
                "game_progress_indicators": {
                    "current_location": "battle",
                    "in_battle": True,
                    "pokemon_health": 1.0,
                    "opponent_pokemon": "pidgey",
                    "opponent_level": 3
                }
            },
            
            # Strategic scenarios
            {
                "screen_base64": "low_health_battle",
                "context": "Player's Pokemon has low health (5/25 HP) in battle against a wild Rattata. Need to make a strategic decision.",
                "expected_action": "Run from battle to preserve Pokemon health",
                "expected_buttons": ["down", "down", "a"],  # Navigate to Run option
                "game_progress_indicators": {
                    "current_location": "battle",
                    "in_battle": True,
                    "pokemon_health": 0.2,
                    "opponent_pokemon": "rattata",
                    "needs_healing": True
                }
            },
            
            # Healing scenarios
            {
                "screen_base64": "pokemon_center_entrance",
                "context": "Player is in Viridian City Pokemon Center with injured Pokemon. Nurse Joy can heal Pokemon for free.",
                "expected_action": "Talk to Nurse Joy to heal Pokemon",
                "expected_buttons": ["up", "a"],
                "game_progress_indicators": {
                    "current_location": "pokemon_center",
                    "pokemon_health": 0.3,
                    "needs_healing": True,
                    "at_healing_station": True
                }
            },
            
            # Shopping scenarios
            {
                "screen_base64": "pokemart_interior",
                "context": "Player is in a Pokemart with 500 Pokedollars. Running low on Pokeballs and Potions. Need to restock supplies.",
                "expected_action": "Buy Pokeballs and Potions",
                "expected_buttons": ["a", "up", "a"],  # Talk to clerk, select items
                "game_progress_indicators": {
                    "current_location": "pokemart",
                    "money": 500,
                    "pokeball_count": 2,
                    "potion_count": 1,
                    "needs_supplies": True
                }
            },
            
            # Gym challenge scenarios
            {
                "screen_base64": "pewter_gym_entrance",
                "context": "Player is at Pewter City Gym, ready to challenge Brock. Pokemon are healed and at good levels for the first gym.",
                "expected_action": "Enter the gym to challenge Brock",
                "expected_buttons": ["up", "a"],
                "game_progress_indicators": {
                    "current_location": "pewter_gym",
                    "pokemon_health": 1.0,
                    "pokemon_level": 12,
                    "gym_badges": 0,
                    "ready_for_gym": True
                }
            },
            
            # Navigation scenarios
            {
                "screen_base64": "viridian_forest_maze",
                "context": "Player is in Viridian Forest, a maze-like area with trainers and wild Pokemon. Need to find the exit to continue to Pewter City.",
                "expected_action": "Navigate through the forest paths",
                "expected_buttons": ["up", "right"],
                "game_progress_indicators": {
                    "current_location": "viridian_forest",
                    "in_maze": True,
                    "trainers_defeated": 2,
                    "items_found": 1
                }
            },
            
            # Trainer battle scenarios
            {
                "screen_base64": "trainer_battle_challenge",
                "context": "A Bug Catcher wants to battle! Player has type advantage with Charmander against Bug-type Pokemon.",
                "expected_action": "Accept the trainer battle",
                "expected_buttons": ["a"],
                "game_progress_indicators": {
                    "current_location": "route_2",
                    "trainer_battle_available": True,
                    "pokemon_health": 0.8,
                    "type_advantage": True
                }
            },
            
            # Item usage scenarios
            {
                "screen_base64": "battle_item_menu",
                "context": "In battle, Pokemon health is at 30%. Player has Super Potions in inventory. Strategic healing needed.",
                "expected_action": "Use Super Potion to heal Pokemon",
                "expected_buttons": ["down", "a", "up", "a"],  # Items -> Super Potion -> Use
                "game_progress_indicators": {
                    "current_location": "battle",
                    "in_battle": True,
                    "pokemon_health": 0.3,
                    "has_potions": True,
                    "strategic_healing_needed": True
                }
            }
        ]
        
        examples = []
        for i, scenario in enumerate(scenarios):
            example = GameplayExample(
                screen_base64=scenario["screen_base64"],
                context=scenario["context"],
                expected_action=scenario["expected_action"],
                expected_buttons=scenario["expected_buttons"],
                game_progress_indicators=scenario["game_progress_indicators"],
                success_criteria={"appropriate_action": True, "strategic_thinking": True}
            )
            examples.append(example)
        
        return examples
    
    def evaluate_single_scenario(
        self,
        example: GameplayExample,
        run_id: Optional[str] = None
    ) -> DSPyEvaluationResult:
        """
        Evaluate a single gameplay scenario using DSPy metrics.
        
        Args:
            example: GameplayExample to evaluate
            run_id: Optional MLflow run ID for tracking
            
        Returns:
            DSPyEvaluationResult with comprehensive metrics
        """
        import time
        start_time = time.time()
        
        try:
            with dspy.context(lm=self.lm):
                # Generate prediction using DSPy agent
                game_state = GameState(
                    screen_base64=example.screen_base64,
                    context=example.context
                )
                
                agent_output = self.dspy_agent.forward(game_state)
                
                # Convert to prediction format
                if hasattr(agent_output, 'action') and hasattr(agent_output, 'buttons'):
                    prediction = GameplayPrediction(
                        action=agent_output.action,
                        buttons=agent_output.buttons if isinstance(agent_output.buttons, list) else [agent_output.buttons],
                        reasoning=getattr(agent_output, 'reasoning', None),
                        confidence=getattr(agent_output, 'confidence', None)
                    )
                else:
                    # Fallback parsing
                    prediction = GameplayPrediction(
                        action=str(agent_output),
                        buttons=[],
                        reasoning=None,
                        confidence=None
                    )
                
                # Calculate DSPy metrics
                gameplay_score = gameplay_effectiveness_metric(example, prediction)
                progress_score = game_progress_metric(example, prediction)
                ai_assessment_score = ai_gameplay_assessment_metric(example, prediction)
                advanced_score = advanced_gameplay_metric(example, prediction)
                buttons_score = buttons_partial_match(example, prediction)
                
                # Calculate composite score
                weights = {
                    'gameplay': 0.3,
                    'progress': 0.25,
                    'ai_assessment': 0.25,
                    'advanced': 0.15,
                    'buttons': 0.05
                }
                
                composite_score = (
                    gameplay_score * weights['gameplay'] +
                    progress_score * weights['progress'] +
                    ai_assessment_score * weights['ai_assessment'] +
                    advanced_score * weights['advanced'] +
                    buttons_score * weights['buttons']
                )
                
                success = composite_score >= 0.7  # Threshold for success
                
                evaluation_time = time.time() - start_time
                
                result = DSPyEvaluationResult(
                    example_id=f"scenario_{hash(example.context) % 10000}",
                    model_config={
                        "model": self.model_name,
                        "temperature": self.temperature
                    },
                    predicted_action=prediction.action,
                    predicted_buttons=prediction.buttons,
                    predicted_reasoning=prediction.reasoning,
                    expected_action=example.expected_action,
                    expected_buttons=example.expected_buttons,
                    gameplay_effectiveness_score=gameplay_score,
                    game_progress_score=progress_score,
                    ai_assessment_score=ai_assessment_score,
                    advanced_gameplay_score=advanced_score,
                    buttons_match_score=buttons_score,
                    dspy_composite_score=composite_score,
                    success=success,
                    evaluation_time=evaluation_time
                )
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error evaluating scenario: {e}")
            evaluation_time = time.time() - start_time
            
            return DSPyEvaluationResult(
                example_id=f"scenario_{hash(example.context) % 10000}",
                model_config={"model": self.model_name, "temperature": self.temperature},
                predicted_action="ERROR",
                predicted_buttons=[],
                predicted_reasoning=None,
                expected_action=example.expected_action,
                expected_buttons=example.expected_buttons,
                gameplay_effectiveness_score=0.0,
                game_progress_score=0.0,
                ai_assessment_score=0.0,
                advanced_gameplay_score=0.0,
                buttons_match_score=0.0,
                dspy_composite_score=0.0,
                success=False,
                evaluation_time=evaluation_time,
                error=str(e)
            )
    
    def run_comprehensive_evaluation(
        self,
        dataset: Optional[List[GameplayExample]] = None,
        save_results: bool = True
    ) -> pd.DataFrame:
        """
        Run comprehensive evaluation using DSPy metrics with MLflow tracking.
        
        Args:
            dataset: Optional dataset to use (creates default if None)
            save_results: Whether to save results to files
            
        Returns:
            DataFrame with evaluation results
        """
        if dataset is None:
            dataset = self.create_gameplay_dataset_from_scenarios()
        
        self.logger.info(f"Starting comprehensive evaluation with {len(dataset)} scenarios")
        
        results = []
        
        with mlflow.start_run(run_name="dspy_comprehensive_evaluation"):
            # Log experiment parameters
            mlflow.log_param("model_name", self.model_name)
            mlflow.log_param("temperature", self.temperature)
            mlflow.log_param("num_scenarios", len(dataset))
            mlflow.log_param("evaluation_type", "dspy_comprehensive")
            
            # Evaluate each scenario
            for i, example in enumerate(dataset):
                self.logger.info(f"Evaluating scenario {i+1}/{len(dataset)}")
                
                with mlflow.start_run(nested=True, run_name=f"scenario_{i+1}"):
                    result = self.evaluate_single_scenario(example)
                    results.append(result)
                    
                    # Log individual results to MLflow
                    mlflow.log_param("scenario_context", example.context[:100] + "...")
                    mlflow.log_param("expected_action", example.expected_action)
                    mlflow.log_param("predicted_action", result.predicted_action)
                    
                    mlflow.log_metric("gameplay_effectiveness", result.gameplay_effectiveness_score)
                    mlflow.log_metric("game_progress", result.game_progress_score)
                    mlflow.log_metric("ai_assessment", result.ai_assessment_score)
                    mlflow.log_metric("advanced_gameplay", result.advanced_gameplay_score)
                    mlflow.log_metric("buttons_match", result.buttons_match_score)
                    mlflow.log_metric("composite_score", result.dspy_composite_score)
                    mlflow.log_metric("success", 1.0 if result.success else 0.0)
                    mlflow.log_metric("evaluation_time", result.evaluation_time)
                    
                    if result.error:
                        mlflow.log_param("error", result.error)
            
            # Calculate and log aggregate metrics
            df_results = pd.DataFrame([asdict(result) for result in results])
            
            # Aggregate metrics
            success_rate = df_results['success'].mean()
            avg_composite_score = df_results['dspy_composite_score'].mean()
            avg_gameplay_score = df_results['gameplay_effectiveness_score'].mean()
            avg_progress_score = df_results['game_progress_score'].mean()
            avg_ai_score = df_results['ai_assessment_score'].mean()
            avg_evaluation_time = df_results['evaluation_time'].mean()
            
            # Log aggregate metrics
            mlflow.log_metric("overall_success_rate", success_rate)
            mlflow.log_metric("avg_composite_score", avg_composite_score)
            mlflow.log_metric("avg_gameplay_effectiveness", avg_gameplay_score)
            mlflow.log_metric("avg_game_progress", avg_progress_score)
            mlflow.log_metric("avg_ai_assessment", avg_ai_score)
            mlflow.log_metric("avg_evaluation_time", avg_evaluation_time)
            
            # Log summary statistics
            summary_stats = {
                "total_scenarios": len(results),
                "successful_scenarios": sum(1 for r in results if r.success),
                "success_rate": success_rate,
                "average_scores": {
                    "composite": avg_composite_score,
                    "gameplay_effectiveness": avg_gameplay_score,
                    "game_progress": avg_progress_score,
                    "ai_assessment": avg_ai_score,
                    "buttons_match": df_results['buttons_match_score'].mean(),
                    "advanced_gameplay": df_results['advanced_gameplay_score'].mean()
                },
                "performance": {
                    "avg_evaluation_time": avg_evaluation_time,
                    "total_evaluation_time": df_results['evaluation_time'].sum()
                }
            }
            
            # Save detailed results
            if save_results:
                # Save as JSON
                with open("dspy_evaluation_results.json", "w") as f:
                    json.dump(summary_stats, f, indent=2)
                
                # Save as CSV
                df_results.to_csv("dspy_evaluation_detailed.csv", index=False)
                
                # Log files as artifacts
                mlflow.log_artifact("dspy_evaluation_results.json")
                mlflow.log_artifact("dspy_evaluation_detailed.csv")
            
            self.logger.info(f"Evaluation complete. Success rate: {success_rate:.3f}")
            
            return df_results
    
    def print_evaluation_summary(self, results_df: pd.DataFrame):
        """
        Print a comprehensive summary of evaluation results.
        
        Args:
            results_df: DataFrame with evaluation results
        """
        print("\n" + "="*80)
        print("POKEMON RED DSPY EVALUATION SUMMARY")
        print("="*80)
        
        # Basic statistics
        total_scenarios = len(results_df)
        successful_scenarios = results_df['success'].sum()
        success_rate = successful_scenarios / total_scenarios
        
        print(f"Total Scenarios Evaluated: {total_scenarios}")
        print(f"Successful Scenarios: {successful_scenarios}")
        print(f"Success Rate: {success_rate:.1%}")
        
        print("\n" + "-"*50)
        print("METRIC SCORES (Average)")
        print("-"*50)
        
        metrics = [
            ('Composite Score', 'dspy_composite_score'),
            ('Gameplay Effectiveness', 'gameplay_effectiveness_score'),
            ('Game Progress', 'game_progress_score'),
            ('AI Assessment', 'ai_assessment_score'),
            ('Advanced Gameplay', 'advanced_gameplay_score'),
            ('Button Matching', 'buttons_match_score')
        ]
        
        for metric_name, column_name in metrics:
            avg_score = results_df[column_name].mean()
            print(f"{metric_name:25}: {avg_score:.3f}")
        
        print("\n" + "-"*50)
        print("PERFORMANCE STATISTICS")
        print("-"*50)
        
        avg_time = results_df['evaluation_time'].mean()
        total_time = results_df['evaluation_time'].sum()
        
        print(f"Average Evaluation Time: {avg_time:.2f} seconds")
        print(f"Total Evaluation Time: {total_time:.2f} seconds")
        
        # Error analysis
        error_count = results_df['error'].notna().sum()
        if error_count > 0:
            print(f"Scenarios with Errors: {error_count}")
        
        print("\n" + "-"*50)
        print("TOP PERFORMING SCENARIOS")
        print("-"*50)
        
        top_scenarios = results_df.nlargest(3, 'dspy_composite_score')
        for i, (_, row) in enumerate(top_scenarios.iterrows(), 1):
            print(f"{i}. Score: {row['dspy_composite_score']:.3f}")
            print(f"   Action: {row['predicted_action'][:60]}...")
            print()


def main():
    """
    Main function demonstrating the integrated DSPy evaluation system.
    """
    print("Integrated DSPy Evaluation for Pokemon Red")
    print("="*60)
    
    # Initialize evaluator
    evaluator = IntegratedPokemonEvaluator(
        model_name="gpt-4o",
        temperature=0.3,
        experiment_name="pokemon_dspy_comprehensive"
    )
    
    # Run comprehensive evaluation
    print("Running comprehensive evaluation...")
    results_df = evaluator.run_comprehensive_evaluation()
    
    # Print summary
    evaluator.print_evaluation_summary(results_df)
    
    print("\n" + "="*60)
    print("Evaluation complete!")
    print("Results saved to:")
    print("- dspy_evaluation_results.json (summary)")
    print("- dspy_evaluation_detailed.csv (detailed results)")
    print("- MLflow tracking server (if running)")


if __name__ == "__main__":
    main()

