import json
from typing import List

class Target:
    '''识别目标类'''
    def __init__(self, id: str, label: str, features: dict, time: int = 0, parent_segment_id: str = None):
        self.id = id # 四位数字的ID
        self.parent_segment_id = parent_segment_id # 所属片段ID
        self.parent_event_id = None # 所属事件ID
        self.label = label # 目标标签
        self.features = features # 目标特征字典
        self.time = time # 目标时间戳

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
    '''识别目标的生产工厂'''
    @classmethod
    def from_config(cls, config_file):
        '''从一个配置文件初始化一个TargetFactory对象'''
        with open(config_file, 'r') as f:
            config = json.load(f)
        return cls(config['valid_labels'], 
                   config['feature_requirements'], 
                   config['feature_descriptions'])

    def __init__(self, valid_labels: list, feature_requirements: dict, feature_descriptions: dict):
        self.valid_labels = valid_labels  # 目标标签列表
        self.feature_requirements = feature_requirements  # 目标特征要求字典
        self.feature_descriptions = feature_descriptions  # 目标特征描述字典

    def create_target(self, id: str, label: str, features: dict, segment_id: str, time: int = 0) -> Target:
        if label not in self.valid_labels:
            raise ValueError(f"Invalid label: {label}")
        
        required_features = self.get_required_features(label)
        for feature in required_features:
            if feature not in features:
                raise ValueError(f"Missing required feature for {label}: {feature}")
        
        return Target(id, segment_id, label, features, time)

    def create_targets_from_json(self, json_file_path: str, segement_id: str) -> List[Target]:
        """
        从指定的 JSON 文件创建多个 Target 实例。

        :param json_file_path: JSON 文件的路径
        :return: 创建的 Target 实例列表
        """
        with open(json_file_path, 'r') as file:
            targets_data = json.load(file).get("targets", [])

        if not isinstance(targets_data, list):
            raise ValueError("The 'targets' field in the JSON file should be a list")

        targets = []
        for target_data in targets_data:
            # 验证必需的字段
            required_fields = ['id', 'label', 'features']
            for field in required_fields:
                if field not in target_data:
                    raise ValueError(f"Missing required field in JSON for a target: {field}")

            # 验证标签
            #if target_data['label'] not in self.valid_labels:
                #raise ValueError(f"Invalid label: {target_data['label']}")

            # 验证特征
            required_features = self.get_required_features(target_data['label'])
            for feature in required_features:
                if feature not in target_data['features']:
                    raise ValueError(f"Missing required feature for {target_data['label']}: {feature}")

            # 创建 Target 实例并添加到列表
            target = Target(
                id=target_data['id'],
                parent_segment_id=segement_id,
                label=target_data['label'],
                features=target_data['features'],
                time=target_data.get('time', 0)  # 如果没有提供 time，默认为 0
            )
            targets.append(target)

        return targets

    def get_valid_labels(self) -> list:
        return self.valid_labels.copy()

    def get_required_features(self, label: str) -> list:
        return self.feature_requirements.get(label, []).copy()

    def get_feature_descriptions(self, label: str) -> dict:
        return self.feature_descriptions.get(label, {}).copy()
    
    def get_fearures(self) -> dict:
        return self.feature_descriptions