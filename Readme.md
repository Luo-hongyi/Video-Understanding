# Story-Line Based Video Understanding Framework

## Overview
This project presents an innovative approach to video understanding through story-line extraction and analysis. Unlike traditional frame-by-frame analysis systems, our framework constructs continuous narratives (story-lines) from video content, enabling deeper contextual understanding and temporal reasoning.

## Key Features
- **Story-Line Construction**: Automatically identifies and connects related events across video segments to form coherent narratives
- **Event Causality Analysis**: Tracks cause-and-effect relationships between events to build meaningful story branches
- **Temporal Reasoning**: Maintains chronological context across video segments with overlapping analysis
- **Multi-Modal RAG System**: Combines visual analysis with text-based retrieval for comprehensive understanding
- **Hierarchical Story Structure**: Organizes events into main storylines with branching side-stories based on relevance and importance

## Architecture
The framework consists of several integrated components:
- **Segment Analysis**: Processes video segments to identify entities and events
- **Story Tree Construction**: Builds hierarchical story structures from detected events
- **Vector Store**: Enables semantic search across story-lines, events, and entities
- **RAG Agent**: Provides natural language interface for querying video content through story-lines

## Use Cases
- Surveillance video analysis
- Media content summarization
- Event detection and tracking
- Video search and retrieval by narrative content

## Examples
See demo notebooks:
- [Demo Search](demo_search.ipynb): Demonstrates story-line based retrieval
- [Demo Analyze](demo_analyze.ipynb): Shows the story-line extraction process
- [Main Experiment](main_experiment.ipynb): Complete end-to-end example

## Technical Details
The system uses GPT-4o for vision analysis and narrative construction, with a custom-built story tree structure that maintains relationships between events across video segments. Each story node contains information about event particularity, causality, and temporal context.