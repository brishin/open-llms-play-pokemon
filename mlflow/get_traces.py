#!/usr/bin/env python3

from datetime import datetime

import click

import mlflow


@click.command()
@click.option(
    "--limit",
    default=2,
    help="Maximum number of traces to fetch",
    type=int,
)
@click.option(
    "--tracking-uri",
    default="http://localhost:8080",
    help="MLflow tracking server URI",
)
@click.option(
    "--run-id",
    help="Filter by specific run ID",
    type=str,
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
    type=click.Choice(["OK", "ERROR", "IN_PROGRESS"]),
    help="Filter by trace status",
)
@click.option(
    "--sort-by",
    default="timestamp_ms",
    type=click.Choice(["timestamp_ms", "status"]),
    help="Sort traces by field",
)
@click.option(
    "--order",
    default="desc",
    type=click.Choice(["asc", "desc"]),
    help="Sort order",
)
def get_traces(
    limit: int,
    tracking_uri: str,
    run_id: str | None,
    experiment_id: str | None,
    experiment_name: str | None,
    status: str | None,
    sort_by: str,
    order: str,
) -> None:
    """Fetch and display MLflow traces with detailed information."""
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

        if run_id:
            # When searching by run_id, we need to get the experiment_id first
            try:
                run = client.get_run(run_id)
                experiment_ids = [run.info.experiment_id]
            except Exception:
                click.echo(f"Run '{run_id}' not found.", err=True)
                return

        # Ensure we have experiment_ids
        if not experiment_ids:
            click.echo("No experiments found to search.", err=True)
            return

        # Build filter string for status and run_id
        filter_parts = []
        if status:
            filter_parts.append(f"status = '{status}'")
        if run_id:
            filter_parts.append(f"run_id = '{run_id}'")

        filter_string = " AND ".join(filter_parts) if filter_parts else None

        # Add ordering
        order_by = f"{sort_by} {order.upper()}"

        # Fetch traces
        traces = client.search_traces(
            experiment_ids=experiment_ids,
            filter_string=filter_string,
            order_by=[order_by],
            max_results=limit,
        )

        if not traces:
            click.echo("No traces found.")
            return

        # Display traces
        click.echo(f"Found {len(traces)} trace(s):")
        click.echo("=" * 120)

        for i, trace in enumerate(traces, 1):
            _print_trace_details(trace, client, i)
            if i < len(traces):
                click.echo("\n" + "-" * 120)

    except Exception as e:
        click.echo(f"Error fetching traces: {e}", err=True)
        raise click.Abort() from e


def _print_trace_details(trace, client, index: int) -> None:
    """Print detailed information for a single trace."""
    trace_info = trace.info
    trace_data = trace.data

    # Format basic trace information
    trace_id = getattr(trace_info, "trace_id", None) or getattr(
        trace_info, "request_id", "unknown"
    )
    short_trace_id = trace_id[:8] + "..." if len(str(trace_id)) > 8 else str(trace_id)
    status = getattr(trace_info, "status", "UNKNOWN")
    timestamp_ms = getattr(trace_info, "timestamp_ms", None)
    execution_time_ms = getattr(trace_info, "execution_time_ms", None)

    # Status icon
    status_icon = {"OK": "✓", "ERROR": "✗", "IN_PROGRESS": "⏳"}.get(status, "?")

    # Format timestamps
    timestamp_str = _format_timestamp(timestamp_ms) if timestamp_ms else "N/A"
    duration_str = (
        _format_duration_ms(execution_time_ms) if execution_time_ms else "N/A"
    )

    # Print trace header
    click.echo(f"\n{index:2d}. TRACE {short_trace_id} {status_icon} {status}")
    click.echo(f"    Full ID: {trace_id}")
    click.echo(f"    Timestamp: {timestamp_str}")
    click.echo(f"    Duration: {duration_str}")

    # Show associated run/experiment if available
    run_id = getattr(trace_info, "run_id", None)
    if run_id:
        click.echo(f"    Run ID: {run_id}")
        try:
            run = client.get_run(run_id)
            exp = client.get_experiment(run.info.experiment_id)
            click.echo(f"    Experiment: {exp.name}")
        except Exception:
            pass

    # Show trace tags if any
    if hasattr(trace_data, "tags") and trace_data.tags:
        click.echo("    Tags:")
        for key, value in trace_data.tags.items():
            click.echo(f"      {key}: {value}")

    _print_trace_spans(trace, client)


def _print_trace_spans(trace, client) -> None:  # noqa: ARG001
    """Print detailed span information for a trace."""
    try:
        # Get spans for this trace
        spans = getattr(trace.data, "spans", [])

        if not spans:
            click.echo("    No spans found.")
            return

        click.echo(f"    Spans ({len(spans)}):")

        for i, span in enumerate(spans, 1):
            span_name = getattr(span, "name", "Unknown")
            span_status = getattr(span, "status", "UNKNOWN")

            # Handle SpanStatus object - extract status_code
            status_str = "UNKNOWN"
            if hasattr(span_status, "status_code") and not isinstance(span_status, str):
                status_code = span_status.status_code
                if hasattr(status_code, "value"):
                    status_str = status_code.value
                else:
                    status_str = str(status_code).split(".")[-1]  # Extract enum name
            elif hasattr(span_status, "name") and not isinstance(span_status, str):
                status_str = span_status.name
            else:
                status_str = str(span_status)

            # Map common status values
            status_mapping = {
                "OK": "✓",
                "UNSET": "✓",  # Often means success
                "ERROR": "✗",
                "IN_PROGRESS": "⏳",
                "RUNNING": "⏳"
            }

            status_icon = status_mapping.get(status_str.upper(), "?")

            start_time = getattr(span, "start_time_ns", None)
            end_time = getattr(span, "end_time_ns", None)

            # Calculate duration
            duration_str = "N/A"
            if start_time and end_time:
                duration_ns = end_time - start_time
                duration_str = _format_duration_ns(duration_ns)

            click.echo(f"      {i:2d}. {status_icon} {span_name} | {duration_str}")

            # Show span attributes if available
            if hasattr(span, "attributes") and span.attributes:
                key_attrs = ["input", "output", "error"]
                for attr_key in key_attrs:
                    if attr_key in span.attributes:
                        attr_value = str(span.attributes[attr_key])[:100]
                        if len(str(span.attributes[attr_key])) > 100:
                            attr_value += "..."
                        click.echo(f"          {attr_key}: {attr_value}")

    except Exception as e:
        click.echo(f"    Error fetching spans: {e}")


def _format_timestamp(timestamp_ms: int | None) -> str:
    """Convert timestamp from milliseconds to readable format."""
    if timestamp_ms is None:
        return "N/A"
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def _format_duration_ms(duration_ms: int | None) -> str:
    """Format duration from milliseconds to readable format."""
    if duration_ms is None:
        return "N/A"

    duration_seconds = duration_ms / 1000
    if duration_seconds < 1:
        return f"{duration_ms}ms"
    elif duration_seconds < 60:
        return f"{duration_seconds:.2f}s"
    elif duration_seconds < 3600:
        return f"{duration_seconds / 60:.1f}m"
    else:
        return f"{duration_seconds / 3600:.1f}h"


def _format_duration_ns(duration_ns: int) -> str:
    """Format duration from nanoseconds to readable format."""
    duration_ms = duration_ns / 1_000_000
    return _format_duration_ms(int(duration_ms))


if __name__ == "__main__":
    get_traces()
