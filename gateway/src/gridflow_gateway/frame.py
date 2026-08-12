def capture_rtsp_frame(source: str) -> bytes:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Install the gateway with the 'rtsp' extra to capture camera frames.") from exc

    capture = cv2.VideoCapture(source)
    try:
        if not capture.isOpened():
            raise RuntimeError("Unable to open the approved RTSP camera source.")
        captured, frame = capture.read()
        if not captured:
            raise RuntimeError("Unable to read a frame from the approved RTSP camera source.")
        encoded, image = cv2.imencode(".jpg", frame)
        if not encoded:
            raise RuntimeError("Unable to encode the camera frame as JPEG.")
        return image.tobytes()
    finally:
        capture.release()
