from typing import List
from classes.Segment import Segment
import os
import re


def generate_segments(frames_dir: str, frames_per_segment: int = 20, overlap_ratio: float = 0.5) -> List[Segment]:
    """
    Generate segments from frames with overlap between consecutive segments.

    :param frames_dir: Path to the video frames directory
    :param frames_per_segment: Number of frames per segment (default: 20)
    :param overlap_ratio: Ratio of overlapping frames between segments (default: 0.5)
    :return: List of generated Segment objects
    """
    if not os.path.exists(frames_dir):
        raise FileNotFoundError(f"Frames directory not found: {frames_dir}")

    frame_files = [f for f in os.listdir(frames_dir) if os.path.isfile(os.path.join(frames_dir, f))]
    frame_files.sort()

    segments = []
    segment_id = 1

    # Step size according to overlap
    step = int(frames_per_segment * (1 - overlap_ratio))
    if step < 1:
        step = 1

    # Slide window and build segments
    for i in range(0, len(frame_files) - frames_per_segment + 1, step):
        segment_frames = frame_files[i:i + frames_per_segment]

        # Compute start/end time assuming filename pattern "frame_xxxx"
        start_frame = int(re.search(r'frame_(\d+)', segment_frames[0]).group(1))
        end_frame = int(re.search(r'frame_(\d+)', segment_frames[-1]).group(1))
        fps = 30
        start_time = start_frame / fps
        end_time = end_frame / fps

        frame_paths = [os.path.join(frames_dir, f) for f in segment_frames]
        segment = Segment(segment_id, start_time, end_time, frame_paths)
        segments.append(segment)
        segment_id += 1

    return segments
