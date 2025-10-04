from langchain_chroma import Chroma
from utils.ai import get_embeddings

class VectorStore:
    def __init__(self):
        self.story_docs = None
        self.event_docs = None
        self.target_docs = None
        self.segment_docs = None
        self.time_interval = None
        self.global_story_vectorstore = None
        self.global_event_vectorstore = None
        self.global_target_vectorstore = None
        self.global_segment_vectorstore = None

    def build_by_vectorstore(self, vectorstore):
        self.story_docs = vectorstore.story_docs
        self.event_docs = vectorstore.event_docs
        self.target_docs = vectorstore.target_docs
        self.segment_docs = vectorstore.segment_docs
        self.time_interval = vectorstore.time_interval
        self.global_story_vectorstore = vectorstore.global_story_vectorstore
        self.global_event_vectorstore = vectorstore.global_event_vectorstore
        self.global_target_vectorstore = vectorstore.global_target_vectorstore
        self.global_segment_vectorstore = vectorstore.global_segment_vectorstore

    def build_by_param(self, story_docs, event_docs, target_docs, segment_docs, time_interval: int = 60):
        self.story_docs = story_docs
        self.event_docs = event_docs
        self.target_docs = target_docs
        self.segment_docs = segment_docs
        self.time_interval = time_interval
        embedding = get_embeddings()
        self.global_story_vectorstore = Chroma.from_documents(documents=story_docs, embedding=embedding, collection_name="global_story_vectorstore")
        self.global_event_vectorstore = Chroma.from_documents(documents=event_docs, embedding=embedding, collection_name="global_event_vectorstore")
        self.global_target_vectorstore = Chroma.from_documents(documents=target_docs, embedding=embedding, collection_name="global_target_vectorstore")
        self.global_segment_vectorstore = Chroma.from_documents(documents=segment_docs, embedding=embedding, collection_name="global_segment_vectorstore")

    def search_story(self, query: str, top_k: int = 3, rerank: bool = False, filter: dict = None):
        search_kwargs = {"k": max(3, top_k * 2)}
        if filter:
            search_kwargs["filter"] = filter
        if not rerank:
            retriever = self.global_story_vectorstore.as_retriever(search_type="similarity", search_kwargs=search_kwargs)
            results = retriever.invoke(query)
            return results[:top_k]

        retriever = self.global_story_vectorstore.as_retriever(search_type="similarity", search_kwargs=search_kwargs)
        results = retriever.invoke(query)
        # Rerank results by cumulative particularity
        sorted_results = sorted(results, key=lambda x: x.metadata.get("cumulative_particularity", 0), reverse=True)
        # Return top_k results
        return sorted_results[:top_k]


    def search_event(self, query: str, top_k: int = 3, rerank: bool = False, filter: dict = None):
        search_kwargs = {"k": max(3, top_k * 2)}
        if filter:
            search_kwargs["filter"] = filter
        if not rerank:
            retriever = self.global_event_vectorstore.as_retriever(search_type="similarity", search_kwargs=search_kwargs)
            results = retriever.invoke(query)
            return results[:top_k]
        retriever = self.global_event_vectorstore.as_retriever(search_type="similarity", search_kwargs=search_kwargs)
        results = retriever.invoke(query)
        # Rerank results by particularity
        sorted_results = sorted(results, key=lambda x: x.metadata.get("particularity", 0), reverse=True)
        # Return top_k results
        return sorted_results[:top_k]


    def search_target(self, query: str, top_k: int = 3, filter: dict = None):
        search_kwargs = {"k": max(3, top_k * 2)}
        if filter:
            search_kwargs["filter"] = filter

        retriever = self.global_target_vectorstore.as_retriever(search_type="similarity", search_kwargs=search_kwargs)
        results = retriever.invoke(query)
        return results[:top_k]

    def search_segment(self, query: str, top_k: int = 3, filter: dict = None):
        search_kwargs = {"k": max(3, top_k * 2)}
        if filter:
            search_kwargs["filter"] = filter
        retriever = self.global_segment_vectorstore.as_retriever(search_type="similarity", search_kwargs=search_kwargs)
        results = retriever.invoke(query)
        return results[:top_k]
