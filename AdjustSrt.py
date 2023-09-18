import re
import os
import zhipuai
import json

# 每行字幕的最短字数，adjust_mode 为 3 时有效
min_length = 120
max_length = 180
if_need_spilt = True 
# 是否需要根据非逗号拆分字幕，时间戳根据字符长度比例拆分，并不一定准确。实验性功能，建议在连续多句字幕都无标点结尾时使用。(主要应用于英文有标点场景)
if_need_LLM_add_punctuation = True
# 是否需要调用 AI 为文本添加标点符号以便处理，主要用于中文无标点场景。如果为 True，需要在 config.json 中配置相关 API。
srt_file = 'D:/MyFolders/Developments/0Python/230912_AdjustSubTitle/subtitle.srt'
adjust_mode = '3'
# 字幕的调整方式，
# 1 为合并被断行的句子，
# 2 在 1 的基础上，保证每行以非逗号结尾
# 3 在 1-2 的基础上，保证每一行的字数在 min_length 和 max_length 之间

# 从 config.json 中读取 zhipuai_api_key
with open("config.json", "r") as f:
    config = json.load(f)
    zhipuai_api_key = config["zhipuai_api_key"]


def main():
    adjust_srt_file(srt_file, adjust_mode)

# 为输入的文本添加标点符号，调用智谱 AI：便宜，处理一般内容足够了
def add_punctuation_zhipuai(inputText):
    zhipuai.api_key = zhipuai_api_key
    response = zhipuai.model_api.invoke(
        model="chatglm_std",
        prompt=[
            {"role": "user", "content": "(你好，我是李先生\n今天我们来讲历史\n好像是说是现在有一个电视剧叫什么《盗墓笔记之龙岭石窟》吧)，请为括号内的文本添加标点符号，除了添加标点，严禁修改源文本、删除换行符、添加换行符。可以不加标点。返回值不应该包含括号,最外层无需使用双引号"},
            {"role": "assistant", "content": "你好，我是李先生。\n今天我们来讲历史。\n好像是说是现在有一个电视剧叫什么《盗墓笔记之龙岭石窟》吧。"},
            {"role": "user", "content": f"({inputText})，请为括号内的文本添加标点符号，除了添加标点，严禁修改源文本、删除换行符、添加换行符。可以不加标点。返回值不应该包含括号,最外层无需使用双引号"},
        ],
        temperature=0.95, # 值越小结果越稳定
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

def generate_output_file_path(srt_file):
    # 生成 output_file 的路径和文件名
    directory = os.path.dirname(srt_file)
    filename = os.path.basename(srt_file)
    new_filename = filename.replace('.srt', '_adjusted.srt')
    output_file = os.path.join(directory, new_filename)
    print(output_file)
    return output_file

#读取srt字幕，按空行分割成不同的组，返回一个列表，列表中的每个元素是一个组，组内包含编号、时间段和字幕文本
def read_and_split_srt_file(srt_file):
    # 读取srt文件内容并将内容按空行分割成不同的组
    with open(srt_file, 'r',encoding="utf-8") as file:
        content = file.read()
    old_groups = re.split(r'\n\s*\n', content)
    # 去除 old_groups 中的空字符串
    old_groups = [group for group in old_groups if group != '']
    return old_groups

# 拆分每行字幕。如果一行字幕内容里含有非逗号的标点，则拆分成两行字幕。同时时间戳按照开头到标点的长度占总长度的比例进行拆分。
def split_srt_content(old_groups):
    # 用于记录当前该处理 old_groups 中的第几个组
    current_number = 0
    # 用于在 new_groups 中的索引
    index = 0
    new_groups = []

    for i in range(len(old_groups)):
        # 如果 i 不等于 current_number 就跳过
        if(i == current_number):
            # 提取编号、时间段和字幕文本
            group = old_groups[i].strip().split('\n')

            if len(group) >= 3:
                time_range = group[1]
                text = ' '.join(group[2:])
                # 检查当前字幕是否含有非逗号的标点，如果有则拆分成两行字幕。text part 取小于 1 的数字，保证不会取到最后一个标点。
                text_part = text[:int(len(text)*4/5)]
                if re.search(r'[^\w,，\s]', text_part):
                    # 获取当前字幕最后一个标点符号的索引
                    last_punctuation_index = re.search(r'[^\w,，\s]', text_part).span()[1]
                    # print(i, last_punctuation_index)
                    # 根据最后一个标点将当前字幕拆分成两行字幕
                    text_1 = text[:last_punctuation_index]
                    text_2 = text[last_punctuation_index:]
                    # 计算原字幕的持续时间，然后根据拆分后的两行字幕的长度占原字幕长度的比例，计算出两行字幕的持续时间。
                    time_range_1, time_range_2 = split_time_range(time_range, len(text_1) / len(text))
                    new_groups.append(f"{index}\n{time_range_1}\n{text_1}")
                    new_groups.append(f"{index+1}\n{time_range_2}\n{text_2}")
                    current_number += 1
                    index += 2
                else:
                    new_groups.append(f"{index}\n{time_range}\n{text}")
                    current_number += 1
                    index += 1
    return new_groups

# 拆分时间段的函数，输入原时间段和拆分比例，返回拆分后的时间段。中间过程精确到毫秒。
def split_time_range(time_range, split_ratio):
    # 获取原时间段的开始时间和结束时间
    time_range_start = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})', time_range).group(1)
    time_range_end = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', time_range)[1]
    # 计算原时间段的持续时间，然后根据拆分后的两行字幕的长度占原字幕长度的比例，计算出两行字幕的持续时间。此处需要注意 00:06:33,319 中有毫秒。
    time_range_start_seconds = int(time_range_start.split(':')[0]) * 3600 + int(time_range_start.split(':')[1]) * 60 + int(time_range_start.split(':')[2].split(',')[0]) + int(time_range_start.split(':')[2].split(',')[1]) / 1000
    time_range_end_seconds = int(time_range_end.split(':')[0]) * 3600 + int(time_range_end.split(':')[1]) * 60 + int(time_range_end.split(':')[2].split(',')[0]) + int(time_range_end.split(':')[2].split(',')[1]) / 1000
    # 计算出拆分的时间，转换为 00:00:00,000 的格式
    split_seconds = (time_range_end_seconds - time_range_start_seconds) * split_ratio
    split_time = time_range_start_seconds + split_seconds
    split_time_hour = int(split_time / 3600)
    split_time_minute = int((split_time - split_time_hour * 3600) / 60)
    split_time_second = int(split_time - split_time_hour * 3600 - split_time_minute * 60)
    split_time_millisecond = int((split_time - split_time_hour * 3600 - split_time_minute * 60 - split_time_second) * 1000)
    split_time_range = f"{split_time_hour:02d}:{split_time_minute:02d}:{split_time_second:02d},{split_time_millisecond:03d}"
    # 返回两个拼接后的时间端 time_range_start -> split_time_range 和 split_time_range -> time_range_end
    return f"{time_range_start} --> {split_time_range}", f"{split_time_range} --> {time_range_end}"


