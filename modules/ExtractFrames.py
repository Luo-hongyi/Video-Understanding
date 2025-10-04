import cv2
import os
import numpy as np


def extract_frames(video_path: str, output_dir: str, interval: float = 1.0):
    """
    Extract a frame every n seconds from a video and save as images.

    :param video_path: Path to input video
    :param output_dir: Output directory for images
    :param interval: Interval in seconds (default: 1.0)
    :return: List of saved image file paths
    """
    os.makedirs(output_dir, exist_ok=True)

    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frames_to_skip = int(fps * interval)

    frame_count = 0
    saved_frames = []

    while True:
        success, frame = video.read()
        if not success:
            break

        if frame_count % frames_to_skip == 0:
            output_filename = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
            cv2.imwrite(output_filename, frame)
            saved_frames.append(output_filename)
            print(f"Saved frame: {output_filename}")

        frame_count += 1

    video.release()
    return saved_frames
