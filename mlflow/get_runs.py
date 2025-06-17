#!/usr/bin/env python3

from datetime import datetime
from typing import Any

import click

import mlflow


@click.command()
@click.option(
    "--limit",
    default=10,
    help="Maximum number of runs to fetch",
    type=int,
)
@click.option(
    "--tracking-uri",
    default="http://localhost:8080",
    help="MLflow tracking server URI",
)
@click.option(
    "--experiment-id",
    help="Filter by specific experiment ID",
    type=str,
)
@click.option(
    "--experiment-name",
    help="Filter by experiment name",
    type=str,
)
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "SCHEDULED", "FINISHED", "FAILED", "KILLED"]),
    help="Filter by run status",
)
@click.option(
    "--sort-by",
    default="start_time",
    type=click.Choice(["start_time", "end_time", "status"]),
    help="Sort runs by field",
)
@click.option(
    "--order",
    default="desc",
    type=click.Choice(["asc", "desc"]),
    help="Sort order",
)
@click.option(
    "--show-traces",
    is_flag=True,
    help="Show trace summary for each run",
)
def get_runs(
    limit: int,
    tracking_uri: str,
    experiment_id: str | None,
    experiment_name: str | None,
    status: str | None,
    sort_by: str,
    order: str,
    show_traces: bool,
) -> None:
    """Fetch and display recent MLflow runs."""
    try:
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(tracking_uri)

        # Get MLflow client
        client = mlflow.MlflowClient()

        # Determine experiment IDs to search
        experiment_ids: list[str] = []
        if experiment_id:
            experiment_ids = [experiment_id]
        elif experiment_name:
            try:
                exp = client.get_experiment_by_name(experiment_name)
                if exp is not None and exp.experiment_id is not None:
                    experiment_ids = [exp.experiment_id]
                else:
                    click.echo(f"Experiment '{experiment_name}' not found.", err=True)
                    return
            except Exception:
                click.echo(f"Experiment '{experiment_name}' not found.", err=True)
                return
        else:
            # Get all experiments if no specific filter
            experiments = client.search_experiments()
            experiment_ids = [
                exp.experiment_id
                for exp in experiments
                if exp.experiment_id is not None
            ]

        # Build filter string
        filter_string = ""
        if status:
            filter_string = f"status = '{status}'"

        # Fetch runs
        runs = client.search_runs(
            experiment_ids=experiment_ids,
            filter_string=filter_string,
            max_results=limit,
            order_by=[f"{sort_by} {order.upper()}"],
        )

        if not runs:
            click.echo("No runs found.")
            return

        # Format run data
        run_data = []
        for run in runs:
            # Get experiment name
            exp_name = "Unknown"
            try:
                exp = client.get_experiment(run.info.experiment_id)
                exp_name = exp.name
            except Exception:
                pass

            # Get artifact information
            artifacts = client.list_artifacts(run.info.run_id)
            artifact_count = len(artifacts)

            run_dict = {
                "run_id": run.info.run_id[:8] + "...",  # Shortened for display
                "full_run_id": run.info.run_id,  # Keep full ID for diagnosis
                "experiment_name": exp_name,
                "status": run.info.status,
                "start_time": _format_timestamp(run.info.start_time),
                "end_time": _format_timestamp(run.info.end_time),
                "duration": _calculate_duration(run.info.start_time, run.info.end_time),
                "artifact_count": artifact_count,
                "artifacts": artifacts,
            }

            # Add key metrics if available
            if run.data.metrics:
                # Show first few metrics
                metrics_str = ", ".join(
                    [f"{k}={v:.3f}" for k, v in list(run.data.metrics.items())[:2]]
                )
                run_dict["key_metrics"] = metrics_str if metrics_str else "None"
            else:
                run_dict["key_metrics"] = "None"

            run_data.append(run_dict)

        # Always show artifact diagnosis by default
        _print_artifact_diagnosis(run_data, client, show_traces)

    except Exception as e:
        click.echo(f"Error fetching runs: {e}", err=True)
        raise click.Abort() from e


