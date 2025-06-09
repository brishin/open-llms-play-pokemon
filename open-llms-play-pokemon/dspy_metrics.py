"""
DSPy metrics implementation for Pokemon Red gameplay evaluation.

This module implements various metrics following DSPy patterns for evaluating
AI agent performance in Pokemon Red gameplay scenarios.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import dspy
from dspy.evaluate import Evaluate


@dataclass
class GameplayExample:
    """Example data structure for Pokemon Red gameplay evaluation."""
    
    screen_base64: str
    context: str
    expected_action: Optional[str] = None
    expected_buttons: Optional[List[str]] = None
    game_progress_indicators: Optional[Dict[str, Any]] = None
    success_criteria: Optional[Dict[str, Any]] = None


@dataclass
class GameplayPrediction:
    """Prediction data structure for Pokemon Red gameplay."""
    
    action: str
    buttons: List[str]
    reasoning: Optional[str] = None
    confidence: Optional[float] = None


# Simple Metrics
def action_exact_match(example: GameplayExample, pred: GameplayPrediction, trace=None) -> Union[bool, float]:
    """
    Simple exact match metric for action prediction.
    
    Args:
        example: Ground truth example with expected action
        pred: Model prediction
        trace: Optional trace for optimization (unused in this simple metric)
    
    Returns:
        bool: True if actions match exactly, False otherwise
    """
    if not example.expected_action:
        return False
    
    return example.expected_action.lower().strip() == pred.action.lower().strip()


def buttons_exact_match(example: GameplayExample, pred: GameplayPrediction, trace=None) -> Union[bool, float]:
    """
    Simple exact match metric for button sequence prediction.
    
    Args:
        example: Ground truth example with expected buttons
        pred: Model prediction
        trace: Optional trace for optimization
    
    Returns:
        bool: True if button sequences match exactly, False otherwise
    """
    if not example.expected_buttons:
        return False
    
    expected_buttons = [btn.lower().strip() for btn in example.expected_buttons]
    pred_buttons = [btn.lower().strip() for btn in pred.buttons]
    
    return expected_buttons == pred_buttons


def buttons_partial_match(example: GameplayExample, pred: GameplayPrediction, trace=None) -> Union[bool, float]:
    """
    Partial match metric for button sequences - allows for some flexibility.
    
    Args:
        example: Ground truth example with expected buttons
        pred: Model prediction
        trace: Optional trace for optimization
    
    Returns:
        float: Ratio of matching buttons (0.0 to 1.0)
    """
    if not example.expected_buttons:
        return 0.0
    
    expected_buttons = set(btn.lower().strip() for btn in example.expected_buttons)
    pred_buttons = set(btn.lower().strip() for btn in pred.buttons)
    
    if not expected_buttons:
        return 1.0 if not pred_buttons else 0.0
    
    intersection = expected_buttons.intersection(pred_buttons)
    return len(intersection) / len(expected_buttons)


# Complex Metrics with Multiple Criteria
def gameplay_effectiveness_metric(example: GameplayExample, pred: GameplayPrediction, trace=None) -> Union[bool, float]:
    """
    Complex metric evaluating multiple aspects of gameplay effectiveness.
    
    Checks:
    1. Action appropriateness for the context
    2. Button sequence validity
    3. Strategic reasoning quality
    
    Args:
        example: Ground truth example
        pred: Model prediction
        trace: Optional trace for optimization
    
    Returns:
        float: Composite score (0.0 to 1.0) if trace is None, bool if trace is provided
    """
    scores = []
    
    # 1. Check if buttons are valid GameBoy buttons
    valid_buttons = {'a', 'b', 'start', 'select', 'up', 'down', 'left', 'right'}
    button_validity = all(btn.lower() in valid_buttons for btn in pred.buttons) if pred.buttons else False
    scores.append(1.0 if button_validity else 0.0)
    
    # 2. Check if action contains reasonable Pokemon-related terms
    pokemon_terms = ['move', 'battle', 'catch', 'explore', 'menu', 'select', 'navigate', 'talk', 'interact']
    action_relevance = any(term in pred.action.lower() for term in pokemon_terms) if pred.action else False
    scores.append(1.0 if action_relevance else 0.0)
    
    # 3. Check if reasoning is provided and substantial
    reasoning_quality = len(pred.reasoning.split()) >= 5 if pred.reasoning else False
    scores.append(1.0 if reasoning_quality else 0.0)
    
    # 4. Check button sequence length is reasonable (not too long or empty)
    sequence_length_ok = 1 <= len(pred.buttons) <= 5 if pred.buttons else False
    scores.append(1.0 if sequence_length_ok else 0.0)
    
    composite_score = sum(scores) / len(scores)
    
    if trace is None:  # Evaluation mode
        return composite_score
    else:  # Optimization/bootstrapping mode - be strict
        return composite_score >= 0.75


# AI-Feedback Based Metrics
class GameplayAssessment(dspy.Signature):
    """Signature for AI-based gameplay assessment."""
    
    game_context = dspy.InputField(desc="Current game context and situation")
    predicted_action = dspy.InputField(desc="AI agent's predicted action")
    predicted_buttons = dspy.InputField(desc="AI agent's predicted button sequence")
    assessment_question = dspy.InputField(desc="Specific question about the gameplay decision")
    
    assessment_answer: bool = dspy.OutputField(desc="Whether the gameplay decision is appropriate")
    assessment_reasoning = dspy.OutputField(desc="Explanation of the assessment")


def ai_gameplay_assessment_metric(example: GameplayExample, pred: GameplayPrediction, trace=None) -> Union[bool, float]:
    """
    AI-feedback based metric for gameplay assessment.
    
    Uses a DSPy module to assess the quality of gameplay decisions using AI feedback.
    
    Args:
        example: Ground truth example
        pred: Model prediction
        trace: Optional trace for optimization
    
    Returns:
        float: AI assessment score (0.0 to 1.0) if trace is None, bool if trace is provided
    """
    assessor = dspy.Predict(GameplayAssessment)
    
    # Prepare assessment questions
    questions = [
        "Is this action appropriate for the current Pokemon Red game context?",
        "Are the predicted buttons valid and likely to achieve the stated action?",
        "Does the action show strategic thinking appropriate for Pokemon gameplay?"
    ]
    
    scores = []
    
    for question in questions:
        try:
            assessment = assessor(
                game_context=example.context,
                predicted_action=pred.action,
                predicted_buttons=", ".join(pred.buttons) if pred.buttons else "None",
                assessment_question=question
            )
            scores.append(1.0 if assessment.assessment_answer else 0.0)
        except Exception:
            # If AI assessment fails, give neutral score
            scores.append(0.5)
    
    composite_score = sum(scores) / len(scores) if scores else 0.0
    
    if trace is None:  # Evaluation mode
        return composite_score
    else:  # Optimization/bootstrapping mode
        return composite_score >= 0.67


# Progress-Based Metrics
def game_progress_metric(example: GameplayExample, pred: GameplayPrediction, trace=None) -> Union[bool, float]:
    """
    Metric based on game progress indicators.
    
    Evaluates whether the predicted action is likely to advance game progress
    based on known progress indicators.
    
    Args:
        example: Ground truth example with progress indicators
        pred: Model prediction
        trace: Optional trace for optimization
    
    Returns:
        float: Progress likelihood score (0.0 to 1.0)
    """
    if not example.game_progress_indicators:
        return 0.5  # Neutral score if no progress indicators
    
    progress_score = 0.0
    total_indicators = 0
    
    # Check various progress indicators
    indicators = example.game_progress_indicators
    
    # Location-based progress
    if 'current_location' in indicators:
        location_actions = {
            'pallet_town': ['up', 'down', 'left', 'right', 'a'],  # Exploration
            'route_1': ['up', 'down', 'a'],  # Moving and battling
            'viridian_city': ['a', 'up', 'down'],  # Interacting with NPCs
            'pokemon_center': ['a', 'up'],  # Healing Pokemon
            'battle': ['a', 'b'],  # Battle actions
        }
        
        current_loc = indicators['current_location'].lower()
        for loc, expected_buttons in location_actions.items():
            if loc in current_loc:
                if any(btn in pred.buttons for btn in expected_buttons):
                    progress_score += 1.0
                total_indicators += 1
                break
    
    # Health-based decisions
    if 'pokemon_health' in indicators:
        health_ratio = indicators.get('pokemon_health', 1.0)
        if health_ratio < 0.3:  # Low health
            if 'pokemon_center' in pred.action.lower() or 'heal' in pred.action.lower():
                progress_score += 1.0
            total_indicators += 1
    
    # Inventory-based decisions
    if 'has_pokeballs' in indicators:
        has_pokeballs = indicators['has_pokeballs']
        if not has_pokeballs and ('buy' in pred.action.lower() or 'shop' in pred.action.lower()):
            progress_score += 1.0
            total_indicators += 1
    
    final_score = progress_score / total_indicators if total_indicators > 0 else 0.5
    
    if trace is None:
        return final_score
    else:
        return final_score >= 0.6


# Advanced Metric Using DSPy Program
class GameplayValidator(dspy.Module):
    """DSPy module for comprehensive gameplay validation."""
    
    def __init__(self):
        super().__init__()
        self.assess_strategy = dspy.ChainOfThought(GameplayAssessment)
    
    def forward(self, example: GameplayExample, pred: GameplayPrediction) -> Dict[str, Any]:
        """
        Comprehensive validation of gameplay decision.
        
        Returns:
            Dict with various assessment scores and reasoning
        """
        # Strategic assessment
        strategy_assessment = self.assess_strategy(
            game_context=example.context,
            predicted_action=pred.action,
            predicted_buttons=", ".join(pred.buttons) if pred.buttons else "None",
            assessment_question="Is this a strategically sound decision for Pokemon Red gameplay?"
        )
        
        # Technical validation
        valid_buttons = {'a', 'b', 'start', 'select', 'up', 'down', 'left', 'right'}
        technical_score = all(btn.lower() in valid_buttons for btn in pred.buttons) if pred.buttons else False
        
        return {
            'strategy_score': 1.0 if strategy_assessment.assessment_answer else 0.0,
            'strategy_reasoning': strategy_assessment.assessment_reasoning,
            'technical_score': 1.0 if technical_score else 0.0,
            'overall_valid': strategy_assessment.assessment_answer and technical_score
        }


def advanced_gameplay_metric(example: GameplayExample, pred: GameplayPrediction, trace=None) -> Union[bool, float]:
    """
    Advanced metric using a DSPy program for validation.
    
    Args:
        example: Ground truth example
        pred: Model prediction
        trace: Optional trace for optimization
    
    Returns:
        float: Composite validation score
    """
    validator = GameplayValidator()
    
    try:
        validation_result = validator.forward(example, pred)
        
        # Combine scores
        strategy_weight = 0.7
        technical_weight = 0.3
        
        composite_score = (
            validation_result['strategy_score'] * strategy_weight +
            validation_result['technical_score'] * technical_weight
        )
        
        if trace is None:
            return composite_score
        else:
            return validation_result['overall_valid']
            
    except Exception:
        # Fallback to basic validation if advanced validation fails
        return gameplay_effectiveness_metric(example, pred, trace)


# Trace-Based Metrics for Optimization
def validate_reasoning_steps(example: GameplayExample, pred: GameplayPrediction, trace=None) -> bool:
    """
    Validate intermediate reasoning steps using trace information.
    
    This metric is specifically designed for optimization and requires trace information.
    
    Args:
        example: Ground truth example
        pred: Model prediction
        trace: Trace information from DSPy execution
    
    Returns:
        bool: Whether the reasoning steps are valid
    """
    if trace is None:
        return True  # Can't validate without trace
    
    # Extract reasoning steps from trace
    reasoning_steps = []
    for step in trace:
        if hasattr(step, 'outputs') and 'reasoning' in step.outputs:
            reasoning_steps.append(step.outputs['reasoning'])
    
    # Validate reasoning quality
    if not reasoning_steps:
        return False
    
    # Check if reasoning mentions key Pokemon concepts
    pokemon_concepts = ['pokemon', 'battle', 'move', 'gym', 'trainer', 'wild', 'catch']
    
    for step in reasoning_steps:
        if not any(concept in step.lower() for concept in pokemon_concepts):
            return False
        
        # Check reasoning length (should be substantial)
        if len(step.split()) < 10:
            return False
    
    return True


# Utility Functions for Evaluation
def create_pokemon_evaluator(
    devset: List[GameplayExample],
    metric_name: str = "gameplay_effectiveness",
    num_threads: int = 1,
    display_progress: bool = True,
    display_table: int = 5
) -> Evaluate:
    """
    Create a DSPy evaluator for Pokemon Red gameplay.
    
    Args:
        devset: Development/test dataset
        metric_name: Name of the metric to use
        num_threads: Number of threads for parallel evaluation
        display_progress: Whether to display progress
        display_table: Number of examples to display in table
    
    Returns:
        Configured DSPy Evaluate instance
    """
    # Map metric names to functions
    metric_map = {
        "action_exact_match": action_exact_match,
        "buttons_exact_match": buttons_exact_match,
        "buttons_partial_match": buttons_partial_match,
        "gameplay_effectiveness": gameplay_effectiveness_metric,
        "ai_assessment": ai_gameplay_assessment_metric,
        "game_progress": game_progress_metric,
        "advanced_gameplay": advanced_gameplay_metric,
        "reasoning_validation": validate_reasoning_steps,
    }
    
    if metric_name not in metric_map:
        raise ValueError(f"Unknown metric: {metric_name}. Available: {list(metric_map.keys())}")
    
    return Evaluate(
        devset=devset,
        metric=metric_map[metric_name],
        num_threads=num_threads,
        display_progress=display_progress,
        display_table=display_table
    )


def run_comprehensive_evaluation(
    program: dspy.Module,
    devset: List[GameplayExample],
    metrics: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Run comprehensive evaluation with multiple metrics.
    
    Args:
        program: DSPy program to evaluate
        devset: Development/test dataset
        metrics: List of metric names to use (default: all available)
    
    Returns:
        Dictionary mapping metric names to scores
    """
    if metrics is None:
        metrics = [
            "gameplay_effectiveness",
            "buttons_partial_match", 
            "game_progress",
            "ai_assessment"
        ]
    
    results = {}
    
    for metric_name in metrics:
        try:
            evaluator = create_pokemon_evaluator(devset, metric_name, display_progress=False)
            score = evaluator(program)
            results[metric_name] = score
            print(f"{metric_name}: {score:.3f}")
        except Exception as e:
            print(f"Error evaluating {metric_name}: {e}")
            results[metric_name] = 0.0
    
    return results


# Example usage and testing
if __name__ == "__main__":
    # Example data for testing
    example = GameplayExample(
        screen_base64="dummy_base64_data",
        context="Player is in Pallet Town and needs to visit Professor Oak's lab",
        expected_action="Move up to enter Professor Oak's lab",
        expected_buttons=["up", "a"],
        game_progress_indicators={
            "current_location": "pallet_town",
            "pokemon_health": 1.0,
            "has_pokeballs": False
        }
    )
    
    pred = GameplayPrediction(
        action="Move up to enter the lab and talk to Professor Oak",
        buttons=["up", "a"],
        reasoning="The player needs to meet Professor Oak to start their Pokemon journey. Moving up will enter the lab, and pressing 'a' will interact with NPCs inside.",
        confidence=0.9
    )
    
    # Test various metrics
    print("Testing DSPy Metrics for Pokemon Red:")
    print(f"Action exact match: {action_exact_match(example, pred)}")
    print(f"Buttons exact match: {buttons_exact_match(example, pred)}")
    print(f"Buttons partial match: {buttons_partial_match(example, pred)}")
    print(f"Gameplay effectiveness: {gameplay_effectiveness_metric(example, pred)}")
    print(f"Game progress: {game_progress_metric(example, pred)}")

