from concurrent.futures import ThreadPoolExecutor
import threading
from classes.Segment import Segment  # 确保导入路径正确
from openai import OpenAI
import json
import os
import time
from typing import List
from prompts import segment_analyze_prompt
from functools import partial

# 初始化OpenAI客户端
openai_model = OpenAI(api_key="")

# 线程局部存储，确保每个线程有自己的OpenAI客户端实例
thread_local = threading.local()

# 辅助方法
def get_openai_client():
    if not hasattr(thread_local, 'openai_client'):
        thread_local.openai_client = openai_model
    return thread_local.openai_client

# 调用模型
def get_response(messages):
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=messages,
        temperature=0
    )
    #return json.loads(response.choices[0].message.content)
    return response.choices[0].message.content
    
#批量处理
def batch_process_segments(segments: List[Segment], target_factory, event_factory, video_name: str, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        partial_process = partial(process_segment, target_factory=target_factory, event_factory=event_factory, video_name=video_name)
        results = list(executor.map(partial_process, segments))
    return results

def create_messages(system_prompt, user_prompt, images):
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        }
    ]

    # 添加图片到用户消息
    for image in images:
        base64_image = image
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
                "detail": "high"
            }
        })

    return messages

def write_result_to_file(segment_id, result, video_name):
    # 确保输出目录存在
    output_dir = f"{video_name}/segment_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建以segment_id命名的文件
    filename = os.path.join(output_dir, f"segment_{segment_id}.json")
    
    # 将结果写入文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    print(f"Result for segment {segment_id} has been written to {filename}")

def process_segment(segment: Segment, event_factory, target_factory, video_name: str):
    images = segment.get_images()
    target_features = target_factory.get_fearures()
    event_features = event_factory.get_event_type_descriptions()

    sys_prompt = segment_analyze_prompt.SEGEMENT_ANALYZE_SYS_PROMPT
    user_prompt = segment_analyze_prompt.SEGEMENT_ANALYZE_USER_PROMPT.format(
        target_config = target_features,
        event_config = event_features,
        start_time = segment.start_time
    )
    messages = create_messages(sys_prompt, user_prompt, images)
    result = json.loads(get_response(messages))
    
    # 将结果写入文件
    write_result_to_file(segment.id, result, video_name)
    
    return result
