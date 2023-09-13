## 背景

在音频转文字的准确率上，OpenAI 的 Whisper + Prompt 远超一般的模型服务(飞书妙记、通义听悟、讯飞...)，尤其是在专业名词较多的领域。

但 Whisper 的转写断句能力较差(Large v2 模型)，经常会出现一句话被分隔成两行字幕的情况。

根据 [openai-cookbook/examples/Whisper_prompting_guide.ipynb at main · openai/openai-cookbook](https://github.com/openai/openai-cookbook/blob/main/examples/Whisper_prompting_guide.ipynb) 所言，Whisper 的 Prompt 和 GPT 的 Prompt 并不完全一致——即 Whisper 的 prompt 并不理解 Prompt 所蕴含的指令含义，它只是在**模仿 Prompt 的语言风格和词汇拼写**。

所以通过 Prompt 很难完美解决 Whipser 转写句子被拆分的问题。

目前思考这个问题有两种解决方案：

1.  上传 srt 给 claude，让其返回合并句子后的 srt 文件。
2.  通过代码按某些规则来合并 srt 文件中的句子。

1 是一种比较简单且理想的方案，因为大模型对语义有理解分析，其断句分段把握的比较合适。

但 1 的问题在于大模型有字符长度限制，实测超过 30 min 的转录文本进行合并分段会超出字符限制。初次之外，这种方案还有等待时间较长，可能会出现幻觉等问题。

我日常转录的是 3h 的课程录音，所以我选择采用方案 2 做断句修正。

## 实现策略

方案 2 的原理上比较简单：

> 判断当前行结尾是否有标点符号，如果没有则和下一组字幕文本合并。

## 脚本使用

Clone 到本地后安装依赖，每次修改 `srt_file` 的路径即可使用。

默认修改的字幕文件和源字幕文件在同一个文件夹之内，文件名会加 `_adjusted` 后缀。

## 待办

- [ ] 增加字幕单行最短字符长度限制，减少字幕行数，提高可读性。