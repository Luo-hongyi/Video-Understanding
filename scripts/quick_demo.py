#!/usr/bin/env python3
import os
from glob import glob
from classes.TargetFactory import TargetFactory
from classes.EventFactory import EventFactory
from classes.Segment import Segment
from modules.FillSegments import fill_segments
from classes.StoryTree import StoryPool
from modules.Load import load_stories, load_targets, load_segments, load_events
from classes.VectorStore import VectorStore
from classes.RAGAgent import Agent


def build_segments_from_json(folder: str):
    """Create Segment objects inferred from existing segment JSON files."""
    files = sorted(glob(os.path.join(folder, "segment_analysis", "segment_*.json")))
    segments = []
    for path in files:
        name = os.path.basename(path)
        seg_id = int(name.split("_")[1].split(".")[0])
        # assume 10 seconds per segment for demo
        start_time = (seg_id - 1) * 10
        end_time = start_time + 10
        segments.append(Segment(seg_id, start_time, end_time, image_paths=None))
    return segments


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Please export your API key.")

    base = os.path.dirname(os.path.dirname(__file__))
    video_name = os.path.join(base, "accident1")

    target_factory = TargetFactory.from_config(os.path.join(video_name, "configs", "target_factory_config.json"))
    event_factory = EventFactory.from_config(os.path.join(video_name, "configs", "event_factory_config.json"))

    segments = build_segments_from_json(video_name)
    if not segments:
        raise RuntimeError("No segment JSON files found under accident1/segment_analysis")

    fill_segments(segments=segments, event_factory=event_factory, target_factory=target_factory, video_name=video_name)

    # Build storyline pool
    story_pool = StoryPool(segments)

    # Build docs
    story_docs = load_stories(story_pool, use_summary=True)
    event_docs = load_events(segments)
    target_docs = load_targets(segments)
    segment_docs = load_segments(segments)

    # Vector store
    vs = VectorStore()
    vs.build_by_param(story_docs, event_docs, target_docs, segment_docs, time_interval=60)

    # Agent and example query
    agent = Agent(vectorstore=vs, segments=segments, story_pool=story_pool, target_factory=target_factory, event_factory=event_factory)
    print("\n=== Quick Demo: Storyline search ===")
    res = agent.search(query="traffic accident near the intersection", mode="storyline", labels="car, accident")
    print(res)


if __name__ == "__main__":
    main()