def _format_timestamp(timestamp_ms: int | None) -> str:
    """Convert timestamp from milliseconds to readable format."""
    if timestamp_ms is None:
        return "N/A"
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def _calculate_duration(start_ms: int | None, end_ms: int | None) -> str:
    """Calculate duration between start and end times."""
    if start_ms is None:
        return "N/A"
    if end_ms is None:
        return "Running"

    duration_seconds = (end_ms - start_ms) / 1000
    if duration_seconds < 60:
        return f"{duration_seconds:.1f}s"
    elif duration_seconds < 3600:
        return f"{duration_seconds / 60:.1f}m"
    else:
        return f"{duration_seconds / 3600:.1f}h"


def _print_artifact_diagnosis(
    data: list[dict[str, Any]], client, show_traces: bool
) -> None:
    """Print detailed artifact diagnosis for each run."""
    for run in data:
        click.echo(f"\n{'=' * 80}")
        click.echo(f"RUN ID: {run['full_run_id']}")
        click.echo(
            f"Status: {run['status']} | Duration: {run['duration']} | Artifacts: {run['artifact_count']}"
        )
        click.echo(f"Start: {run['start_time']} | End: {run['end_time']}")
        click.echo(f"Metrics: {run['key_metrics']}")

        if run["artifact_count"] > 0:
            click.echo(f"\nARTIFACTS ({run['artifact_count']}):")
            artifacts = run["artifacts"]
            for i, artifact in enumerate(artifacts, 1):
                artifact_info = f"  {i:2d}. {artifact.path}"
                if artifact.is_dir:
                    artifact_info += " (directory)"
                else:
                    artifact_info += f" ({artifact.file_size} bytes)"
                click.echo(artifact_info)

                # Show file contents for small text files
                if not artifact.is_dir and artifact.file_size < 1000:
                    try:
                        if artifact.path.endswith((".txt", ".json", ".log", ".md")):
                            content = client.download_artifacts(
                                run["full_run_id"], artifact.path
                            )
                            with open(content) as f:
                                preview = f.read()[:200]
                                if len(preview) == 200:
                                    preview += "..."
                                click.echo(f"     Preview: {preview}")
                    except Exception:
                        pass
        else:
            click.echo("\nNo artifacts found for this run.")

        # Show tags if any
        try:
            run_details = client.get_run(run["full_run_id"])
            if run_details.data.tags:
                click.echo("\nTAGS:")
                for key, value in run_details.data.tags.items():
                    click.echo(f"  {key}: {value}")
        except Exception:
            pass

        # Show trace summary if requested
        if show_traces:
            _print_trace_summary(run["full_run_id"], client)


def _print_trace_summary(run_id: str, client) -> None:
    """Print trace summary for a specific run."""
    try:
        # Search for traces associated with this run
        traces = client.search_traces(run_id=run_id)

        if not traces:
            click.echo("\nTRACES: No traces found for this run.")
            return

        # Count traces by status
        status_counts = {"OK": 0, "ERROR": 0, "IN_PROGRESS": 0}
        total_traces = len(traces)

        for trace in traces:
            status = getattr(trace.info, "status", "UNKNOWN")
            if status in status_counts:
                status_counts[status] += 1

        click.echo(f"\nTRACES ({total_traces}):")
        if status_counts["OK"] > 0:
            click.echo(f"  ✓ Success: {status_counts['OK']}")
        if status_counts["ERROR"] > 0:
            click.echo(f"  ✗ Error: {status_counts['ERROR']}")
        if status_counts["IN_PROGRESS"] > 0:
            click.echo(f"  ⏳ In Progress: {status_counts['IN_PROGRESS']}")

        # Show recent traces (up to 3)
        recent_traces = traces[:3]
        click.echo("  Recent traces:")
        for trace in recent_traces:
            trace_id = trace.info.trace_id[:8] + "..."
            status_icon = (
                "✓"
                if getattr(trace.info, "status", None) == "OK"
                else ("✗" if getattr(trace.info, "status", None) == "ERROR" else "⏳")
            )
            timestamp_ms = getattr(trace.info, "timestamp_ms", None)
            timestamp_str = _format_timestamp(timestamp_ms) if timestamp_ms else "N/A"
            click.echo(f"    {status_icon} {trace_id} | {timestamp_str}")

    except Exception as e:
        click.echo(f"\nTRACES: Error fetching traces - {e}")


if __name__ == "__main__":
    get_runs()
