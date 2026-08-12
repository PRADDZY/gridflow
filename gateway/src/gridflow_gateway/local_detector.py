from io import BytesIO
import time

from gridflow_gateway.detection import VehicleDetectionSummary, summarize_vehicle_detections


class LocalRtdetrDetector:
    """Loads RT-DETR in the gateway process; no video frame leaves the host for inference."""

    def __init__(self, *, model: str, revision: str, threshold: float) -> None:
        self._model_name = model
        self._revision = revision
        self._threshold = threshold
        self._processor = None
        self._model = None

    def analyze_jpeg(self, image_bytes: bytes) -> tuple[VehicleDetectionSummary, int]:
        try:
            import torch
            from PIL import Image
            from transformers import AutoImageProcessor, RTDetrForObjectDetection
        except ImportError as exc:
            raise RuntimeError("Install the gateway with the 'vision' extra to run local RT-DETR inference.") from exc

        if self._processor is None or self._model is None:
            self._processor = AutoImageProcessor.from_pretrained(self._model_name, revision=self._revision)
            self._model = RTDetrForObjectDetection.from_pretrained(self._model_name, revision=self._revision)
            self._model.eval()

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        inputs = self._processor(images=image, return_tensors="pt")
        started = time.perf_counter()
        with torch.no_grad():
            outputs = self._model(**inputs)
        target_sizes = torch.tensor([image.size[::-1]])
        detections = self._processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=self._threshold)[0]
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        labels = self._model.config.id2label
        summarized = summarize_vehicle_detections(
            [
                {"label": labels[int(label)], "score": float(score)}
                for score, label in zip(detections["scores"].tolist(), detections["labels"].tolist(), strict=True)
            ],
            threshold=self._threshold,
        )
        return summarized, elapsed_ms
