import cv2
import torch
import os
from typing import List, Tuple
import json


def annotate_frame(frame_path: str, output_dir: str, yolo_model, conf: float = 0.5):
    """
    Run YOLOv8 detection on an image, draw annotations, and save the result.

    :param frame_path: Input image path
    :param output_dir: Output directory for annotated images
    :param yolo_model: YOLOv8 model instance
    :param conf: Confidence threshold (default: 0.5)
    :return: Path to the annotated image
    """

    os.makedirs(output_dir, exist_ok=True)

    img = cv2.imread(frame_path)
    if img is None:
        print(f"Error: Unable to read image at {frame_path}")
        return None

    results = yolo_model.predict(
        source=img,
        line_width=1,
        show=True,
        conf=conf,
        agnostic_nms=True
    )

    output_path = os.path.join(output_dir, os.path.basename(frame_path))

    results[0].plot(line_width=1, filename=output_path, save=True)

    return output_path
