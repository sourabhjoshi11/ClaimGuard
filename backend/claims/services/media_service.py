import base64
import os
from typing import List

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def is_supported_media(path: str, media_type: str) -> bool:
    extension = os.path.splitext(path)[1].lower()
    allowed = VIDEO_EXTENSIONS if media_type == "video" else IMAGE_EXTENSIONS
    return extension in allowed


def _load_image_b64(path: str) -> str:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _extract_video_strip_b64(path: str) -> str:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "Video support requires opencv-python-headless and numpy to be installed"
        ) from exc

    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        raise ValueError("Unable to read video file")

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        capture.release()
        raise ValueError("Video contains no frames")

    target_indexes: List[int] = sorted(
        set([0, max(frame_count // 2, 0), max(frame_count - 1, 0)])
    )

    frames = []
    for frame_index in target_indexes:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok or frame is None:
            continue
        height, width = frame.shape[:2]
        if width > 960:
            scale = 960 / width
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        frames.append(frame)

    capture.release()

    if not frames:
        raise ValueError("Could not extract frames from video")

    strip = np.vstack(frames)
    ok, encoded = cv2.imencode(".jpg", strip)
    if not ok:
        raise ValueError("Failed to encode video preview")

    return base64.b64encode(encoded.tobytes()).decode("utf-8")


def media_to_base64_preview(path: str, media_type: str) -> str:
    if media_type == "video":
        return _extract_video_strip_b64(path)
    return _load_image_b64(path)