# 把断句合并成一句
def adjust_srt_content(old_groups):
    # 用于记录当前该处理 old_groups 中的第几个组
    current_number = 0
    # 用于在 new_groups 中的索引
    index = 0
    new_groups = []

    for i in range(len(old_groups)):
        # 如果 i 不等于 current_number 就跳过
        if(i == current_number):
            # 提取编号、时间段和字幕文本
            group = old_groups[i].strip().split('\n')

            if len(group) >= 3:
                time_range = group[1]
                text = ' '.join(group[2:])
                print(i,text)
                # 当前字幕文本不以标点结尾，则向后找到第一个不以逗号结尾的字幕文本；否则直接写入 new_groups
                if text.endswith(('.', ',', ':', ';', '?', '!')):
                    new_groups.append(f"{index}\n{time_range}\n{text}")
                    current_number += 1 
                else:
                    move_times = 1
                    # 如果当前句子结尾不是标点符号
                    while not text.endswith(('.', ',', ':', ';', '?', '!')):
                        # 判断 i+move_times 是否超出 old_groups 的索引范围
                        if i + move_times >= len(old_groups)-1:
                            move_times = 0
                            break
                        next_text = ' '.join(old_groups[i + move_times].strip().split('\n')[2:])
                        text = f"{text} {next_text}"
                        move_times += 1
                    print(i, move_times)
                    # 合并时间段和字幕文本
                    time_range_start = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})', time_range).group(1)
                    next_time_range_end = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', old_groups[i + move_times-1])[1]
                    new_time_range = f"{time_range_start} --> {next_time_range_end}"

                    new_groups.append(f"{index}\n{new_time_range}\n{text}")
                    current_number += move_times   
                index += 1
    return new_groups

