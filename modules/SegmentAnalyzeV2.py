import time
from classes.Segment import Segment
from classes.TargetFactory import TargetFactory
from classes.EventFactory import EventFactory
from utils.ai import get_openai_client
import json
import os
import re
from typing import List
from prompts import segment_analyze_prompt_v2
import uuid

openai_model = get_openai_client()


def extract_json_from_markdown(text):
    """Extract JSON content from fenced code blocks if present."""
    json_match = re.search(r'```json\n([\s\S]*?)\n```', text)
    if json_match:
        return json_match.group(1)

    code_match = re.search(r'```([\s\S]*?)```', text)
    if code_match:
        return code_match.group(1)

    return text


def get_response(messages):
    response = openai_model.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content


def process_segments_serially(segments: List[Segment], target_factory, event_factory, video_name: str, subsection_interval):
    for segment in segments:
        process_segment(segment, target_factory, event_factory, video_name=video_name, summary_subsection_interval=subsection_interval)


def create_messages(system_prompt, user_prompt, images):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
    ]

    # Attach images to the user message
    for image in images:
        base64_image = image
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}
        })

    return messages


def write_result_to_file(segment_id, result, video_name):
    output_dir = f"{video_name}/segment_analysis"
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"segment_{segment_id}.json")

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"Result for segment {segment_id} has been written to {filename}")


def read_previous_result(segment_id, video_name):
    previous_id = int(segment_id) - 1
    filename = os.path.join(f"{video_name}/segment_analysis", f"segment_{previous_id}.json")
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f), filename
            except json.JSONDecodeError:
                print(f"Warning: Unable to parse previous result file for segment {previous_id} as JSON.")
                return None, None
    return None, None


def process_segment(segment: Segment, target_factory: TargetFactory, event_factory: EventFactory, video_name: str, summary_subsection_interval):
    time.sleep(10)
    images = segment.get_images()
    target_features = target_factory.get_fearures()
    event_features = event_factory.get_event_type_descriptions()

    # Read previous segment's result (if any)
    previous_result, previous_path = read_previous_result(segment.id, video_name=video_name)
    previous_events = []
    previous_targets = []
    previous_summary = ""
    if previous_result:
        if segment.id % summary_subsection_interval != 0:
            # Refresh summary every N segments to keep it locally scoped
            previous_summary = previous_result.get("summary")
        previous_targets = target_factory.create_targets_from_json(previous_path, segement_id=segment.id)
        previous_events_json = previous_result.get("events")
        if previous_events_json is not None:
            for previous_event_json in previous_events_json:
                if previous_event_json.get("particularity") != 0:
                    previous_events.append(event_factory.create_event(
                        event_id=previous_event_json.get("event_id"),
                        event_type=previous_event_json.get("event_type"),
                        start_time=previous_event_json.get("start_time"),
                        target_ids=previous_event_json.get("target_ids"),
                        description=previous_event_json.get("description"),
                        particularity=previous_event_json.get("particularity"),
                        cause_event_id=previous_event_json.get("cause_event_id"),
                        cause=previous_event_json.get("cause"),
                        target_list=previous_targets,
                        segment_id=segment.id
                    ))

    previous_event_str = "\n".join([str(event) + "\n" for event in previous_events])

    sys_prompt = segment_analyze_prompt_v2.SEGEMENT_ANALYZE_SYS_PROMPT
    user_prompt = segment_analyze_prompt_v2.SEGEMENT_ANALYZE_USER_PROMPT.format(
        target_config=target_features,
        event_config=event_features,
        start_time=segment.start_time,
        previous_events=previous_event_str,
        previous_summary=previous_summary
    )
    messages = create_messages(sys_prompt, user_prompt, images)
    result = get_response(messages)

    # Try to parse result as JSON
    try:
        result_json = json.loads(extract_json_from_markdown(result))
        result_json = add_uuid_to_events(result_json)
    except json.JSONDecodeError:
        print(f"Warning: Unable to parse result as JSON for segment {segment.id}. Storing as plain text.")
        result_json = {"raw_text": result}

    write_result_to_file(segment.id, result_json, video_name=video_name)


def add_uuid_to_events(data):
    for event in data['events']:
        short_uuid = str(uuid.uuid4())[:8]
        event['event_id'] = short_uuid
    return data
