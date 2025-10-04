from langchain_core.documents import Document
from classes.StoryTree import StoryPool
from classes.Segment import Segment
from typing import List


def load_stories(story_pool: StoryPool, use_summary: bool = False) -> List[Document]:
    """Build documents for storylines, using either full head or root summary."""
    docs = []
    for segment_id in story_pool.roots.keys():
        for root_index in range(len(story_pool.roots[segment_id])):
            story_line = story_pool.get_story_line_string(segment_id=segment_id, root_index=root_index)
            if use_summary:
                story_head = story_pool.roots[segment_id][root_index].root_summary
            else:
                story_head = story_pool.get_story_head_string(segment_id=segment_id, root_index=root_index)
            metadata = {
                "segment_id": segment_id,
                "root_index": root_index,
                "time": story_pool.roots[segment_id][root_index].event.current_time,
                "whole_story": story_line,
                "cumulative_particularity": story_pool.roots[segment_id][root_index].cumulative_particularity,
                "type": story_pool.roots[segment_id][root_index].event.event_type,
            }
            doc = Document(page_content=story_head, metadata=metadata)
            docs.append(doc)
    return docs


def load_targets(segments: List[Segment]) -> List[Document]:
    """Build documents for targets found in segments."""
    docs = []
    for segment in segments:
        for target in segment.targets:
            target_str = str(target)
            if target.parent_event_id is None:
                target.parent_event_id = "-1"
            metadata = {"segment_id": segment.id, "parent_event_id": target.parent_event_id, "time": target.time}
            doc = Document(page_content=target_str, metadata=metadata)
            docs.append(doc)
    return docs


def load_segments(segments: List[Segment]) -> List[Document]:
    """Build documents for raw segment content."""
    docs = []
    for segment in segments:
        segment_str = str(segment)
        metadata = {"segment_id": segment.id, "time": segment.start_time}
        doc = Document(page_content=segment_str, metadata=metadata)
        docs.append(doc)
    return docs


def load_events(segments: List[Segment]) -> List[Document]:
    """Build documents for events found in segments."""
    docs = []
    for segment in segments:
        for event in segment.events:
            event_str = str(event)
            metadata = {"segment_id": segment.id, "time": event.current_time, "particularity": event.particularity, "type": event.event_type}
            doc = Document(page_content=event_str, metadata=metadata)
            docs.append(doc)
    return docs
