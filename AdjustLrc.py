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
        deepseek_api_key = config["deepseek_api_key"]

# 智谱，垃圾
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
            {"role": "system", "content": "你是为音频转录生成的 LRC 格式字幕添加标点符号的专家。保留原始单词，仅插入必要的标点符号，例如句号、逗号、大写字母、美元符号或百分号等符号以及格式。如果结合下一行判断此行无需添加标点，则可以不添加标点。仅使用提供的上下文，返回添加标点后的 LRC 格式字幕文本"},
            {"role": "user", "content": f"{inputText}"}
        ],
        "frequency_penalty":0,
        "presence_penalty":0,
        "temperature":0.6,
        "top_p":1
    }

    response = requests.post(f"{openai_api_url}/v1/chat/completions", headers=headers, json=data)
    response_data = response.json()

    if "choices" in response_data and len(response_data["choices"]) > 0:
        # $0.0005 为 prompt_tokens 的单价，$0.0015 为 completion_tokens 的单价,根据单价计算本次请求的总花费：prompt_tokens*0.0015 + completion_tokens*0.002
        print("openai api Token 数量：{}，花费{}元".format(response_data["usage"]["total_tokens"], response_data["usage"]["prompt_tokens"]/1000*0.0005*7.2 + response_data["usage"]["completion_tokens"]/1000*0.0015*7.2))
        outputText = response_data["choices"][0]["message"]["content"]
        print('##outputText:\n', outputText)
        return outputText
    else:
        print("response_data", response_data)
        # 抛出错误
        raise Exception("openai api 返回的数据不正确")

# 使用 deepseek api 添加标点 
def add_punctuation_deepseek(inputText):
    # https://platform.deepseek.com/api-docs/
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {deepseek_api_key}"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是为音频转录生成的 LRC 格式字幕添加标点符号的专家。保留原始单词，仅插入必要的标点符号，例如句号、逗号、大写字母、美元符号或百分号等符号以及格式。如果结合下一行判断此行无需添加标点，则可以不添加标点。仅使用提供的上下文，返回添加标点后的 LRC 格式字幕文本"},
            {"role": "user", "content": f"{inputText}"}
        ],
        "temperature":0.6
    }

    response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)
    response_data = response.json()

    if "choices" in response_data and len(response_data["choices"]) > 0:
        outputText = response_data["choices"][0]["message"]["content"]
        print('##outputText:\n', outputText)
        return outputText
    else:
        print("response_data", response_data)
        # 抛出错误
        raise Exception("deepseek api 返回的数据不正确")
    
# 为字幕文本添加标点，可以使用智谱AI，也可以使用 chatgpt。输入 captionList，返回 new_groups
def add_punctuation_service(captionList,service='deepseek'):
    # 最大中文长度，采取 max_token/2.5 估算。
    max_text_length_per_request = 1500
    # 将 captionList 的所有字幕文本(groups 里的第二项)拼接成一个字符串列表，每个字符串以换行符连接，长度不能超过 max_text_length_per_request。
    text_list = []
    text = ''
    for i in range(len(captionList)):
        if len(text) + len(captionList[i]) < max_text_length_per_request:
            text = f"{text}\n{captionList[i]}"
        else:
            text_list.append(text)
            text = ''
    text_list.append(text)
    # 对 text_list 中每一项调用 AI 为文本添加标点符号。合并所有返回的文本，然后按换行符分割成列表，每一项就是新的字幕文本。
    new_text_list = []
    for text in text_list:
        if service == 'zhipuai':
            new_text = add_punctuation_zhipuai(text)
        elif service == 'openai':
            new_text = add_punctuation_openai(text)
        elif service == 'deepseek':
            new_text = add_punctuation_deepseek(text)
        new_text_list.append(new_text)
    new_text = '\n'.join(new_text_list)
    print('文本处理后：',new_text)
    return new_text

def generate_output_file_path(lrc_file):
    # 生成 output_file 的路径和文件名
    directory = os.path.dirname(lrc_file)
    filename = os.path.basename(lrc_file)
    new_filename = filename.replace('.lrc', '_add_punctuation.lrc')
    output_file = os.path.join(directory, new_filename)
    print(output_file)
    return output_file

def lrc2srt_file_path(lrc_file):
    # 生成 srt_file 的路径和文件名
    directory = os.path.dirname(lrc_file)
    filename = os.path.basename(lrc_file)
    new_filename = filename.replace('.lrc', '.srt')
    srt_file = os.path.join(directory, new_filename)
    print(srt_file)
    return srt_file

# 将 lrc 格式字幕转换成 srt 格式，输入 lrc 文本，返回 srt 文本。
def parse_lrc_timestamp(timestamp):
    try:
        parts = timestamp.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = parts
        else:
            return None

        seconds, milliseconds = seconds.split('.')
        hours, minutes, seconds, milliseconds = int(hours), int(minutes), int(seconds), int(milliseconds)
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    except ValueError:
        return None

def format_time(seconds):
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    seconds = int(seconds) % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def lrc_to_srt(lrc_content):
    subs = []
    pattern = r'\[(\d+:\d+:\d+\.\d+|\d+:\d+\.\d+)\](.*)'
    matches = re.findall(pattern, lrc_content)
    for idx, match in enumerate(matches):
        timestamp, text = match
        start_time = parse_lrc_timestamp(timestamp)
        if start_time is not None:
            end_time = parse_lrc_timestamp(matches[idx + 1][0]) if idx + 1 < len(matches) else start_time + 1
            subs.append(f"{len(subs) + 1}\n{format_time(start_time)} --> {format_time(end_time)}\n{text.strip()}\n")
    return ''.join(subs)

# 主函数，读取 lrc 文件，调用 add_punctuation_service 为字幕文本添加标点，然后将结果写入新的 lrc 文件。
def main():
    lrc_file = "D:/我的坚果云/中国城夜总会剿匪记.lrc"
    # LLM_service = 'deepseek'
    LLM_service = 'openai'
    # 读取 lrc 文件
    with open(lrc_file, "r", encoding="utf-8") as f:
        lrc = f.read()
    # 将 lrc 按换行符分割成列表 captaionList，每一项就是一条字幕
        captionList = lrc.split("\n")
    # print("captionList", captionList)
    # newCaption = add_punctuation_service(captionList,LLM_service)
    newCaption = lrc
    # 将 newCaption 写入新的 lrc 文件
    output_file = generate_output_file_path(lrc_file)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(newCaption)
    # 将 lrc 转换成 srt
    srt = lrc_to_srt(newCaption)
    # 将 srt 写入新的 srt 文件
    with open(lrc2srt_file_path(output_file), "w", encoding="utf-8") as f:
        f.write(srt)

if __name__ == "__main__":
    main()