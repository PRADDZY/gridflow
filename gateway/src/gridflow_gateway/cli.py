import asyncio
import json

import typer

from gridflow_gateway.frame import capture_rtsp_frame
from gridflow_gateway.models import GatewaySettings
from gridflow_gateway.pipeline import analyze_and_submit

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def submit_rtsp(
    source: str = typer.Option(..., help="Approved RTSP camera URL."),
    event_id: str = typer.Option(..., help="Race-event identifier."),
    camera_id: str = typer.Option(..., help="Approved camera identifier."),
    zone_id: str = typer.Option(..., help="Operational queue zone identifier."),
    capacity: int = typer.Option(..., min=1, help="Approved people capacity for the zone."),
    queue_change_per_minute: float = typer.Option(..., help="Observed queue change per minute."),
) -> None:
    settings = GatewaySettings.from_environment()
    image = capture_rtsp_frame(source)
    recommendation = asyncio.run(
        analyze_and_submit(
            settings=settings,
            image=image,
            event_id=event_id,
            camera_id=camera_id,
            zone_id=zone_id,
            capacity=capacity,
            queue_change_per_minute=queue_change_per_minute,
        )
    )
    typer.echo(json.dumps(recommendation, indent=2, sort_keys=True))
