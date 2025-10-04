from typing import List
from classes.Segment import Segment
import os
import re


def generate_segments(frames_dir: str, frames_per_segment: int = 20) -> List[Segment]:
    """
    Generate segments from a directory of frames, each containing a fixed number of frames.

    :param frames_dir: Path to the video frames directory
    :param frames_per_segment: Number of frames per segment (default: 20)
    :return: List of generated Segment objects
    """
    # Ensure the frames directory exists
    if not os.path.exists(frames_dir):
        raise FileNotFoundError(f"Frames directory not found: {frames_dir}")

    # Collect frame files and sort
    frame_files = [f for f in os.listdir(frames_dir) if os.path.isfile(os.path.join(frames_dir, f))]
    frame_files.sort()

    segments = []
    segment_id = 1

    # Create a segment for each chunk of frames_per_segment
    for i in range(0, len(frame_files), frames_per_segment):
        segment_frames = frame_files[i:i + frames_per_segment]

        # Skip incomplete last segment
        if len(segment_frames) < frames_per_segment:
            continue

        # Compute start/end time assuming filenames like "frame_xxxx.jpg" and 30 fps
        start_frame = int(segment_frames[0].split('frame_')[1].split('.')[0])
        end_frame = int(segment_frames[-1].split('frame_')[1].split('.')[0])
        fps = 30
        start_time = start_frame / fps
        end_time = end_frame / fps

        frame_paths = [os.path.join(frames_dir, f) for f in segment_frames]
        segment = Segment(segment_id, start_time, end_time, frame_paths)
        segments.append(segment)
        segment_id += 1

    return segments
