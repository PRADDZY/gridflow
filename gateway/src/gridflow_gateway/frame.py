def capture_video_frame(source: str) -> bytes:
    """Reads one in-memory JPEG frame from an approved public HLS stream."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Install the gateway with the 'vision' extra to capture HLS video frames.") from exc

    capture = cv2.VideoCapture(source)
    try:
        if not capture.isOpened():
            raise RuntimeError("Unable to open the approved public HLS camera source.")
        captured, frame = capture.read()
        if not captured:
            raise RuntimeError("Unable to read a frame from the approved public HLS camera source.")
        encoded, image = cv2.imencode(".jpg", frame)
        if not encoded:
            raise RuntimeError("Unable to encode the public camera frame as JPEG.")
        return image.tobytes()
    finally:
        capture.release()
