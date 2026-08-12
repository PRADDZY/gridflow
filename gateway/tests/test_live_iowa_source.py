import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urljoin
import unittest

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gridflow_gateway.iowa_dot import IowaDotCameraSource
from gridflow_gateway.frame import capture_video_frame
from gridflow_gateway.local_detector import LocalRtdetrDetector


@unittest.skipUnless(
    os.getenv("GRIDFLOW_RUN_LIVE_TESTS") == "true",
    "Set GRIDFLOW_RUN_LIVE_TESTS=true to verify the public Iowa DOT source.",
)
class LiveIowaDotSourceTests(unittest.TestCase):
    def test_metadata_and_hls_playlist_are_live(self) -> None:
        async def verify() -> tuple[str, str, str]:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                camera = await IowaDotCameraSource(client).fetch("iowa-dq-dqtv17", "DQTV17")
                master = await client.get(str(camera.video_url))
                master.raise_for_status()
                child_path = next(
                    line.strip()
                    for line in master.text.splitlines()
                    if line.strip() and not line.startswith("#")
                )
                child = await client.get(urljoin(str(camera.video_url), child_path))
                child.raise_for_status()
                return master.text, child.text, child.headers.get("access-control-allow-origin", "")

        master, child, allow_origin = asyncio.run(verify())

        self.assertIn("#EXTM3U", master)
        self.assertIn("#EXT-X-PROGRAM-DATE-TIME", child)
        self.assertEqual(allow_origin, "*")


@unittest.skipUnless(
    os.getenv("GRIDFLOW_RUN_MODEL_TESTS") == "true",
    "Set GRIDFLOW_RUN_MODEL_TESTS=true to verify local RT-DETR against a live HLS frame.",
)
class LiveLocalVisionTests(unittest.TestCase):
    def test_live_hls_frame_is_processed_locally(self) -> None:
        async def camera_url() -> str:
            async with httpx.AsyncClient(timeout=20.0) as client:
                camera = await IowaDotCameraSource(client).fetch("iowa-dq-dqtv17", "DQTV17")
                return str(camera.video_url)

        frame = capture_video_frame(asyncio.run(camera_url()))
        summary, inference_ms = LocalRtdetrDetector(
            model="PekingU/rtdetr_r50vd",
            revision="main",
            threshold=0.5,
        ).analyze_jpeg(frame)

        self.assertGreater(len(frame), 1_000)
        self.assertGreaterEqual(summary.class_counts.total, 0)
        self.assertGreaterEqual(inference_ms, 0)
