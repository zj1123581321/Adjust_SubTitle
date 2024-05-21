import json
import re
import os


def extract(path):
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


def write(data, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data)


def ms_to_srt(time_in_ms):
    convert_ms = int(time_in_ms / 1000)
    ms = convert_ms % 1000
    total_seconds = (convert_ms - ms) / 1000
    seconds = int(total_seconds % 60)
    total_minutes = (total_seconds - seconds) / 60
    minutes = int(total_minutes % 60)
    hour = int((total_minutes - minutes) / 60)

    return f'{hour:02}:{minutes:02}:{seconds:02},{ms:03}'


def scrap_subs(content):
    subtitles_info = []
    materials = content['materials']
    sub_timing = content['tracks'][1]['segments']

    for m in materials['texts']:
        content_json = json.loads(m['content'])
        text = content_json['text']

        segment = next(seg for seg in sub_timing if seg['material_id'] == m['id'])
        start = segment['target_timerange']['start']
        end = start + segment['target_timerange']['duration']
        timestamp = f'{ms_to_srt(start)} --> {ms_to_srt(end)}'
        index = len(subtitles_info) + 1

        subtitles_info.append({
            'index': index,
            'timestamp': timestamp,
            'content': text
        })

    return subtitles_info


if __name__ == "__main__":
    # capcut_path = os.getenv("LOCALAPPDATA") + r"\CapCut"
    # projects_path = capcut_path + r"\User Data\Projects\com.lveditor.draft"
    # projects_path = r"D:\OneDrive\文档\Jianying\CapCut Drafts"

    # project = input(
    #     "[*]Projects list:\n" +
    #     "\n".join(p for p in os.listdir(projects_path) if p not in ['.recycle_bin', 'root_meta_info.json']) +
    #     "\n\n[*]Type the project name in order to extract auto captions: "
    # )

    # draft = fr"{projects_path}\{project}\draft_content.json"
    draft = "D:\OneDrive\文档\Jianying\CapCut Drafts\SrtExport\draft_content.json"
    subtitles = scrap_subs(extract(draft))

    output = ''.join([f'{s["index"]}\n{s["timestamp"]}\n{s["content"]}\n\n' for s in subtitles])
    write(output, 'capcut_subtitles.srt')

    print("[+]Successfully SRT file extracted!")