# 保证每一行的结尾非逗号
def adjust_srt_content_end_with_no_comma(old_groups):
    # 用于记录当前该处理 old_groups 中的第几个组
    current_number = 0
    # 用于在 new_groups 中的索引
    index = 0
    new_groups = []
    
    for i in range(len(old_groups)):
        # 如果 i 不等于 current_number 就跳过
        if(i == current_number):
            # 提取编号、时间段和字幕文本
            group = old_groups[i].strip().split('\n')

            if len(group) >= 3:
                time_range = group[1]
                text = ' '.join(group[2:])
                # 当前字幕文本以逗号结尾，则向后找到第一个不以逗号结尾的字幕文本，合并
                if text.endswith((',', '，')):
                    move_times = 1
                    # 如果以中文逗号或者英文逗号结尾
                    while text.endswith((',', '，')):
                        # 判断 i+move_times 是否超出 old_groups 的索引范围
                        if i + move_times >= len(old_groups)-1:
                            move_times = 0
                            break
                        next_text = ' '.join(old_groups[i + move_times].strip().split('\n')[2:])
                        text = f"{text} {next_text}"
                        move_times += 1
                    # 合并时间段和字幕文本
                    time_range_start = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})', time_range).group(1)
                    next_time_range_end = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', old_groups[i + move_times-1])[1]
                    new_time_range = f"{time_range_start} --> {next_time_range_end}"

                    new_groups.append(f"{index}\n{new_time_range}\n{text}")
                    current_number += move_times    
                else:
                    new_groups.append(f"{index}\n{time_range}\n{text}")
                    current_number += 1
                index += 1
    return new_groups

# 每行字数在 min_length 和 max_length 之间
def adjust_srt_content_with_min_max(old_groups):
    # 用于记录当前该处理 old_groups 中的第几个组
    current_number = 0
    # 用于在 new_groups 中的索引
    index = 0
    new_groups = []
    
    print('len(old_groups)', len(old_groups))
    for i in range(len(old_groups)):
        # 如果 i 不等于 current_number 就跳过
        if(i == current_number):
            # 提取编号、时间段和字幕文本
            group = old_groups[i].strip().split('\n')

            if len(group) >= 3:
                time_range = group[1]
                text = ' '.join(group[2:])
                print(i,text)
                # 如果当前字幕文本的长度小于 min_length，计算需要合并 n 组字幕文本才能大于 min_length，小于 max_length；否则直接写入 new_groups
                if len(text) < min_length:
                    move_times = 1
                    while len(text) < min_length:
                        # 判断 i+move_times 是否超出 old_groups 的索引范围
                        if i + move_times >= len(old_groups):
                            print('out of range,len(old_groups):', len(old_groups))
                            # move_times = 1
                            break
                        next_text = ' '.join(old_groups[i + move_times].strip().split('\n')[2:])
                        # 如果当前字幕文本加上下一个字幕文本的长度大于 max_length，就不再合并
                        if len(text) + len(next_text) > max_length:
                            break
                        text = f"{text} {next_text}"
                        move_times += 1
                    print(current_number, move_times, len(text))
                    # 合并时间段和字幕文本
                    time_range_start = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})', time_range).group(1)
                    next_time_range_end = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', old_groups[i + move_times-1])[1]
                    new_time_range = f"{time_range_start} --> {next_time_range_end}"

                    new_groups.append(f"{index}\n{new_time_range}\n{text}")
                    current_number += move_times    
                else:
                    new_groups.append(f"{index}\n{time_range}\n{text}")
                    current_number += 1
                index += 1
    return new_groups

def write_new_srt_file(output_file, new_groups):
    # 将new_groups的内容按srt格式写入新的srt文件
    with open(output_file, 'w',encoding="utf-8") as file:
        file.write('\n\n'.join(new_groups))

# 为字幕文本添加标点，可以使用智谱AI，也可以使用 chatgpt。输入 old_groups，返回 new_groups
def add_punctuation_service(old_groups):
    max_text_length_per_request = 4000
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
        new_text = add_punctuation_zhipuai(text)
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


def adjust_srt_file(srt_file, adjust_mode):
    old_groups = read_and_split_srt_file(srt_file)
    if if_need_LLM_add_punctuation:
        print('if_need_LLM_add_punctuation is True，调用 AI 为文本添加标点符号')
        new_groups = add_punctuation_service(old_groups)
        old_groups = new_groups
    if if_need_spilt:
        print('adjust_mode is 0，先根据非逗号拆分行')
        old_groups = split_srt_content(old_groups)
    # 断句合并是基础操作
    new_groups = adjust_srt_content(old_groups)
    if adjust_mode == '2':
        print('adjust_mode is 2，保证每行以非逗号结尾')
        new_groups = adjust_srt_content_end_with_no_comma(new_groups)
    elif adjust_mode == '3':
        print('adjust_mode is 3,min_length is ', min_length, 'max_length is ', max_length)
        # 先保证每行以非逗号结尾，再保证每行字数在 min_length 和 max_length 之间
        new_groups = adjust_srt_content_end_with_no_comma(new_groups)
        new_groups = adjust_srt_content_with_min_max(new_groups)
    output_file = generate_output_file_path(srt_file)
    write_new_srt_file(output_file, new_groups)

if __name__ == '__main__':
    main()