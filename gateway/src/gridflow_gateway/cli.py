import asyncio
import json

import typer

from gridflow_gateway.frame import capture_rtsp_frame
from gridflow_gateway.models import GatewaySettings, SyntheticGatewaySettings
from gridflow_gateway.pipeline import analyze_and_submit, submit_synthetic

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


@app.command()
def submit_synthetic(
    event_id: str = typer.Option("monza-2026", help="Test event identifier."),
    camera_id: str = typer.Option("cam-04", help="Synthetic camera identifier."),
    zone_id: str = typer.Option("south-exit", help="Operational queue zone identifier."),
    capacity: int = typer.Option(520, min=1, help="Approved test-zone capacity."),
    queue_change_per_minute: float = typer.Option(18, help="Synthetic queue change per minute."),
    detector_people: int = typer.Option(432, min=0, help="Synthetic person-detector count."),
    detector_confidence: float = typer.Option(0.93, min=0, max=1, help="Synthetic detector confidence."),
    density_people: int = typer.Option(440, min=0, help="Synthetic density-estimator count."),
    density_confidence: float = typer.Option(0.90, min=0, max=1, help="Synthetic density confidence."),
) -> None:
    """Submit a marked synthetic observation to a demo environment."""
    settings = SyntheticGatewaySettings.from_environment()
    recommendation = asyncio.run(
        submit_synthetic(
            settings=settings,
            event_id=event_id,
            camera_id=camera_id,
            zone_id=zone_id,
            capacity=capacity,
            queue_change_per_minute=queue_change_per_minute,
            detector_people=detector_people,
            detector_confidence=detector_confidence,
            density_people=density_people,
            density_confidence=density_confidence,
        )
    )
    typer.echo(json.dumps(recommendation, indent=2, sort_keys=True))
