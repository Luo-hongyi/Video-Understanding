from typing import List, Optional, Dict
from classes.EventFactory import Event
from classes.Segment import Segment
from collections import defaultdict
from openai import OpenAI

SYSTEM_PROMPT = '''
你是一个故事线总结者，你的任务是将用户提供给你的故事线简短的总结为2～3个句子，包括故事线的所有主要内容。你的总结不得超过50个字。
'''

class StoryNode:
    def __init__(self, event: Event, next: Optional['StoryNode'] = None, side: Optional[List['StoryNode']] = None):
        self.event = event
        self.next = next
        self.side = side if side is not None else []
        self.height = 1
        self.cumulative_particularity = event.particularity
        self.root_summary = ""

class StoryPool:
    def __init__(self, segments: List[Segment]):
        self.events: Dict[int, List[Event]] = defaultdict(list)
        self.roots: Dict[int, List[StoryNode]] = {}

        # 使用事件列表初始化
        for segment in segments:
            self.events[segment.id] = segment.events

        # 生成故事线
        self.generate_story_lines()

        # 更新节点属性
        self.update_node_properties()

        # 生成摘要
        self.generate_summaries()

    def generate_story_lines(self):
        ongoing_nodes = []

        for segment_id in sorted(self.events.keys()):
            current_events = self.events[segment_id]

            # 将所有当前事件转换为故事节点，并按particularity排序
            current_nodes = sorted(
                [StoryNode(event) for event in current_events],
                key=lambda node: node.event.particularity,
                reverse=True
            )

            if not ongoing_nodes:
                # 如果没有正在进行的事件，将所有当前事件设为根节点
                self.roots[segment_id] = current_nodes
                ongoing_nodes = current_nodes
                continue

            new_ongoing_nodes = []
            unmatched_nodes = []

            for current_node in current_nodes:
                matched = False
                for ongoing_node in ongoing_nodes:
                    if current_node.event.cause_event_id == ongoing_node.event.id:
                        matched = True
                        if not ongoing_node.next:
                            ongoing_node.next = current_node
                        else:
                            ongoing_node.side.append(current_node)
                            if segment_id not in self.roots:
                                self.roots[segment_id] = []
                            if current_node not in self.roots[segment_id]:
                                self.roots[segment_id].append(current_node)
                        if current_node not in new_ongoing_nodes:
                            new_ongoing_nodes.append(current_node)

                if not matched:
                    unmatched_nodes.append(current_node)

            # 将未匹配的当前事件添加为新的根节点
            if unmatched_nodes:
                if segment_id not in self.roots:
                    self.roots[segment_id] = []
                self.roots[segment_id].extend(unmatched_nodes)
                new_ongoing_nodes.extend(unmatched_nodes)

            ongoing_nodes = new_ongoing_nodes

    def update_node_properties(self):
        for root_nodes in self.roots.values():
            for root in root_nodes:
                self._update_node(root)

    def _update_node(self, node: StoryNode):
        # 计算高度
        max_side_height = 0
        for side_node in node.side:
            side_height = self._update_node(side_node)
            max_side_height = max(max_side_height, side_height)

        if node.next:
            next_height = self._update_node(node.next)
            node.height = max(next_height, max_side_height) + 1
        else:
            node.height = max_side_height + 1

        # 计算累积特殊性
        node.cumulative_particularity = node.event.particularity

        if node.next:
            node.cumulative_particularity += node.next.cumulative_particularity

        for side_node in node.side:
            node.cumulative_particularity += side_node.cumulative_particularity

        return node.height

    def print_story_lines(self):
        for segment_id, roots in self.roots.items():
            print(f"Segment {segment_id} story lines:")
            for root in roots:
                self._print_story_line(root, 0, is_side=False)
            print()  # 在每个segment的故事线之间添加一个空行

    def _print_story_line(self, node, depth, is_side=False):
        indent = "  " * depth
        arrow = "支线" if is_side else "->"
        print(f"{indent}{arrow} [Segment {node.event.parent_segment_id}, Time {node.event.current_time}] {node.event.description} (ID: {node.event.id}, Cumulative Particularity: {node.cumulative_particularity:.2f})")

        if node.next:
            self._print_story_line(node.next, depth + 1, is_side=False)

        for side_node in node.side:
            self._print_story_line(side_node, depth + 1, is_side=True)

    def get_story_line_string(self, segment_id, root_index):
        if segment_id not in self.roots or root_index >= len(self.roots[segment_id]):
            return f"No story line found for Segment {segment_id}, Root Index {root_index}"

        root = self.roots[segment_id][root_index]
        return self._get_story_line_string(root)

    def _get_story_line_string(self, node, depth=0, is_side=False):
        indent = "  " * depth
        arrow = "支线" if is_side else "->"
        line = f"{indent}{arrow} [Segment {node.event.parent_segment_id}, Time {node.event.current_time}] {node.event.description} (ID: {node.event.id}, Particularity: {node.event.particularity:.2f}, Cumulative Particularity: {node.cumulative_particularity:.2f})\n"

        if node.next:
            line += self._get_story_line_string(node.next, depth + 1, is_side=False)

        for side_node in node.side:
            line += self._get_story_line_string(side_node, depth + 1, is_side=True)

        return line

    def get_story_head_string(self, segment_id, root_index):
        if segment_id not in self.roots or root_index >= len(self.roots[segment_id]):
            return f"No story line found for Segment {segment_id}, Root Index {root_index}"

        node = self.roots[segment_id][root_index]
        return node.event.description

    def generate_summary(self, descriptions: str) -> str:
        sys_prompt = SYSTEM_PROMPT
        user_prompt = descriptions
        prompt = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.get_response(prompt)

    def generate_summaries(self):
        for segment_id, root_nodes in self.roots.items():
            for root_index, root in enumerate(root_nodes):
                if not root.root_summary:
                    self._generate_summary_for_node(root, segment_id, root_index)

    def _generate_summary_for_node(self, node: StoryNode, segment_id: int, root_index: int) -> str:
        if node.root_summary:
            return node.root_summary

        if node.height == 1:
            node.root_summary = self._format_event_description(node.event)
            return node.root_summary

        story_descriptions = []
        current = node
        while current:
            story_descriptions.append(self._format_event_description(current.event))

            # 处理当前节点的所有支线
            for side_index, side_node in enumerate(current.side):
                side_summary = self._generate_summary_for_node(side_node, segment_id, root_index)
                story_descriptions.append(f"在时间 {current.event.current_time} 发生了支线：[支线概要：{side_summary}]")

            if current.next and current.next.root_summary:
                story_descriptions.append(current.next.root_summary)
                break

            current = current.next

        # 生成总结
        prompt = f"请总结以下事件序列：\n" + "\n".join(story_descriptions)
        node.root_summary = f"[时间 {node.event.start_time}  类型{node.event.event_type}]" + self.generate_summary(prompt)
        return node.root_summary

    def _format_event_description(self, event: Event) -> str:
        return f"[时间 {event.current_time}] {event.description}"

    def get_response(self, messages):
        openai_model = OpenAI(api_key="")
        response = openai_model.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.5
        )
        return response.choices[0].message.content
