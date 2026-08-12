import hashlib
import hmac
import sys
from pathlib import Path
import unittest

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gridflow_gateway.huggingface import HuggingFaceVisionClient, InferenceResponseError
from gridflow_gateway.models import GatewaySettings
from gridflow_gateway.signing import compact_json, signed_headers


SETTINGS = GatewaySettings(
    control_api_url="https://control.example.com",
    ingestion_hmac_secret="not-a-real-production-secret",
    hf_token="hf_not-a-real-token",
    hf_detector_endpoint="https://detector.example.com",
    hf_density_endpoint="https://density.example.com",
)


class GatewayTests(unittest.TestCase):
    def test_signed_headers_match_control_api_contract(self) -> None:
        body = compact_json({"zone_id": "south-exit", "people_count": 436})
        headers = signed_headers(body, SETTINGS.ingestion_hmac_secret, sent_at=1_723_450_000)
        expected = hmac.new(
            SETTINGS.ingestion_hmac_secret.encode(),
            b"1723450000." + body,
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(headers["x-gridflow-signature"], f"sha256={expected}")
        self.assertEqual(headers["x-gridflow-sent-at"], "1723450000")

    def test_detector_counts_people_only(self) -> None:
        client = HuggingFaceVisionClient(SETTINGS, httpx.AsyncClient())
        estimate = client._parse_detector(
            ([
                {"label": "person", "score": 0.8},
                {"label": "car", "score": 0.99},
                {"label": "person", "score": 0.9},
            ], 220)
        )

        self.assertEqual(estimate.people_count, 2)
        self.assertEqual(estimate.confidence, 0.85)

    def test_density_rejects_untrusted_payload(self) -> None:
        client = HuggingFaceVisionClient(SETTINGS, httpx.AsyncClient())

        with self.assertRaises(InferenceResponseError):
            client._parse_density(({"people_count": "436", "confidence": 0.9}, 120))
