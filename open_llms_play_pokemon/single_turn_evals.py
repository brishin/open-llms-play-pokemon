import base64
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, Any

import dspy
import mlflow
import pandas as pd
import typer


@dataclass
class BoundingBox:
    """Represents a bounding box with optional label."""

    x: float
    y: float
    width: float
    height: float
    label: str | None = None
    confidence: float | None = None


@dataclass
class EvalConfig:
    """Configuration for running evaluations."""

    model: str
    temperature: float


@dataclass
class EvaluationResult:
    """Dataclass to hold evaluation results for a single run."""

    image_path: str
    config: dict[str, Any]
    prompt: str
    success: bool
    error: str | None
    num_boxes: int
    bounding_boxes: list[dict[str, Any]]
    raw_reasoning: str | None
    raw_output: str | None
    run_id: str | None


class BoundingBoxTask(dspy.Signature):
    """DSPy signature for bounding box generation from images."""

    image = dspy.InputField(desc="Base64 encoded image to analyze")
    prompt = dspy.InputField(desc="Text prompt for the vision model")

    bounding_boxes = dspy.OutputField(
        desc="JSON array of bounding boxes in format: "
        "[{'x': float, 'y': float, 'width': float, 'height': float, 'label': str}]"
    )


class BoundingBoxGenerator(dspy.Module):
    """DSPy module for generating bounding boxes from images."""

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(BoundingBoxTask)

    def forward(
        self, image: str, prompt: str = "Draw bounding boxes on each object here"
    ) -> dspy.Prediction:
        """Generate bounding boxes for objects in the image."""
        return self.generate(image=image, prompt=prompt)


def bounding_box_accuracy_metric(predictions, targets=None):
    """Custom MLflow metric for bounding box evaluation."""
    success_rate = sum(1 for pred in predictions if pred.get("success", False)) / len(
        predictions
    )
    avg_boxes = sum(
        pred.get("num_boxes", 0) for pred in predictions if pred.get("success", False)
    )
    successful_predictions = sum(
        1 for pred in predictions if pred.get("success", False)
    )
    avg_boxes = avg_boxes / successful_predictions if successful_predictions > 0 else 0

    return {
        "success_rate": success_rate,
        "avg_boxes_per_image": avg_boxes,
        "total_evaluations": len(predictions),
    }


