import zhipuai
import os
import json

# 从 config.json 中读取 api_key
with open("config.json", "r") as f:
    config = json.load(f)
    api_key = config["api_key"]

def main():
    inputText = "大家好,我是余更哲老师。\n今天咱们谈一下袁天罡和李淳风。\n为什么谈这个呢？\n我在咱们这个B站上问诸位朋友，\n说你们想听哪些历史人物，\n结果有不少人提到袁天罡和李淳风。\n因为什么呢？\n好像是说是现在有一个电视剧叫什么《盗墓笔记之龙岭石窟》吧，是不是？"
    outputText = add_punctuation(inputText)
    print(outputText)


# 为输入的文本添加标点符号，调用智谱 AI：便宜，处理一般内容足够了
def add_punctuation(inputText):
    zhipuai.api_key = api_key
    response = zhipuai.model_api.invoke(
        model="chatglm_lite",
        prompt=[
            {"role": "user", "content": "(你好，我是李先生\n今天我们来讲历史)，请为括号内的文本添加标点符号，除了添加标点，不可以修改源文本,不要删除换行符。可以不加标点。返回值不应该包含括号"},
            {"role": "assistant", "content": "你好，我是李先生。\n今天我们来讲历史。"},
            {"role": "user", "content": f"({inputText})，请为括号内的文本添加标点符号，除了添加标点，不可以修改源文本，不要删除换行符。可以不加标点。返回值不应该包含括号"},
        ]
    )
    # Sample response:{'code': 200, 'msg': '操作成功', 'data': {'request_id': '7941314437787463250', 'task_id': '7941314437787463250', 'task_status': 'SUCCESS', 'choices': [{'role': 'assistant', 'content': '" 说你们想听哪些历史人物？"'}], 'usage': {'total_tokens': 9}}, 'success': True}
    # 直接打印 choices 中的第一个 content
    # print(response)
    # 检验是否成功
    if response["success"] == False:
        print("请求失败")
        return None
    else:
        print("Token 数量：{}，花费{}元".format(response["data"]["usage"]["total_tokens"], response["data"]["usage"]["total_tokens"]/1000*0.002))
        return response["data"]["choices"][0]["content"]

if __name__ == "__main__":
    main()  
