import asyncio
import json

import typer

from gridflow_gateway.models import ReferenceGatewaySettings
from gridflow_gateway.pipeline import monitor_reference as run_reference_monitor


app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def gateway() -> None:
    """Run only the external-reference analytics gateway commands."""


@app.command()
def monitor_reference(
    once: bool = typer.Option(False, help="Capture, infer, and submit one real reference sample."),
) -> None:
    settings = ReferenceGatewaySettings.from_environment()
    asyncio.run(
        monitor_reference_samples(
            settings=settings,
            once=once,
        )
    )


async def monitor_reference_samples(*, settings: ReferenceGatewaySettings, once: bool) -> None:
    await run_reference_monitor(
        settings=settings,
        once=once,
        on_sample=lambda observation: typer.echo(json.dumps(observation, indent=2, sort_keys=True)),
    )