class BoundingBoxEvaluator:
    """Evaluator for bounding box generation across multiple providers and settings using MLflow."""

    def __init__(
        self,
        mlflow_tracking_uri: str = "http://localhost:8080",
        experiment_name: str = "single_turn_evals",
    ):
        self.generator = BoundingBoxGenerator()
        self.current_experiment = experiment_name

        # Configure MLflow
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)

    def setup_llm(self, config: EvalConfig) -> dspy.LM:
        """Setup LLM based on configuration."""
        return dspy.LM(
            model=config.model,
            temperature=config.temperature,
            max_tokens=2048,
        )

    def encode_image(self, image_path: str | Path) -> str:
        """Encode image as base64 string."""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def parse_bounding_boxes(self, bounding_boxes_str: str) -> list[BoundingBox]:
        """Parse bounding boxes from JSON string."""
        try:
            boxes_data = json.loads(bounding_boxes_str)
            if not isinstance(boxes_data, list):
                return []

            boxes = []
            for box_data in boxes_data:
                if isinstance(box_data, dict) and all(
                    key in box_data for key in ["x", "y", "width", "height"]
                ):
                    boxes.append(
                        BoundingBox(
                            x=float(box_data["x"]),
                            y=float(box_data["y"]),
                            width=float(box_data["width"]),
                            height=float(box_data["height"]),
                            label=box_data.get("label"),
                            confidence=box_data.get("confidence"),
                        )
                    )
            return boxes
        except (json.JSONDecodeError, ValueError, KeyError):
            return []

    def evaluate_single(
        self,
        image_path: str | Path,
        config: EvalConfig,
        prompt: str = "Draw bounding boxes on each object here",
    ) -> dict[str, Any]:
        """Run evaluation for a single image with given configuration using MLflow."""
        with mlflow.start_run(nested=True):
            # Log parameters
            mlflow.log_param("model", config.model)
            mlflow.log_param("temperature", config.temperature)
            mlflow.log_param("image_path", str(image_path))
            mlflow.log_param("prompt", prompt)

            # Setup LLM
            llm = self.setup_llm(config)

            with dspy.context(lm=llm):
                # Encode image
                image_b64 = self.encode_image(image_path)

                # Generate bounding boxes
                try:
                    result = self.generator(image=image_b64, prompt=prompt)
                    bounding_boxes = self.parse_bounding_boxes(result.bounding_boxes)
                    success = True
                    error = None

                    # Log artifacts
                    mlflow.log_text(result.rationale, "reasoning.txt")
                    mlflow.log_text(result.bounding_boxes, "raw_bounding_boxes.json")

                except Exception as e:
                    bounding_boxes = []
                    success = False
                    error = str(e)
                    result = None
                    mlflow.log_text(str(e), "error.txt")

            # Log metrics
            mlflow.log_metric("success", 1.0 if success else 0.0)
            mlflow.log_metric("num_boxes", len(bounding_boxes))

            if error:
                mlflow.log_param("error", error)

            eval_result = EvaluationResult(
                image_path=str(image_path),
                config={
                    "model": config.model,
                    "temperature": config.temperature,
                },
                prompt=prompt,
                success=success,
                error=error,
                num_boxes=len(bounding_boxes),
                bounding_boxes=[asdict(box) for box in bounding_boxes],
                raw_reasoning=result.rationale if result else None,
                raw_output=result.bounding_boxes if result else None,
                run_id=(active_run := mlflow.active_run()) and active_run.info.run_id,
            )

            # Log the full result as JSON artifact
            mlflow.log_dict(asdict(eval_result), "evaluation_result.json")

            return asdict(eval_result)

    def evaluate_batch(
        self,
        image_paths: list[str | Path],
        configs: list[EvalConfig],
        prompt: str = "Draw bounding boxes on each object here",
        experiment_name: str | None = None,
    ) -> pd.DataFrame:
        """Run evaluations for multiple images and configurations using MLflow."""
        if experiment_name:
            mlflow.set_experiment(experiment_name)
            self.current_experiment = experiment_name

        batch_results = []

        with mlflow.start_run(run_name="batch_evaluation"):
            # Log batch parameters
            mlflow.log_param("num_images", len(image_paths))
            mlflow.log_param("num_configs", len(configs))
            mlflow.log_param("total_evaluations", len(image_paths) * len(configs))
            mlflow.log_param("prompt", prompt)

            for image_path in image_paths:
                for config in configs:
                    print(
                        f"Evaluating {image_path} with {config.model} (T={config.temperature})"
                    )
                    result = self.evaluate_single(image_path, config, prompt)
                    batch_results.append(result)

            # Create evaluation dataset for MLflow
            eval_data = pd.DataFrame(batch_results)

            # Use MLflow evaluate for comprehensive evaluation
            if batch_results:
                mlflow.evaluate(
                    data=eval_data,
                    model_type="question-answering",  # Closest available type
                    evaluators="default",
                    extra_metrics=[bounding_box_accuracy_metric],
                )

                # Log aggregate metrics
                total_success = sum(1 for r in batch_results if r["success"])
                total_evaluations = len(batch_results)
                success_rate = (
                    total_success / total_evaluations if total_evaluations > 0 else 0
                )

                mlflow.log_metric("overall_success_rate", success_rate)
                mlflow.log_metric("total_successful_evaluations", total_success)

                # Group metrics by model
                model_metrics = eval_data.groupby(
                    eval_data["config"].apply(lambda x: x.get("model"))
                ).apply(
                    lambda g: pd.Series(
                        {
                            "success_rate": g["success"].mean() * 100,
                            "avg_boxes": g[g["success"]]["num_boxes"].mean()
                            if g["success"].any()
                            else 0,
                        }
                    )
                )

                for model, stats in model_metrics.iterrows():
                    mlflow.log_metric(f"{model}_success_rate", stats["success_rate"])
                    mlflow.log_metric(f"{model}_avg_boxes", stats["avg_boxes"])

            return eval_data

    def get_experiment_results(
        self, experiment_name: str | None = None
    ) -> pd.DataFrame:
        """Retrieve results from MLflow experiment."""
        exp_name = experiment_name or self.current_experiment
        experiment = mlflow.get_experiment_by_name(exp_name)
        if experiment is None:
            print(f"Experiment '{exp_name}' not found")
            return pd.DataFrame()

        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        return runs if isinstance(runs, pd.DataFrame) else pd.DataFrame()

    def print_mlflow_summary(self, experiment_name: str | None = None) -> None:
        """Print summary of evaluation results from MLflow."""
        runs_df = self.get_experiment_results(experiment_name)

        if runs_df.empty:
            print("No evaluation results found in MLflow")
            return

        # Filter for individual evaluation runs (not batch runs)
        individual_runs = runs_df[runs_df["tags.mlflow.runName"] != "batch_evaluation"]

        if individual_runs.empty:
            print("No individual evaluation runs found")
            return

        total = len(individual_runs)
        successful = individual_runs["metrics.success"].sum()

        print("\nMLflow Evaluation Summary:")
        print(f"Total evaluations: {total}")
        print(f"Successful: {int(successful)} ({successful / total * 100:.1f}%)")
        print(
            f"Failed: {total - int(successful)} ({(total - successful) / total * 100:.1f}%)"
        )

        # Group by model
        if "params.model" in individual_runs.columns:
            print("\nBy Model:")

            successful_runs_df = individual_runs[
                individual_runs["metrics.success"] == 1.0
            ]
            avg_boxes_per_model = successful_runs_df.groupby("params.model")[
                "metrics.num_boxes"
            ].mean()

            model_stats = individual_runs.groupby("params.model").agg(
                total_runs=("metrics.success", "count"),
                successful_runs=("metrics.success", "sum"),
            )

            model_stats["success_rate"] = (
                (model_stats["successful_runs"] / model_stats["total_runs"]) * 100
            ).fillna(0)
            model_stats["avg_boxes"] = avg_boxes_per_model.reindex(
                model_stats.index
            ).fillna(0)

            for model, stats in model_stats.iterrows():
                print(
                    f"  {model}: {stats['success_rate']:.1f}% success, {stats['avg_boxes']:.1f} avg boxes"
                )


