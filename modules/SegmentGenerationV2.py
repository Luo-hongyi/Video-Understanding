from typing import List
from classes.Segment import Segment
import os
import re

def generate_segments(frames_dir: str, frames_per_segment: int = 20, overlap_ratio: float = 0.5) -> List[Segment]:
    """
    从视频帧目录中生成段列表，每个段包含指定数量的帧，相邻段之间有指定比例的帧重叠。

    :param frames_dir: 视频帧目录的路径
    :param frames_per_segment: 每个段包含的帧数，默认为20
    :param overlap_ratio: 相邻段之间的重叠比例，默认为0.5（50%重叠）
    :return: 生成的段列表
    """
    # 确保视频帧目录存在
    if not os.path.exists(frames_dir):
        raise FileNotFoundError(f"Frames directory not found: {frames_dir}")

    # 获取视频帧文件列表
    frame_files = [f for f in os.listdir(frames_dir) if os.path.isfile(os.path.join(frames_dir, f))]

    # 按文件名排序
    frame_files.sort()

    # 创建段列表
    segments = []

    # 初始化段的ID
    segment_id = 1

    # 计算每次移动的帧数
    step = int(frames_per_segment * (1 - overlap_ratio))
    if step < 1:
        step = 1

    # 遍历帧文件，每次移动指定步长
    for i in range(0, len(frame_files) - frames_per_segment + 1, step):
        # 获取当前段的帧文件
        segment_frames = frame_files[i:i+frames_per_segment]
        
        # 计算段的起始和结束时间
        # 假设帧文件名格式为 "frame_xxxx.jpg"，其中xxxx是帧号
        start_frame = int(re.search(r'frame_(\d+)', segment_frames[0]).group(1))
        end_frame = int(re.search(r'frame_(\d+)', segment_frames[-1]).group(1))
        
        # 假设每秒30帧，您可以根据实际情况调整这个值
        fps = 30
        start_time = start_frame / fps
        end_time = end_frame / fps

        # 创建完整的帧文件路径列表
        frame_paths = [os.path.join(frames_dir, f) for f in segment_frames]

        # 创建段对象
        segment = Segment(segment_id, start_time, end_time, frame_paths)

        # 添加段到段列表
        segments.append(segment)

        # 更新段ID
        segment_id += 1

    return segments