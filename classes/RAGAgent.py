from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from classes.VectorStore import VectorStore
from typing import List
from classes.Segment import Segment
from classes.StoryTree import StoryPool

#全局变量
database = VectorStore()
global_segments = None
global_story_pool = None

SYSTEM_PROMPT = '''
你是一个视频理解系统的智能体。现在，视频被切割为了多个片段，每个片段已经转换为了文本。你的任务是调用不同的工具接口完成RAG搜索来回答用户的提问。
你可以使用以下搜索模式：
1. 故事线模式：该方法会返回由多个事件连接而成的故事线，涵盖了事件的前因后果与发展，你的query会与故事线的总结进行对比。故事线会延伸出支线，代表的是事件的延伸或影响。
2. 事件模式：该方法会返回与query最相似的独立事件，包括事件的描述与事件的参与目标。
3. 目标模式：该方法会返回与query最相似的目标，包括目标的描述与目标所在的事件。除非用户直接描述目标的特征，否则你应该首先使用其他模式。
4. 片段搜索：其他搜索模式会返回一个片段序号，你可以通过这个方法了解特定片段的内容。
5. 片段总结：该方法会返回所有片段的简要描述。
6. 故事线总结：该方法会返回所有故事线（包括所有事件）的简要描述。你可以省略重要性为0的故事线。

---工作流程---
1. 首先，理解你可以进行的搜索模式。
2. 然后，识别用户的意图，调用合适的工具接口。
3. 最后，结合你获得的信息，简洁的回答用户的问题。

---注意---
1. 你应当谨慎使用filter字典来筛选特定类型的故事线、事件或目标。
2. 你可以使用use_filter来启用或禁用filter。
3. 你的搜索结果可能会包含大量重复信息，你需要进行总结与推理来回答用户。
4. 你最多进行四次工具调用。
5. 你可以考虑使用时间线的方式输出总结内容，注意省略重复与不必要的信息。
6. 搜索结果的时间信息为视频的第几秒，请将时间信息转换为mm:ss格式。

---filter信息---
目标类型：{valid_labels}
事件类型：{event_types}

---额外信息---
搜索模式：{mode}
搜索模式为空时，你应该自主进行多次搜索，直到你可以回答用户的问题。
关注标签：{labels}
用户关注的标签事件或者目标，你应该进行适当的转换至filter信息中提供的类型。
'''

