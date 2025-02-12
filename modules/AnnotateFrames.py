import cv2
import torch
import os
from typing import List, Tuple
import json

def annotate_frame(frame_path: str, output_dir: str, yolo_model, conf: float = 0.5):
    """
    使用YOLOv8模型对图片进行目标检测并标注，然后保存标注后的图片。

    :param frame_path: 输入图片的路径
    :param output_dir: 输出标注后图片的目录
    :param yolo_model: YOLOv8模型实例
    :param conf: 置信度阈值，默认为0.5
    :return: 标注后图片的路径
    """

    os.makedirs(output_dir, exist_ok=True)

    # 读取图片
    img = cv2.imread(frame_path)
    if img is None:
        print(f"Error: Unable to read image at {frame_path}")
        return None

    # 进行目标检测
    results = yolo_model.predict(
        source=img,
        line_width=1,
        show=True,
        conf=conf,
        agnostic_nms=True
    )

    output_path = os.path.join(output_dir, os.path.basename(frame_path))

    results[0].plot(line_width = 1,filename = output_path, save = True)

    return output_path