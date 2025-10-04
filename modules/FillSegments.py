from classes.EventFactory import EventFactory
from classes.TargetFactory import TargetFactory
from classes.Segment import Segment
from typing import List
import os
import json
import logging

logger = logging.getLogger(__name__)


def fill_segments(segments: List[Segment], event_factory: EventFactory, target_factory: TargetFactory, video_name: str):
    errors = []
    for segment in segments:
        segment_file_path = f"{video_name}/segment_analysis/segment_{segment.id}.json"

        if not os.path.exists(segment_file_path):
            msg = f"File not found for segment {segment.id}: {segment_file_path}"
            logger.error(msg)
            errors.append((segment.id, msg))
            continue

        try:
            with open(segment_file_path, 'r', encoding='utf-8') as file:
                segment_data = json.load(file)
                targets_data = target_factory.create_targets_from_json(json_file_path=segment_file_path, segement_id=segment.id)
                events_data = event_factory.create_events_from_json(json_file_path=segment_file_path, target_list=targets_data, segment_id=segment.id)
                summary = segment_data.get("summary", "")

                # Extra handling (to be improved): propagate segment time as current_time
                for event in events_data:
                    event.current_time = segment.start_time

                segment.set_summary(summary)
                segment.set_targets(targets_data)
                segment.set_events(events_data)

        except json.JSONDecodeError as e:
            msg = f"Invalid JSON for segment {segment.id}: {e}"
            logger.error(msg)
            errors.append((segment.id, msg))
            continue

    if errors:
        logger.warning("FillSegments completed with %d error(s).", len(errors))
        for sid, emsg in errors:
            logger.warning("segment=%s error=%s", sid, emsg)