class Agent:
    def __init__(self, vectorstore: VectorStore, segments: List[Segment], story_pool: StoryPool, target_factory, event_factory):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.5, api_key="")

        global global_segments, global_story_pool, database
        database.build_by_vectorstore(vectorstore)
        global_segments = segments
        global_story_pool = story_pool

        self.target_factory = target_factory
        self.event_factory = event_factory
        tools = [self.vector_search_storylines, self.index_search_segment, self.vector_search_events, self.vector_search_targets, self.summary_segments, self.summary_story_lines]
        self.react_agent = create_react_agent(model=self.model, tools=tools)

    @tool
    def vector_search_storylines(query: str, top_k: int, filter: dict, use_filter: bool):
        """
        故事线模式向量搜索，通过对比query与故事线总结的相似度，返回最接近的top_k个故事线，你可以使用filter字典来选定特定种类的故事。
        Args:
            query (str): 搜索的query，将被用于向量搜索。
            top_k (int): 返回的结果数量, 默认为1。
            filter (dict): {'type': 'xxx'}，筛选单个类型的故事线，type与event_type对应。如果不需要筛选，使用'None'。
            use_filter (bool): 是否使用filter, 仅在用户要求启用过滤时为True。
        Returns:
            list: 通过rag搜索返回top_k个故事线，包括每个故事线的总结与完整的故事线。完整的故事线包含故事线的主线，与在特定时刻延伸的支线。
        """
        if not use_filter:
            filter = None
        results = database.search_story(query, top_k=top_k, filter=filter, rerank=True)

        result_str = ""

        for result in results:
            result_str += f"故事线总结：{result.page_content}\n"
            result_str += f"故事线起点所在的片段序号：{result.metadata['segment_id']}\n"
            result_str += f"故事线起点所在的片段的事件序号：{result.metadata['root_index']}\n"
            result_str += f"完整故事线：{result.metadata['whole_story']}\n\n"

        return result_str

    @tool
    def index_search_segment(index: int):
        """
        通过片段序号搜索特定的片段。
        Args:
            index (int): 片段序号。
        Returns:
            str: 片段的内容, 包括片段包含的所有实体与事件。
        """
        return global_segments[index - 1]

    @tool
    def vector_search_events(query: str, top_k: int, filter: dict, use_filter: bool):
        """
        事件模式向量搜索，通过对比query与事件的相似度，返回最接近的top_k个事件，你可以使用filter字典来选定特定种类的事件。
        Args:
            query (str): 搜索的query，将被用于向量搜索。
            top_k (int): 返回的结果数量, 默认为3。
            filter (dict): {'type': 'xxx'}，筛选单个类型的事件，type与event_type对应。如果不需要筛选，使用'None'。
            use_filter (bool): 是否使用filter, 仅在用户要求启用过滤时为True。
        Returns:
            list: 通过rag搜索返回top_k个事件，包括完整的事件与参与事件的目标的详细描述。
        """
        if not use_filter:
            filter = None
        results = database.search_event(query, top_k=top_k, filter=filter, rerank=True)

        result_str = ""

        for result in results:
            result_str += f"事件所在的片段序号：{result.metadata['segment_id']}\n"
            result_str += f"事件：{result.page_content}\n\n"

        return result_str

    @tool
    def summary_segments():
        """
        返回所有片段的简要描述。
        Returns:
            str: 所有片段的简要描述。
        """
        result_str = ""
        for index, segment in enumerate(global_segments):
            result_str += f"片段序号：{index + 1}\n"
            result_str += f"片段时间：{segment.start_time}\n"
            result_str += f"片段描述：{segment}\n\n"
        return result_str

    @tool
    def summary_story_lines():
        """
        返回所有故事线的简要描述。当你被问到总结事件时，你可以使用这个方法来回答。
        Returns:
            str: 所有故事线的简要描述。
        """
        result_str = ""
        for segment_id, story_list in global_story_pool.roots.items():
            for story in story_list:
                result_str += f"片段序号：{segment_id}\n"
                result_str += f"故事线起始时间：{story.event.start_time}\n"
                result_str += f"故事线重要性：{story.cumulative_particularity}\n"
                result_str += f"故事线总结：{story.root_summary}\n\n"
        return result_str

    @tool
    def vector_search_targets(query: str, top_k: int, filter: dict, use_filter: bool):
        """
        目标模式向量搜索，通过对比query与目标的相似度，返回最接近的top_k个目标，你可以使用filter字典来选定特定种类的目标。
        Args:
            query (str): 搜索的query，将被用于向量搜索。
            top_k (int): 返回的结果数量, 默认为3。
            filter (dict): {'type': 'xxx'}，筛选单个类型的目标，type与targets的valid_label对应。如果不需要筛选，使用'None'。
            use_filter (bool): 是否使用filter, 仅在用户要求启用过滤时为True。
        Returns:
            list: 通过rag搜索返回top_k个目标，包括目标的详细描述与目标所在的事件。
        """
        if not use_filter:
            filter = None
        results = database.search_target(query, top_k=top_k, filter=filter)

        result_str = ""

        for result in results:
            result_str += f"目标：{result.page_content}\n"

            parent_event_id = result.metadata['parent_event_id']
            segment_id = result.metadata['segment_id']

            if parent_event_id != "-1":
                events = global_segments[segment_id - 1].events
                for event in events:
                    if event.id == parent_event_id:
                        result_str += f"目标参与的事件：{str(event)}\n\n"
                        break
        return result_str

    def search(self, query: str, mode: str, labels: str):
        valid_labels =str(self.target_factory.valid_labels)
        event_types = str(self.event_factory.event_types)
        sys_prompt = SYSTEM_PROMPT.format(
            valid_labels=valid_labels,
            event_types=event_types,
            mode = mode,
            labels = labels
        )
        user_prompt = f"{query}"
        messages = {
            "messages":[
                ("system", sys_prompt),
                ("user", user_prompt)
            ]
        }
        response = self.react_agent.invoke(messages)
        return response