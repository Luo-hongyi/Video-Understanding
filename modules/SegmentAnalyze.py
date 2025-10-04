from concurrent.futures import ThreadPoolExecutor
import threading
from classes.Segment import Segment
from utils.ai import get_openai_client
import json
import os
import time
from typing import List
from prompts import segment_analyze_prompt
from functools import partial

openai_model = get_openai_client()

# Thread-local storage so each thread has its own OpenAI client
thread_local = threading.local()


def get_openai_client():
    if not hasattr(thread_local, 'openai_client'):
        thread_local.openai_client = openai_model
    return thread_local.openai_client


def get_response(messages):
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content


def batch_process_segments(segments: List[Segment], target_factory, event_factory, video_name: str, max_workers=5):
    """Process segments concurrently using a thread pool."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        partial_process = partial(process_segment, target_factory=target_factory, event_factory=event_factory, video_name=video_name)
        results = list(executor.map(partial_process, segments))
    return results


def create_messages(system_prompt, user_prompt, images):
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [{"type": "text", "text": user_prompt}],
        },
    ]

    # Attach images to the user message
    for image in images:
        base64_image = image
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"},
        })

    return messages


def write_result_to_file(segment_id, result, video_name):
    # Ensure output directory exists
    output_dir = f"{video_name}/segment_analysis"
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"segment_{segment_id}.json")

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"Result for segment {segment_id} has been written to {filename}")


def process_segment(segment: Segment, event_factory, target_factory, video_name: str):
    images = segment.get_images()
    target_features = target_factory.get_fearures()
    event_features = event_factory.get_event_type_descriptions()

    sys_prompt = segment_analyze_prompt.SEGEMENT_ANALYZE_SYS_PROMPT
    user_prompt = segment_analyze_prompt.SEGEMENT_ANALYZE_USER_PROMPT.format(
        target_config=target_features,
        event_config=event_features,
        start_time=segment.start_time,
    )
    messages = create_messages(sys_prompt, user_prompt, images)
    result = json.loads(get_response(messages))

    write_result_to_file(segment.id, result, video_name)

    return result
