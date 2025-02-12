from classes.EventFactory import EventFactory
from classes.TargetFactory import TargetFactory
from classes.Segment import Segment
from typing import List
import os
import json

def fill_segments(segments: List[Segment], event_factory: EventFactory, target_factory: TargetFactory, video_name: str):
    for segment in segments:
        segment_file_path = f"{video_name}/segment_analysis/segment_{segment.id}.json"

        if not os.path.exists(segment_file_path):
            print(f"Error: File not found for segment {segment.id}")
            break  # 立即终止循环

        try:
            with open(segment_file_path, 'r') as file:
                segment_data = json.load(file)
                targets_data = target_factory.create_targets_from_json(json_file_path=segment_file_path, segement_id=segment.id)
                events_data = event_factory.create_events_from_json(json_file_path=segment_file_path, target_list=targets_data, segment_id=segment.id)
                summary = segment_data.get("summary", "")
                
                ###额外处理，后续优化###
                for event in events_data:
                    event.current_time = segment.start_time

                segment.set_summary(summary)
                segment.set_targets(targets_data)
                segment.set_events(events_data)



        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in file for segment {segment.id}")
            break