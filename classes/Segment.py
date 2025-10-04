from typing import List, Optional
from classes.TargetFactory import Target
from classes.EventFactory import Event
from base64 import b64encode
import os


class Segment:
    def __init__(self, segment_id: str, start_time: float, end_time: float, image_paths: Optional[List[str]] = None):
        self.id = segment_id
        self.start_time = start_time
        self.end_time = end_time
        self.images: List[str] = []
        self.targets: List[Target] = []
        self.events: List[Event] = []
        self.summary: str = ""

        if image_paths:
            for path in image_paths:
                self.add_image(path)

    def add_image(self, image_path: str):
        if not os.path.exists(image_path):
            print(f"Warning: Image file not found at {image_path}")
            return

        try:
            with open(image_path, "rb") as image_file:
                encoded_string = b64encode(image_file.read()).decode('utf-8')
                self.images.append(encoded_string)
        except Exception as e:
            print(f"Error adding image {image_path}: {str(e)}")

    def set_targets(self, targets: List[Target]):
        self.targets = targets

    def set_events(self, events: List[Event]):
        self.events = events

    def set_summary(self, summary: str):
        self.summary = summary

    def get_images(self):
        return self.images

    def __str__(self):
        return (f"Segment(id={self.id}, start={self.start_time}, end={self.end_time}, "
                f"images_count={len(self.images)}, "
                f"targets=[{', '.join(str(t) for t in self.targets)}], "
                f"events=[{', '.join(str(e) for e in self.events)}], "
                f"summary='{self.summary}')")
