import cv2
import os
import numpy as np

def extract_frames(video_path: str, output_dir: str, interval: float = 1.0):
    """
    从视频中每隔n秒抽取一帧并保存为图像文件。

    :param video_path: 输入视频的路径
    :param output_dir: 输出图像的目录
    :param interval: 抽取帧的时间间隔（秒），默认为1秒
    :return: 保存的图像文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 打开视频文件
    video = cv2.VideoCapture(video_path)

    # 获取视频的FPS（每秒帧数）
    fps = video.get(cv2.CAP_PROP_FPS)

    # 计算需要跳过的帧数
    frames_to_skip = int(fps * interval)

    frame_count = 0
    saved_frames = []

    while True:
        # 读取一帧
        success, frame = video.read()

        if not success:
            break

        # 每隔指定帧数保存一帧
        if frame_count % frames_to_skip == 0:
            # 生成输出文件名
            output_filename = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
            
            # 保存图像
            cv2.imwrite(output_filename, frame)
            saved_frames.append(output_filename)
            print(f"Saved frame: {output_filename}")

        frame_count += 1

    # 释放视频对象
    video.release()

    return saved_frames
