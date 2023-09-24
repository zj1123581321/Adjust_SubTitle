import re
import os
import zhipuai
import json
import requests

if_need_LLM_add_punctuation = True
# 是否需要调用 AI 为文本添加标点符号以便处理，主要用于中文无标点场景。如果为 True，需要在 config.json 中配置相关 API。
# 如果 if_need_LLM_add_punctuation = True, 从 config.json 中读取相关 API
if if_need_LLM_add_punctuation:
    with open("config.json", "r") as f:
        config = json.load(f)
        zhipuai_api_key = config["zhipuai_api_key"]
        openai_api_key =config["openai_api_key"]
        openai_api_url = config["openai_api_url"]

def add_punctuation_zhipuai(inputText):
    zhipuai.api_key = zhipuai_api_key
    response = zhipuai.model_api.invoke(
        model="chatglm_std",
        prompt=[
            {"role": "user", "content": f"{inputText}\n\n这是一个音频的转文字结果，以 .lrc 格式存储。请结合语义和上下文为每句话添加标点符号，禁止删除或新增时间点，只需返回修改后的 lrc 文本。"},
        ],
        temperature=0.9, # 值越小结果越稳定
        top_p = 0.7 
    )
    # Sample response:{'code': 200, 'msg': '操作成功', 'data': {'request_id': '7941314437787463250', 'task_id': '7941314437787463250', 'task_status': 'SUCCESS', 'choices': [{'role': 'assistant', 'content': '" 说你们想听哪些历史人物？"'}], 'usage': {'total_tokens': 9}}, 'success': True}
    # 直接打印 choices 中的第一个 content
    # print(response)
    # 检验是否成功
    if response["success"] == False:
        print("请求失败")
        return None
    else:
        print("智谱 AI Token 数量：{}，花费{}元".format(response["data"]["usage"]["total_tokens"], response["data"]["usage"]["total_tokens"]/1000*0.002))
        outputText = response["data"]["choices"][0]["content"]
        # 检查 outputText 最外层是否有双引号，如果有则去掉
        if outputText.startswith('"') and outputText.endswith('"'):
            outputText = outputText[1:-1]
        return outputText

# 调用 gpt3.5 为输入的文本添加标点符号。使用自定义的 api url。函数功能和 add_punctuation_zhipuai 相同。
def add_punctuation_openai(inputText):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "我会向你发送一段音频的转文字结果，以 json 格式存储，key 值为编号，value 为字幕文本。编号 n 的字幕文本和编号 n+1 的字幕文本语义上有连接关系，请基于前后语义为每个 value 添加逗号，句号等标点符号，避免全部使用句号。请直接返回 json 格式的修改结果。"},
            {"role": "user", "content": f"{inputText}"}
        ]
    }

    response = requests.post(f"{openai_api_url}/v1/chat/completions", headers=headers, json=data)
    response_data = response.json()

    if "choices" in response_data and len(response_data["choices"]) > 0:
        # $0.0015 为 prompt_tokens 的单价，$0.002 为 completion_tokens 的单价,根据单价计算本次请求的总花费：prompt_tokens*0.0015 + completion_tokens*0.002
        print("openai api Token 数量：{}，花费{}元".format(response_data["usage"]["total_tokens"], response_data["usage"]["prompt_tokens"]/1000*0.0015*7.2 + response_data["usage"]["completion_tokens"]/1000*0.002*7.2))
        outputText = response_data["choices"][0]["message"]["content"]
        print('outputText', outputText)
        return outputText
    else:
        print("response_data", response_data)
        # 抛出错误
        raise Exception("openai api 返回的数据不正确")

# 为字幕文本添加标点，可以使用智谱AI，也可以使用 chatgpt。输入 old_groups，返回 new_groups
def add_punctuation_service(old_groups):
    max_text_length_per_request = 2000
    # 将 old_groups 的所有字幕文本(groups 里的第二项)拼接成一个字符串列表，每个字符串以换行符连接，长度不能超过 max_text_length_per_request。
    text_list = []
    text = ''
    for i in range(len(old_groups)):
        currentText = old_groups[i].strip().split('\n')[2]
        # print('currentText', currentText)
        if len(text) + len(currentText) < max_text_length_per_request:
            text = f"{text} {currentText}"
        else:
            text_list.append(text)
            text = ''
    text_list.append(text)
    # 对 text_list 中每一项调用智谱 AI 为文本添加标点符号。合并所有返回的文本，然后按换行符分割成列表，每一项就是新的字幕文本。
    new_text_list = []
    for text in text_list:
        new_text = add_punctuation_openai(text)
        new_text_list.append(new_text)
    new_text = '\n'.join(new_text_list)
    print('加标点后文本',new_text)
    # 将 new_text 按文本'\n'拆分为列表 new_caption_list，然后将 new_caption_list 中的每一项按照 old_groups 的顺序，插入到 old_groups 中。
    new_caption_list = new_text.split('\\n')
    # 如果 old_groups 和 new_caption_list 的长度不一致，就报错
    if len(old_groups) != len(new_caption_list):
        print('len(old_groups)', len(old_groups), 'len(new_caption_list)', len(new_caption_list))
        raise Exception('old_groups 和 new_caption_list 的长度不一致')
    # 取 old_groups 中的编号和时间段，然后将 new_text 按换行符分割成列表，每一项就是新的字幕文本。
    new_groups = []
    for i in range(len(old_groups)):
        # 提取编号、时间段和字幕文本
        group = old_groups[i].strip().split('\n')
        if len(group) >= 3:
            time_range = group[1]
            new_text = new_caption_list[i]
            new_groups.append(f"{i}\n{time_range}\n{new_text}")
    return new_groups
