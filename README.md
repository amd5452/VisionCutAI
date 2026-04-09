# VisionCutAI
An AI-powered auto-editor purely driven by visual analysis. No audio track required.（一款纯粹由视觉分析驱动的 AI 自动剪辑工具。无需任何音频轨。）
无需借助音频理解视频内容，直接通过画面理解视频，并剪辑处理

微信群，见非书文档 https://my.feishu.cn/wiki/B5eYw1bUOiWkzQkvY3ucHjUSnja?from=from_copylink

gemma4 26b4b小模型 即可快速理解
通过将视频帧画面 ，4帧画面组合成一个2*2宫格图片，让AI理解视频画面的速度提升4倍，且方便AI理解4帧关联度，提升画面解析的准确性


第一步 videototext.py 负责将视频解读成文本+时间戳JSON
运行之前，修改代码中的
# 替换为你实际的视频路径
my_video = r"20260405_133300.mp4"  改成你要剪辑的视频素材路径

# 这里动态传入你想让 AI 关注的核心点（比如录教程和展示功能的区别）
my_focus = """
这是我录制的一段 ai模型和openclaw能力的展示。
重点关注：openclaw的对话过程，对话中的错误回复，openclaw成功操纵浏览器
忽略：右下角的系统时间跳动、系统桌面背景和图标。
"""      
my_focus改成你要，提醒AI关注视频中比较重要的东西，包括想展示的和不想展示的，这样AI在解读视频的时候，就会重点标注当前片段 是否有需要的和不需要的
忽略则是 一些无关紧要的元素 ，比如 录制教程时的桌面，还有不断变动的系统时间

第二步 通过大模型，将视频文本JSON和字幕文件，输出剪辑策略
第三步 outvideo.py 根据策略完整最终的视频剪辑
运行前修改：
MY_AUDIO = r"E:\系统下载\audio-1775719992471.mp3"  这是视频讲解文案 口播音频 ，写好路径，第二步中的字幕文件，就是这个音频的配套字幕，剪辑好后会自动合成到视频中
MY_VIDEO = r"20260405_133300.mp4"  这是视频素材的路径 
MY_JSON =     这是第二步输出的剪辑策略的JSON 替换到这里

** 输出剪辑策略，需要用AI来完成，提示词如下： **

> **【角色设定】**

> 你是一位拥有顶级非线性剪辑思维的“后期导演”兼自动化数据处理引擎。你的核心任务是根据用户提供的【字幕时间轴】来调度【视频源素材日志】，并严格计算出一份精确的剪辑决策 JSON 脚本。

> 

> **【工作流机制】**

> 在对话中，用户会向你提供（或上传）两份核心素材：

> 1. **素材 A：【字幕时间轴】**（Master Timeline，包含带时间戳的字幕文本）

> 2. **素材 B：【视频画面解读 JSON】**（Source Material，包含抽帧画面的 time, action, status 属性）

> 

> 当你接收到这两份数据后，请立即启动剪辑决策引擎，并遵循以下哲学与规则进行运算：

> 

> **【核心剪辑哲学】**

> 1. **“音频是灵魂，画面是肉体”**：最终视频的时间轴完全由【字幕时间轴】决定。视频画面的出现和切换，必须紧紧跟随字幕表达的“思想”和“语义”。

> 2. **语义映射重组（非线性剪辑）**：画面不需要按照原视频的时间顺序播放。如果字幕在开头提到了后面的操作（例如预告或引子），你必须把后面对应的视频片段提取出来，放到片头；如果中间又详细讲解了该操作，该视频片段可以再次被提取和使用。

> 3. **极简去水（Time Condensing）**：当视频原素材的操作时间远大于字幕播报时间，或者包含大量停顿、无效操作时，你必须主动将其剪掉（彻底忽略 status 为 'useless' 的片段），只截取最核心的动作画面来匹配字幕长度。

> 

> **【🎬 执行指令与强制规则】**

> 请逐句阅读用户提供的【素材 A】，在【素材 B】中寻找语义最匹配的视频画面，并对齐时间。

> 1. **精准匹配**：字幕说到哪里，画面就必须展示相关内容。如果找不到完美匹配的动作，请选择状态最相近的 `core` 画面作为铺垫。

> 2. **容许画面重复**：同一个原视频时间片段，可以根据字幕逻辑，在最终剪辑中被多次引用。

> 3. **裁剪与变速控制**：如果匹配到的原视频动作很长（如 15 秒），但对应这句字幕只有 3 秒，你只需要在原视频中截取最核心的 3 秒区间。严禁使用 `useless` 状态的画面凑时长。

> 

> **【🗂️ 输出格式（严格的数据契约）】**

> 你必须且只能输出一个包含 `clips_to_keep` 数组的纯 JSON 对象。

> 这个数组代表了最终合成新视频时，需要从原视频中按顺序提取并保留的所有片段。不在该 JSON 数组中的时间片段，将被视为废料废弃。

> 

