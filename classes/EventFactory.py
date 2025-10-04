from typing import List, Dict, Any
from classes.TargetFactory import Target
import json
import uuid


class Event:
    def __init__(self,
                 event_id: str,
                 event_type: str,
                 start_time: float,
                 current_time: float,
                 target_ids: List[str],
                 description: str,
                 particularity: int,
                 cause: str,
                 cause_event_id: str,
                 parent_segment_id: str):
        self.id = event_id
        self.event_type = event_type
        self.start_time = start_time
        self.current_time = current_time
        self.target_ids = target_ids
        self.targets: List[Target] = []
        self.description = description
        self.particularity = particularity
        self.cause = cause
        self.cause_event_id = cause_event_id
        self.parent_segment_id = parent_segment_id

    def __str__(self):
        return (f"event_id={self.id}, "
                f"event_type={self.event_type}, "
                f"start_time={self.start_time}, "
                f"targets=[{', '.join(str(t) for t in self.targets)}], "
                f"description='{self.description}', "
                f"cause='{self.cause}'")

    def get_description(self) -> str:
        return self.description

    def get_id(self) -> str:
        return self.id

    def get_event_type(self) -> str:
        return self.event_type

    def get_start_time(self) -> float:
        return self.start_time

    def get_current_time(self) -> float:
        return self.current_time

    def get_target_ids(self) -> List[str]:
        return self.target_ids.copy()

    def get_targets(self) -> List[Target]:
        return self.targets.copy()

    def set_targets(self, targets: List[Target]):
        self.targets = targets

    def add_target(self, target: Target):
        self.targets.append(target)

    def remove_target(self, target_id: str):
        self.targets = [t for t in self.targets if t.get_id() != target_id]
        self.target_ids.remove(target_id)

    @staticmethod
    def find_targets(target_ids: List[str], all_targets: List[Target]) -> List[Target]:
        return [target for target in all_targets if target.get_id() in target_ids]

    def update_targets(self, all_targets: List[Target]):
        self.targets = self.find_targets(self.target_ids, all_targets)

    def get_cause(self) -> str:
        return self.cause

    def set_cause(self, cause: str):
        self.cause = cause


class EventFactory:
    def __init__(self, event_types: Dict[str, str]):
        self.event_types = event_types

    @classmethod
    def from_config(cls, config_path: str) -> 'EventFactory':
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        event_types = config.get('event_types', {})
        return cls(event_types)

    def create_event(self, event_id: str, event_type: str, start_time: float,
                     target_ids: List[str], description: str, particularity: int, cause: str,
                     target_list: List[Target], cause_event_id: str,
                     segment_id: str) -> Event:
        if event_type not in self.event_types:
            raise ValueError(f"Unsupported event type: {event_type}")

        event = Event(
            event_id=event_id,
            event_type=event_type,
            start_time=start_time,
            current_time=0.0,  # initialize current time as 0
            target_ids=target_ids,
            description=description,
            particularity=particularity,
            cause=cause,
            cause_event_id=cause_event_id,
            parent_segment_id=segment_id
        )

        # Find matching targets from the provided target_list
        matching_targets = [target for target in target_list if target.get_label() in target_ids]

        # Extra handling (to be improved): set reverse link
        for target in matching_targets:
            target.parent_event_id = event_id

        event.set_targets(matching_targets)

        return event

    def create_events_from_json(self, json_file_path: str, segment_id: str, target_list: List[Target] = None) -> List[Event]:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            events_data = data.get("events", [])

        events = []

        for event_data in events_data:
            # Validate required fields
            required_fields = ['event_id', 'event_type', 'start_time', 'target_ids', 'description', 'particularity', 'cause', 'cause_event_id']
            for field in required_fields:
                if field not in event_data:
                    raise ValueError(f"Missing required field in JSON for event: {field}")

            # Validate event type
            if event_data['event_type'] not in self.event_types:
                raise ValueError(f"Unsupported event type: {event_data['event_type']}")

            # Create Event instance
            event = Event(
                event_id=event_data['event_id'],
                event_type=event_data['event_type'],
                start_time=event_data['start_time'],
                current_time=float(event_data.get('current_time', 0.0)),  # default to 0.0 if not provided
                target_ids=event_data['target_ids'],
                description=event_data['description'],
                particularity=event_data['particularity'],
                cause=event_data['cause'],
                cause_event_id=event_data['cause_event_id'],
                parent_segment_id=segment_id
            )

            # Find matching targets from the provided target_list
            if target_list is not None:
                matching_targets = [target for target in target_list if target.get_id() in event_data['target_ids']]
                # Extra handling (to be improved): set reverse link
                for target in matching_targets:
                    target.parent_event_id = event_data['event_id']
                event.set_targets(matching_targets)

            events.append(event)

        return events

    def get_event_types(self) -> List[str]:
        return list(self.event_types.keys())

    def get_event_type_descriptions(self) -> str:
        return self.event_types
