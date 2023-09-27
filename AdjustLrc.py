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
            {"role": "system", "content": "你是一个专业的审校人员。你会收到一段音频的转文字结果,以 .lrc 格式存储。请结合语义和上下文，如果一句话被拆分成了不同行的字幕，请将它们合并,以非逗号结尾，但整句话不宜过长。同时需要给字幕文本添加标点符号。以 .lrc 格式返回。"},
            {"role": "user", "content": f"{inputText}"}
        ]
    }

    response = requests.post(f"{openai_api_url}/v1/chat/completions", headers=headers, json=data)
    response_data = response.json()

    if "choices" in response_data and len(response_data["choices"]) > 0:
        # $0.0015 为 prompt_tokens 的单价，$0.002 为 completion_tokens 的单价,根据单价计算本次请求的总花费：prompt_tokens*0.0015 + completion_tokens*0.002
        print("openai api Token 数量：{}，花费{}元".format(response_data["usage"]["total_tokens"], response_data["usage"]["prompt_tokens"]/1000*0.0015*7.2 + response_data["usage"]["completion_tokens"]/1000*0.002*7.2))
        outputText = response_data["choices"][0]["message"]["content"]
        print('##outputText:\n', outputText)
        return outputText
    else:
        print("response_data", response_data)
        # 抛出错误
        raise Exception("openai api 返回的数据不正确")

# 为字幕文本添加标点，可以使用智谱AI，也可以使用 chatgpt。输入 captionList，返回 new_groups
def add_punctuation_service(captionList):
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
    # 对 text_list 中每一项调用智谱 AI 为文本添加标点符号。合并所有返回的文本，然后按换行符分割成列表，每一项就是新的字幕文本。
    new_text_list = []
    for text in text_list:
        new_text = add_punctuation_openai(text)
        new_text_list.append(new_text)
    new_text = '\n'.join(new_text_list)
    print('文本处理后：',new_text)
    return new_text

def generate_output_file_path(lrc_file):
    # 生成 output_file 的路径和文件名
    directory = os.path.dirname(lrc_file)
    filename = os.path.basename(lrc_file)
    new_filename = filename.replace('.lrc', '_adjusted.lrc')
    output_file = os.path.join(directory, new_filename)
    print(output_file)
    return output_file

# 将 lrc 格式字幕转换成 srt 格式，输入 lrc 文本，返回 srt 文本。
def lrc_to_srt(lrc):
    # 将 LRC 文本按行分割
    lines = lrc.split('\n')
    
    # 初始化 SRT 文本和计数器
    srt = ''
    count = 1
    
    # 遍历每一行 LRC 文本
    for i in range(len(lines)):
        line = lines[i]
        
        # 使用正则表达式提取时间戳和歌词内容
        match = re.match(r'\[(\d+:\d+\.\d+)\](.*)', line)
        if match:
            timestamp = match.group(1)
            content = match.group(2).strip()
            
            # 将时间戳格式转换为 SRT 格式
            srt_timestamp = timestamp.replace('.', ',')
            
            # 获取下一行的时间戳
            next_line = lines[i + 1] if i < len(lines) - 1 else ''
            next_match = re.match(r'\[(\d+:\d+\.\d+)\]', next_line)
            if next_match:
                next_timestamp = next_match.group(1)
                srt_timestamp += ' --> ' + next_timestamp.replace('.', ',')
            
            # 将 SRT 时间戳和内容添加到 SRT 文本中
            srt += f'{count}\n{srt_timestamp}\n{content}\n\n'
            count += 1
    
    return srt.strip()

# 主函数，读取 lrc 文件，调用 add_punctuation_service 为字幕文本添加标点，然后将结果写入新的 lrc 文件。
def main():
    # 读取 lrc 文件
    with open("sampleLrc.lrc", "r", encoding="utf-8") as f:
        lrc = f.read()
    # 将 lrc 按换行符分割成列表 captaionList，每一项就是一条字幕
        captionList = lrc.split("\n")
    # print("captionList", captionList)
    newCaption = add_punctuation_service(captionList)
    # 将 newCaption 写入新的 lrc 文件
    output_file = generate_output_file_path("sampleLrc.lrc")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(newCaption)
    # 将 lrc 转换成 srt
    srt = lrc_to_srt(newCaption)
    # 将 srt 写入新的 srt 文件
    with open("sampleSrt.srt", "w", encoding="utf-8") as f:
        f.write(srt)

if __name__ == "__main__":
    main()