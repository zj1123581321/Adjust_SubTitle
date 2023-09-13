import re
import os

# 每行字幕的最短字数，adjust_mode 为 2 时有效
min_length = 120
max_length = 180


def main():
    srt_file = 'D:/MyFolders/Developments/0Python/230912_AdjustSubTitle/subtitle.srt'
    # 字幕的调整方式，
    # 1 为合并被断行的句子，
    # 2 在 1 的基础上，保证每行以非逗号结尾
    # 3 在 1-2 的基础上，保证每一行的字数不小于目标值
    adjust_mode = '3'
    adjust_srt_file(srt_file, adjust_mode)

def generate_output_file_path(srt_file):
    # 生成 output_file 的路径和文件名
    directory = os.path.dirname(srt_file)
    filename = os.path.basename(srt_file)
    new_filename = filename.replace('.srt', '_adjusted.srt')
    output_file = os.path.join(directory, new_filename)
    print(output_file)
    return output_file

def read_and_split_srt_file(srt_file):
    # 读取srt文件内容并将内容按空行分割成不同的组
    with open(srt_file, 'r') as file:
        content = file.read()
    old_groups = re.split(r'\n\s*\n', content)
    # 去除 old_groups 中的空字符串
    old_groups = [group for group in old_groups if group != '']
    return old_groups

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
                number = group[0]
                time_range = group[1]
                text = ' '.join(group[2:])

                if text.endswith(('.', ',', ':', ';', '?', '!')):
                    # 如果字幕文本以标点符号结尾
                    new_groups.append(f"{index}\n{time_range}\n{text}")
                    current_number += 1
                else:
                    # 合并时间段和字幕文本
                    time_range_start = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})', time_range).group(1)
                    # next_time_range_end = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})', old_groups[i + 1]).group(1)
                    #获取下一个时间段的结尾时间，即正则表达式中的第二个匹配项 re.findall
                    next_time_range_end = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', old_groups[i + 1])[1]

                    new_time_range = f"{time_range_start} --> {next_time_range_end}"

                    current_text = text
                    next_text = ' '.join(old_groups[i + 1].strip().split('\n')[2:])
                    new_text = f"{current_text} {next_text}"

                    new_groups.append(f"{index}\n{new_time_range}\n{new_text}")
                    current_number += 2

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
                        if i + move_times >= len(old_groups)-1:
                            move_times = 0
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

def write_new_srt_file(output_file, new_groups):
    # 将new_groups的内容按srt格式写入新的srt文件
    with open(output_file, 'w') as file:
        file.write('\n\n'.join(new_groups))

def adjust_srt_file(srt_file, adjust_mode):
    old_groups = read_and_split_srt_file(srt_file)
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