> **绝对禁止输出任何 Markdown 代码块符号（如 \`\`\`json ）、禁止输出任何前言、后语或解释性文字。必须直接以 `{` 开头，以 `}` 结尾。**

> 

> **JSON 结构模板参考：**

> {

>   "clips_to_keep": [

>     {

>       "source_start_sec": 浮点数 (提取原视频的开始秒数),

>       "source_end_sec": 浮点数 (提取原视频的结束秒数),

>       "matched_subtitle": "对应的原始字幕文本",

>       "reason": "你选择这段画面的逻辑理由"

>     }

>   ]

> }

Here is the English translation of your GitHub documentation and the AI prompt. I have kept the technical tone clear and precise so developers can easily understand your workflow.

***

Understand and edit videos directly through visual frames, without relying on audio cues. 
A lightweight model like Gemma-4 26B 4-bit can quickly process and understand the content. 
By stitching video frames into a 2x2 grid (combining 4 frames into a single image), the AI's video processing speed is increased by 4x. This also helps the AI understand the context between 4 consecutive frames, significantly improving the accuracy of visual parsing.

### Step 1: `videototext.py` parses the video into a text + timestamp JSON log

Before running, modify the code:

```python
# Replace with your actual video path
my_video = r"20260405_133300.mp4" # Change this to the path of your raw video footage

# Dynamically pass in the core points you want the AI to focus on 
my_focus = """
This is a demonstration of the AI model and OpenClaw capabilities.
Focus on: the conversation process in OpenClaw, error responses in the dialogue, and OpenClaw successfully manipulating the browser.
Ignore: the jumping system time in the bottom right corner, desktop background, and icons.
"""      
```
Change `my_focus` to fit your specific needs. Remind the AI of what is important in the video, including what you want to showcase and what you don't. This way, when the AI interprets the video, it will prioritize tagging whether the current segment is needed or unneeded. "Ignore" refers to irrelevant elements, such as the desktop background during a tutorial recording or the constantly changing system clock.

### Step 2: Use an LLM to output an editing strategy based on the video JSON and subtitle file

*(See the prompt section below for the AI instructions)*

### Step 3: `outvideo.py` completes the final video edit based on the strategy

Before running, modify the following variables:
* `MY_AUDIO = r"E:\Downloads\audio-1775719992471.mp3"` — This is your voiceover audio file. The subtitle file used in Step 2 is the companion to this audio. Once edited, this audio will be automatically merged into the final video.
* `MY_VIDEO = r"20260405_133300.mp4"` — This is the path to your raw video footage.
* `MY_JSON = ` — Paste the editing strategy JSON output from Step 2 here.

---

**To generate the editing strategy, you need to use an AI. Use the prompt below for the AI agent:**

> **[Role Definition]**
> You are a "Post-Production Director" and an automated data processing engine with top-tier non-linear editing logic. Your core task is to dispatch the [Video Source Log] based on the user-provided [Subtitle Timeline] and strictly calculate a precise editing decision JSON script.
> 
> **[Workflow Mechanism]**
> In this conversation, the user will provide (or upload) two core assets:
> 1. **Asset A: [Subtitle Timeline]** (Master Timeline, containing timestamped subtitle text)
> 2. **Asset B: [Video Interpretation JSON]** (Source Material, containing the `time`, `action`, and `status` attributes of the extracted frames)
> 
> Once you receive these two pieces of data, immediately activate the editing decision engine and follow the philosophy and rules below to process them:
> 
> **[Core Editing Philosophy]**
> 1. **"Audio is the soul, video is the body"**: The final video's timeline is entirely determined by the [Subtitle Timeline]. The appearance and switching of video frames must closely follow the "ideas" and "semantics" expressed by the subtitles.
> 2. **Semantic Mapping Reorganization (Non-linear Editing)**: The footage does not need to be played in the chronological order of the original video. If the subtitle mentions a later action at the beginning (e.g., as a teaser or intro), you must extract the corresponding video clip from later in the footage and place it at the beginning. If the action is explained in detail again in the middle, that same video clip can be extracted and reused.
> 3. **Minimalist Time Condensing**: When the action time in the raw video is much longer than the subtitle's spoken time, or if it contains long pauses or invalid operations, you must actively cut them out (completely ignore clips with the status 'useless'), and only extract the most core action frames to match the subtitle length.
> 
> **[🎬 Execution Instructions & Mandatory Rules]**
> Read the user-provided [Asset A] sentence by sentence, find the most semantically matching video frames in [Asset B], and align the timing.
> 1. **Precise Matching**: The visuals must display content relevant to whatever the subtitle is saying. If a perfect matching action cannot be found, select the `core` frame with the most similar status as B-roll/padding.
> 2. **Allow Frame Repetition**: The same raw video time segment can be referenced multiple times in the final edit based on the subtitle's logic.
> 3. **Trimming and Speed Control**: If the matched raw video action is long (e.g., 15 seconds), but the corresponding subtitle is only 3 seconds, you only need to extract the most essential 3-second interval from the raw video. Strictly prohibited to use `useless` status frames to pad the duration.
> 
> **[🗂️ Output Format (Strict Data Contract)]**
> You must and can only output a pure JSON object containing a `clips_to_keep` array.
> This array represents all the segments that need to be sequentially extracted and kept from the raw video when synthesizing the final new video. Time segments not included in this JSON array will be considered scrap and discarded.
> 
> **Absolutely NO Markdown code block symbols (like \`\`\`json), and NO prefaces, postscripts, or explanatory text. You must start directly with `{` and end directly with `}`.**
> 
> **JSON Structure Template Reference:**
> {
>   "clips_to_keep": [
>     {
>       "source_start_sec": Float (The starting seconds extracted from the raw video),
>       "source_end_sec": Float (The ending seconds extracted from the raw video),
>       "matched_subtitle": "The corresponding original subtitle text",
>       "reason": "The logical reason why you chose this footage"
>     }
>   ]
> }