def create_sample_configs() -> list[EvalConfig]:
    """Create sample configurations for different models and temperatures."""
    configs = []

    # OpenAI configurations
    for temp in [0.0, 0.3, 0.7, 1.0]:
        configs.append(EvalConfig(model="gpt-4o", temperature=temp))

    return configs


def main(
    images: Annotated[
        list[str | Path], typer.Option("--images", help="Image file paths")
    ],
    experiment: Annotated[
        str, typer.Option("--experiment", help="MLflow experiment name")
    ] = "single_turn_evals",
    mlflow_uri: Annotated[
        str, typer.Option("--mlflow-uri", help="MLflow tracking server URI")
    ] = "http://localhost:8080",
    prompt: Annotated[
        str, typer.Option("--prompt", help="Prompt for the model")
    ] = "Draw bounding boxes on each object here",
    summary_only: Annotated[
        bool,
        typer.Option(
            "--summary-only", help="Only print summary from existing MLflow runs"
        ),
    ] = False,
):
    """Run bounding box generation evaluations with MLflow."""
    # Create evaluator
    evaluator = BoundingBoxEvaluator(
        mlflow_tracking_uri=mlflow_uri, experiment_name=experiment
    )

    if summary_only:
        evaluator.print_mlflow_summary(experiment)
        return

    # Create sample configurations
    configs = create_sample_configs()

    # Run evaluations
    evaluator.evaluate_batch(images, configs, prompt, experiment)

    # Print summary
    evaluator.print_mlflow_summary(experiment)

    print(f"\nResults tracked in MLflow at {mlflow_uri}")
    print(f"Experiment: {experiment}")


if __name__ == "__main__":
    typer.run(main)
