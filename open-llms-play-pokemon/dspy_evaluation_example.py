"""
Example script demonstrating DSPy metrics usage for Pokemon Red gameplay evaluation.

This script shows how to integrate the DSPy metrics with the existing Pokemon Red
gameplay system and run comprehensive evaluations.
"""

import base64
import json
from pathlib import Path
from typing import List, Dict, Any

import dspy
from dspy.evaluate import Evaluate

from dspy_metrics import (
    GameplayExample,
    GameplayPrediction,
    create_pokemon_evaluator,
    run_comprehensive_evaluation,
    gameplay_effectiveness_metric,
    ai_gameplay_assessment_metric,
    game_progress_metric,
    advanced_gameplay_metric,
)
from main_dspy import PokemonRedDSPyAgent, GameState


class PokemonGameplayEvaluator:
    """
    Comprehensive evaluator for Pokemon Red gameplay using DSPy metrics.
    
    This class integrates the DSPy metrics with the existing Pokemon Red
    gameplay system to provide thorough evaluation capabilities.
    """
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.3):
        """
        Initialize the evaluator.
        
        Args:
            model_name: Name of the LLM to use
            temperature: Temperature for LLM generation
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Setup DSPy LLM
        self.lm = dspy.LM(
            model=model_name,
            temperature=temperature,
            max_tokens=2048
        )
        
        # Initialize the Pokemon Red agent
        self.agent = PokemonRedDSPyAgent()
    
    def create_sample_dataset(self) -> List[GameplayExample]:
        """
        Create a sample dataset for evaluation.
        
        In a real scenario, this would load actual gameplay data.
        
        Returns:
            List of GameplayExample instances
        """
        examples = [
            GameplayExample(
                screen_base64="dummy_pallet_town_base64",
                context="Player is in Pallet Town at the start of the game. Need to visit Professor Oak's lab to begin the Pokemon journey.",
                expected_action="Move up to enter Professor Oak's lab",
                expected_buttons=["up", "a"],
                game_progress_indicators={
                    "current_location": "pallet_town",
                    "pokemon_health": 1.0,
                    "has_pokeballs": False,
                    "story_progress": "beginning"
                },
                success_criteria={
                    "enters_lab": True,
                    "talks_to_oak": True
                }
            ),
            GameplayExample(
                screen_base64="dummy_route1_base64",
                context="Player is on Route 1 with a wild Pidgey appearing. Player has Pokeballs and a healthy starter Pokemon.",
                expected_action="Engage in battle with the wild Pidgey to gain experience",
                expected_buttons=["a"],
                game_progress_indicators={
                    "current_location": "route_1",
                    "pokemon_health": 0.8,
                    "has_pokeballs": True,
                    "wild_pokemon_present": True
                },
                success_criteria={
                    "engages_battle": True,
                    "makes_strategic_choice": True
                }
            ),
            GameplayExample(
                screen_base64="dummy_pokemon_center_base64",
                context="Player is in a Pokemon Center with injured Pokemon. Need to heal Pokemon before continuing journey.",
                expected_action="Talk to Nurse Joy to heal Pokemon",
                expected_buttons=["up", "a"],
                game_progress_indicators={
                    "current_location": "pokemon_center",
                    "pokemon_health": 0.2,
                    "has_pokeballs": True,
                    "needs_healing": True
                },
                success_criteria={
                    "talks_to_nurse": True,
                    "heals_pokemon": True
                }
            ),
            GameplayExample(
                screen_base64="dummy_battle_base64",
                context="Player is in battle against a wild Pokemon. Player's Pokemon has low health but the wild Pokemon is also weak.",
                expected_action="Use a Pokeball to attempt to catch the weakened Pokemon",
                expected_buttons=["down", "a"],  # Navigate to items, select Pokeball
                game_progress_indicators={
                    "current_location": "battle",
                    "pokemon_health": 0.3,
                    "opponent_health": 0.2,
                    "has_pokeballs": True,
                    "in_battle": True
                },
                success_criteria={
                    "uses_pokeball": True,
                    "strategic_timing": True
                }
            ),
            GameplayExample(
                screen_base64="dummy_gym_base64",
                context="Player is outside Pewter City Gym, ready to challenge Brock for the first gym badge.",
                expected_action="Enter the gym to challenge the gym leader",
                expected_buttons=["up", "a"],
                game_progress_indicators={
                    "current_location": "pewter_gym",
                    "pokemon_health": 1.0,
                    "has_pokeballs": True,
                    "gym_badges": 0,
                    "ready_for_gym": True
                },
                success_criteria={
                    "enters_gym": True,
                    "prepared_for_battle": True
                }
            )
        ]
        
        return examples
    
    def convert_agent_output_to_prediction(self, agent_output) -> GameplayPrediction:
        """
        Convert the agent's output to a GameplayPrediction format.
        
        Args:
            agent_output: Output from the PokemonRedDSPyAgent
            
        Returns:
            GameplayPrediction instance
        """
        if hasattr(agent_output, 'action') and hasattr(agent_output, 'buttons'):
            return GameplayPrediction(
                action=agent_output.action,
                buttons=agent_output.buttons if isinstance(agent_output.buttons, list) else [agent_output.buttons],
                reasoning=getattr(agent_output, 'reasoning', None),
                confidence=getattr(agent_output, 'confidence', None)
            )
        else:
            # Fallback for different output formats
            return GameplayPrediction(
                action=str(agent_output),
                buttons=[],
                reasoning=None,
                confidence=None
            )
    
    def evaluate_agent_on_dataset(
        self, 
        dataset: List[GameplayExample],
        metrics: List[str] = None
    ) -> Dict[str, float]:
        """
        Evaluate the Pokemon Red agent on a dataset using multiple metrics.
        
        Args:
            dataset: List of GameplayExample instances
            metrics: List of metric names to use
            
        Returns:
            Dictionary mapping metric names to scores
        """
        if metrics is None:
            metrics = [
                "gameplay_effectiveness",
                "game_progress", 
                "ai_assessment"
            ]
        
        print(f"Evaluating agent with {len(dataset)} examples using metrics: {metrics}")
        
        # Set up DSPy context
        with dspy.context(lm=self.lm):
            results = {}
            
            for metric_name in metrics:
                print(f"\nEvaluating with {metric_name}...")
                
                try:
                    evaluator = create_pokemon_evaluator(
                        devset=dataset,
                        metric_name=metric_name,
                        display_progress=True,
                        display_table=3
                    )
                    
                    # Create a wrapper function for the agent
                    def agent_wrapper(example):
                        game_state = GameState(
                            screen_base64=example.screen_base64,
                            context=example.context
                        )
                        agent_output = self.agent.forward(game_state)
                        return self.convert_agent_output_to_prediction(agent_output)
                    
                    score = evaluator(agent_wrapper)
                    results[metric_name] = score
                    print(f"{metric_name} score: {score:.3f}")
                    
                except Exception as e:
                    print(f"Error evaluating {metric_name}: {e}")
                    results[metric_name] = 0.0
        
        return results
    
    def run_single_evaluation_example(self):
        """
        Run a single evaluation example to demonstrate the metrics.
        """
        print("Running single evaluation example...")
        
        # Create a sample example
        example = GameplayExample(
            screen_base64="dummy_base64_data",
            context="Player is in Pallet Town and needs to visit Professor Oak's lab to start their Pokemon journey.",
            expected_action="Move up to enter Professor Oak's lab",
            expected_buttons=["up", "a"],
            game_progress_indicators={
                "current_location": "pallet_town",
                "pokemon_health": 1.0,
                "has_pokeballs": False
            }
        )
        
        # Create a sample prediction (simulating agent output)
        prediction = GameplayPrediction(
            action="Move up to enter the lab and talk to Professor Oak",
            buttons=["up", "a"],
            reasoning="The player needs to meet Professor Oak to start their Pokemon journey. Moving up will enter the lab, and pressing 'a' will interact with NPCs inside.",
            confidence=0.9
        )
        
        print(f"Example context: {example.context}")
        print(f"Expected action: {example.expected_action}")
        print(f"Expected buttons: {example.expected_buttons}")
        print(f"Predicted action: {prediction.action}")
        print(f"Predicted buttons: {prediction.buttons}")
        print(f"Reasoning: {prediction.reasoning}")
        
        # Test different metrics
        print("\nMetric Results:")
        print(f"Gameplay Effectiveness: {gameplay_effectiveness_metric(example, prediction):.3f}")
        print(f"Game Progress: {game_progress_metric(example, prediction):.3f}")
        
        # Test AI assessment (requires LLM)
        with dspy.context(lm=self.lm):
            try:
                ai_score = ai_gameplay_assessment_metric(example, prediction)
                print(f"AI Assessment: {ai_score:.3f}")
            except Exception as e:
                print(f"AI Assessment failed: {e}")
        
        print(f"Advanced Gameplay: {advanced_gameplay_metric(example, prediction):.3f}")
    
    def run_comprehensive_evaluation(self):
        """
        Run a comprehensive evaluation using the sample dataset.
        """
        print("Running comprehensive evaluation...")
        
        # Create sample dataset
        dataset = self.create_sample_dataset()
        print(f"Created dataset with {len(dataset)} examples")
        
        # Run evaluation
        results = self.evaluate_agent_on_dataset(dataset)
        
        print("\n" + "="*50)
        print("COMPREHENSIVE EVALUATION RESULTS")
        print("="*50)
        
        for metric_name, score in results.items():
            print(f"{metric_name:25}: {score:.3f}")
        
        # Calculate overall score
        overall_score = sum(results.values()) / len(results) if results else 0.0
        print(f"{'Overall Score':25}: {overall_score:.3f}")
        
        return results
    
    def save_evaluation_results(self, results: Dict[str, float], filepath: str = "evaluation_results.json"):
        """
        Save evaluation results to a JSON file.
        
        Args:
            results: Dictionary of evaluation results
            filepath: Path to save the results
        """
        evaluation_data = {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "metrics": results,
            "overall_score": sum(results.values()) / len(results) if results else 0.0
        }
        
        with open(filepath, 'w') as f:
            json.dump(evaluation_data, f, indent=2)
        
        print(f"Evaluation results saved to {filepath}")


def main():
    """
    Main function demonstrating DSPy metrics usage.
    """
    print("DSPy Metrics for Pokemon Red - Evaluation Example")
    print("="*60)
    
    # Initialize evaluator
    evaluator = PokemonGameplayEvaluator(
        model_name="gpt-4o",
        temperature=0.3
    )
    
    # Run single example
    print("\n1. Single Evaluation Example:")
    print("-" * 30)
    evaluator.run_single_evaluation_example()
    
    # Run comprehensive evaluation
    print("\n\n2. Comprehensive Evaluation:")
    print("-" * 30)
    results = evaluator.run_comprehensive_evaluation()
    
    # Save results
    evaluator.save_evaluation_results(results)
    
    print("\n" + "="*60)
    print("Evaluation complete! Check evaluation_results.json for detailed results.")


if __name__ == "__main__":
    main()

