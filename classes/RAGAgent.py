from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from classes.VectorStore import VectorStore
from typing import List
from classes.Segment import Segment
from classes.StoryTree import StoryPool
from utils.ai import get_chat_model
import logging
import os

SYSTEM_PROMPT = '''
You are an agent for a video understanding system. The video has been split into segments and each segment has been converted to text. Your task is to call different tools to perform RAG-style search and answer the user's question.
You can use the following modes:
1. Storyline mode: Return storylines formed by linked events, including causes and developments. The query is compared with the storyline summaries. Storylines may have branches representing extensions or impacts.
2. Event mode: Return the most similar standalone events, including event descriptions and participating targets.
3. Target mode: Return the most similar targets, including detailed target descriptions and the events they belong to. Prefer other modes unless the user directly describes target features.
4. Segment lookup: Use the segment index from other results to inspect a specific segment's content.
5. Segment summary: Return concise descriptions of all segments.
6. Storyline summary: Return concise descriptions of all storylines (including all events). You may omit storylines with zero importance.

— Workflow —
1) Understand the available search modes.
2) Identify the user's intent and call appropriate tools.
3) Synthesize and answer concisely.

— Notes —
1) Use the filter dict carefully to restrict to specific types of storylines, events, or targets.
2) Use use_filter to enable/disable filters.
3) Results may be repetitive; summarize and reason before answering.
4) At most four tool calls.
5) Consider using a timeline style in outputs and omit redundancy.
6) Times are seconds from video start; convert to mm:ss format in answers.

— Filter Info —
Target types: {valid_labels}
Event types: {event_types}

— Extra Info —
Search mode: {mode}
When empty, you should autonomously search until you can answer.
Focus labels: {labels}
Map focus labels to provided types when needed.
'''

class Agent:
    def __init__(self, vectorstore: VectorStore, segments: List[Segment], story_pool: StoryPool, target_factory, event_factory):
        # Model
        self.model = get_chat_model(model="gpt-4o", temperature=0.5)

        # State
        self.database = VectorStore()
        self.database.build_by_vectorstore(vectorstore)
        self.segments = segments
        self.story_pool = story_pool

        self.target_factory = target_factory
        self.event_factory = event_factory
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialized Agent with %d segments and %d storyline roots", len(self.segments), len(self.story_pool.roots))

        # Tools as closures capturing instance state
        def _storyline_search(query: str, top_k: int = 1, filter: dict = None, use_filter: bool = False):
            self.logger.debug("tool:vector_search_storylines query=%r top_k=%s use_filter=%s filter=%s", query, top_k, use_filter, filter)
            if not use_filter:
                filter = None
            results = self.database.search_story(query, top_k=top_k, filter=filter, rerank=True)
            out = []
            for r in results:
                out.append(
                    "\n".join(
                        [
                            f"Storyline summary: {r.page_content}",
                            f"Storyline root segment index: {r.metadata['segment_id']}",
                            f"Storyline root index in segment: {r.metadata['root_index']}",
                            f"Full storyline: {r.metadata['whole_story']}\n",
                        ]
                    )
                )
            return "\n".join(out)

        def _segment_lookup(index: int):
            self.logger.debug("tool:index_search_segment index=%s", index)
            return self.segments[index - 1]

        def _event_search(query: str, top_k: int = 3, filter: dict = None, use_filter: bool = False):
            self.logger.debug("tool:vector_search_events query=%r top_k=%s use_filter=%s filter=%s", query, top_k, use_filter, filter)
            if not use_filter:
                filter = None
            results = self.database.search_event(query, top_k=top_k, filter=filter, rerank=True)
            out = []
            for r in results:
                out.append(f"Event segment index: {r.metadata['segment_id']}\nEvent: {r.page_content}\n")
            return "\n".join(out)

        def _segments_summary():
            self.logger.debug("tool:summary_segments count=%s", len(self.segments))
            out = []
            for idx, seg in enumerate(self.segments):
                out.append(
                    f"Segment index: {idx + 1}\nSegment start time: {seg.start_time}\nSegment content: {seg}\n"
                )
            return "\n".join(out)

        def _storylines_summary():
            self.logger.debug("tool:summary_story_lines roots=%s", len(self.story_pool.roots))
            out = []
            for segment_id, story_list in self.story_pool.roots.items():
                for story in story_list:
                    out.append(
                        f"Segment index: {segment_id}\n"
                        f"Storyline start time: {story.event.start_time}\n"
                        f"Storyline importance: {story.cumulative_particularity}\n"
                        f"Storyline summary: {story.root_summary}\n"
                    )
            return "\n".join(out)

        def _target_search(query: str, top_k: int = 3, filter: dict = None, use_filter: bool = False):
            self.logger.debug("tool:vector_search_targets query=%r top_k=%s use_filter=%s filter=%s", query, top_k, use_filter, filter)
            if not use_filter:
                filter = None
            results = self.database.search_target(query, top_k=top_k, filter=filter)
            out = []
            for r in results:
                text = [f"Target: {r.page_content}"]
                parent_event_id = r.metadata['parent_event_id']
                segment_id = r.metadata['segment_id']
                if parent_event_id != "-1":
                    events = self.segments[segment_id - 1].events
                    for ev in events:
                        if ev.id == parent_event_id:
                            text.append(f"Target's event: {str(ev)}\n")
                            break
                out.append("\n".join(text))
            return "\n".join(out)

        tools = [
            Tool.from_function(name="vector_search_storylines", description="Search similar storylines.", func=_storyline_search),
            Tool.from_function(name="index_search_segment", description="Lookup a segment by index.", func=_segment_lookup),
            Tool.from_function(name="vector_search_events", description="Search similar events.", func=_event_search),
            Tool.from_function(name="vector_search_targets", description="Search similar targets.", func=_target_search),
            Tool.from_function(name="summary_segments", description="Summarize all segments.", func=_segments_summary),
            Tool.from_function(name="summary_story_lines", description="Summarize all storylines.", func=_storylines_summary),
        ]

        self.react_agent = create_react_agent(model=self.model, tools=tools)

    def search(self, query: str, mode: str, labels: str):
        valid_labels = str(self.target_factory.valid_labels)
        event_types = str(self.event_factory.event_types)
        sys_prompt = SYSTEM_PROMPT.format(
            valid_labels=valid_labels,
            event_types=event_types,
            mode=mode,
            labels=labels
        )
        user_prompt = f"{query}"
        messages = {
            "messages": [
                ("system", sys_prompt),
                ("user", user_prompt)
            ]
        }
        response = self.react_agent.invoke(messages)
        return response
