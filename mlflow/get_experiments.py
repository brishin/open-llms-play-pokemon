#!/usr/bin/env python3

from datetime import datetime
from typing import Any

import click
from tabulate import tabulate

import mlflow


@click.command()
@click.option(
    "--limit",
    default=3,
    help="Maximum number of experiments to fetch",
    type=int,
)
@click.option(
    "--tracking-uri",
    default="http://localhost:8080",
    help="MLflow tracking server URI",
)
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["table", "json", "csv"]),
    help="Output format",
)
@click.option(
    "--sort-by",
    default="creation_time",
    type=click.Choice(["creation_time", "last_update_time", "name"]),
    help="Sort experiments by field",
)
@click.option(
    "--order",
    default="desc",
    type=click.Choice(["asc", "desc"]),
    help="Sort order",
)
def get_experiments(
    limit: int,
    tracking_uri: str,
    output_format: str,
    sort_by: str,
    order: str,
) -> None:
    """Fetch and display recent MLflow experiments."""
    try:
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(tracking_uri)

        # Get MLflow client
        client = mlflow.MlflowClient()

        # Fetch experiments
        experiments = client.search_experiments(
            max_results=limit, order_by=[f"{sort_by} {order.upper()}"]
        )

        if not experiments:
            click.echo("No experiments found.")
            return

        # Format experiment data
        experiment_data = []
        for exp in experiments:
            # Get run count for this experiment
            runs = client.search_runs(
                experiment_ids=[exp.experiment_id], max_results=1000
            )
            run_count = len(runs)

            exp_dict = {
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "run_count": run_count,
                "artifact_location": exp.artifact_location,
                "lifecycle_stage": exp.lifecycle_stage,
                "creation_time": _format_timestamp(exp.creation_time),
                "last_update_time": _format_timestamp(exp.last_update_time),
            }
            experiment_data.append(exp_dict)

        # Output in requested format
        if output_format == "table":
            _print_table(experiment_data)
        elif output_format == "json":
            _print_json(experiment_data)
        elif output_format == "csv":
            _print_csv(experiment_data)

    except Exception as e:
        click.echo(f"Error fetching experiments: {e}", err=True)
        raise click.Abort() from e


def _format_timestamp(timestamp_ms: int | None) -> str:
    """Convert timestamp from milliseconds to readable format."""
    if timestamp_ms is None:
        return "N/A"
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def _print_table(data: list[dict[str, Any]]) -> None:
    """Print experiments as a formatted table."""
    headers = [
        "ID",
        "Name",
        "Runs",
        "Lifecycle Stage",
        "Created",
        "Last Updated",
        "Artifact Location",
    ]

    table_data = []
    for exp in data:
        table_data.append(
            [
                exp["experiment_id"],
                exp["name"],
                exp["run_count"],
                exp["lifecycle_stage"],
                exp["creation_time"],
                exp["last_update_time"],
                exp["artifact_location"][:50] + "..."
                if len(exp["artifact_location"]) > 50
                else exp["artifact_location"],
            ]
        )

    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


def _print_json(data: list[dict[str, Any]]) -> None:
    """Print experiments as JSON."""
    import json

    click.echo(json.dumps(data, indent=2))


def _print_csv(data: list[dict[str, Any]]) -> None:
    """Print experiments as CSV."""
    import csv
    import sys

    if not data:
        return

    writer = csv.DictWriter(sys.stdout, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)


if __name__ == "__main__":
    get_experiments()
