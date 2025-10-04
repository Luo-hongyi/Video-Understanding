import json
from typing import List


class Target:
    """Detected target entity."""

    def __init__(self, id: str, label: str, features: dict, time: int = 0, parent_segment_id: str = None):
        self.id = id  # four-digit ID
        self.parent_segment_id = parent_segment_id  # parent segment ID
        self.parent_event_id = None  # parent event ID
        self.label = label  # target label
        self.features = features  # target feature dict
        self.time = time  # timestamp

    def __str__(self):
        return f"Target(id={self.id}, label={self.label}, features={self.features}, time={self.time})"

    def get_id(self) -> str:
        return self.id

    def get_label(self):
        return self.label

    def get_features(self):
        return self.features

    def get_time(self):
        return self.time

    def set_label(self, new_label: str):
        self.label = new_label

    def set_time(self, new_time: int):
        self.time = new_time


class TargetFactory:
    """Factory for creating detected targets."""

    @classmethod
    def from_config(cls, config_file):
        """Initialize a TargetFactory from a JSON config file."""
        with open(config_file, 'r') as f:
            config = json.load(f)
        return cls(config['valid_labels'], config['feature_requirements'], config['feature_descriptions'])

    def __init__(self, valid_labels: list, feature_requirements: dict, feature_descriptions: dict):
        self.valid_labels = valid_labels  # available target labels
        self.feature_requirements = feature_requirements  # required features per label
        self.feature_descriptions = feature_descriptions  # feature descriptions per label

    def create_target(self, id: str, label: str, features: dict, segment_id: str, time: int = 0) -> Target:
        if label not in self.valid_labels:
            raise ValueError(f"Invalid label: {label}")

        required_features = self.get_required_features(label)
        for feature in required_features:
            if feature not in features:
                raise ValueError(f"Missing required feature for {label}: {feature}")

        # Fix argument order to match Target signature
        return Target(id=id, label=label, features=features, time=time, parent_segment_id=segment_id)

    def create_targets_from_json(self, json_file_path: str, segement_id: str) -> List[Target]:
        """Create multiple Target instances from a JSON file."""
        with open(json_file_path, 'r') as file:
            targets_data = json.load(file).get("targets", [])

        if not isinstance(targets_data, list):
            raise ValueError("The 'targets' field in the JSON file should be a list")

        targets = []
        for target_data in targets_data:
            # Validate required fields
            required_fields = ['id', 'label', 'features']
            for field in required_fields:
                if field not in target_data:
                    raise ValueError(f"Missing required field in JSON for a target: {field}")

            # Validate features
            required_features = self.get_required_features(target_data['label'])
            for feature in required_features:
                if feature not in target_data['features']:
                    raise ValueError(f"Missing required feature for {target_data['label']}: {feature}")

            # Create Target instance
            target = Target(
                id=target_data['id'],
                parent_segment_id=segement_id,
                label=target_data['label'],
                features=target_data['features'],
                time=target_data.get('time', 0)
            )
            targets.append(target)

        return targets

    def get_valid_labels(self) -> list:
        return self.valid_labels.copy()

    def get_required_features(self, label: str) -> list:
        return self.feature_requirements.get(label, []).copy()

    def get_feature_descriptions(self, label: str) -> dict:
        return self.feature_descriptions.get(label, {}).copy()

    # Keep legacy method name for backward compatibility
    def get_fearures(self) -> dict:  # noqa: D401 (legacy typo retained)
        """Return feature descriptions (legacy name)."""
        return self.feature_descriptions

    # Provide a correctly spelled alias for future use
    def get_features(self) -> dict:
        return self.feature_descriptions
