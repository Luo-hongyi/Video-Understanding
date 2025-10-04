import os
from typing import List


def get_all_file_paths(directory: str) -> List[str]:
    """
    Read all file paths under the specified directory.

    :param directory: Directory to scan
    :return: List of absolute file paths
    """
    file_paths = []

    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return file_paths

    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            file_paths.append(full_path)

    return file_paths
