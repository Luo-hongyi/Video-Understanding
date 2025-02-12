import os
from typing import List

def get_all_file_paths(directory: str) -> List[str]:
    """
    读取指定文件夹中所有文件的路径。

    :param directory: 要读取的文件夹路径
    :return: 包含所有文件完整路径的列表
    """
    file_paths = []
    
    # 检查目录是否存在
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return file_paths

    # 遍历目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 构造完整文件路径
            full_path = os.path.join(root, file)
            file_paths.append(full_path)
    
    return file_paths