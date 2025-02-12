from typing import List
from classes.Segment import Segment
import os
import re

def generate_segments(frames_dir: str, frames_per_segment: int = 20) -> List[Segment]:
    """
    从视频帧目录中生成段列表，每个段包含指定数量的帧。

    :param frames_dir: 视频帧目录的路径
    :param frames_per_segment: 每个段包含的帧数，默认为5
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

    # 遍历帧文件，每frames_per_segment个帧创建一个段
    for i in range(0, len(frame_files), frames_per_segment):
        # 获取当前段的帧文件
        segment_frames = frame_files[i:i+frames_per_segment]
        
        # 如果是最后一个段，可能不足frames_per_segment帧
        if len(segment_frames) < frames_per_segment:
            continue  # 跳过不足frames_per_segment帧的最后一个段

        # 计算段的起始和结束时间
        # 假设帧文件名格式为 "frame_xxxx.jpg"，其中xxxx是帧号
        start_frame = int(segment_frames[0].split('frame_')[1].split('.')[0])
        end_frame = int(segment_frames[-1].split('frame_')[1].split('.')[0])
        
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

