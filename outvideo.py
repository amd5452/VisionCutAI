import json
import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

def create_final_video(video_path, audio_path, json_string, output_path="final_cut.mp4"):
    print("🎬 正在初始化剪辑引擎...")
    
    # 1. 解析 AI 生成的 JSON 数据
    try:
        data = json.loads(json_string)
        clips_to_keep = data.get("clips_to_keep", [])
    except json.JSONDecodeError:
        print("❌ JSON 解析失败，请检查格式！")
        return

    if not clips_to_keep:
        print("❌ 没有找到需要保留的片段！")
        return

    # 2. 加载原始视频和目标音频
    print(f"📥 正在加载视频源: {video_path}")
    if not os.path.exists(video_path):
        print("❌ 找不到视频文件，请检查路径！")
        return
        
    print(f"📥 正在加载音频源: {audio_path}")
    if not os.path.exists(audio_path):
        print("❌ 找不到音频文件，请检查路径！")
        return

    video = VideoFileClip(video_path)
    voiceover_audio = AudioFileClip(audio_path)
    
    video_duration = video.duration
    extracted_clips = []
    total_new_duration = 0

    print("\n✂️ 开始切割视频片段...")
    # 3. 按照 JSON 的指令切片
    for i, clip_info in enumerate(clips_to_keep):
        start_sec = clip_info["source_start_sec"]
        end_sec = clip_info["source_end_sec"]
        subtitle = clip_info.get("matched_subtitle", "未知字幕")
        
        # 安全防范：防止 AI 给的时间超过了视频总长
        if start_sec >= video_duration:
            print(f"⚠️ 警告: 起始时间 {start_sec}s 超出视频总长，跳过此段。")
            continue
        if end_sec > video_duration:
            end_sec = video_duration

        print(f"  [{i+1}/{len(clips_to_keep)}] 切取 {start_sec}s -> {end_sec}s | 对应台词: '{subtitle}'")
        
        # 核心动作：切取片段，并且【一定要静音】，否则原视频的杂音会和你的 MP3 混在一起
        # 2.0 版本中 subclip 变成了 subclipped
        subclip = video.subclipped(start_sec, end_sec).without_audio()
        extracted_clips.append(subclip)
        total_new_duration += (end_sec - start_sec)

    if not extracted_clips:
        print("❌ 没有提取到任何有效片段。")
        return

    # 4. 拼接所有切下来的片段
    print("\n🔗 正在拼接所有片段...")
    final_video_no_audio = concatenate_videoclips(extracted_clips)

    
    # 5. 处理音视频对齐与合成
    print("🎵 正在处理音视频对齐...")
    
    video_dur = final_video_no_audio.duration
    audio_dur = voiceover_audio.duration

    if video_dur < audio_dur:
        print(f"⚠️ 提示：视频总时长({video_dur:.1f}s) 小于 音频总时长({audio_dur:.1f}s)。")
        print("❄️ 正在冻结最后一帧画面以补齐结尾的音频...")
        
        # 1. 引入制作静态画面的必要模块 (放在文件最顶部的 import 也可以)
        from moviepy import ImageClip
        
        # 2. 计算需要补齐的时间差
        gap = audio_dur - video_dur
        
        # 3. 获取视频的最后一帧画面（稍微提前0.1秒截取，防止取到黑屏空帧）
        last_frame = final_video_no_audio.get_frame(video_dur - 0.1)
        
        # 4. 用最后一帧生成一个静态视频片段，时长为 gap
        freeze_clip = ImageClip(last_frame).with_duration(gap)
        
        # 5. 将原来的视频和静态结尾拼接在一起
        final_video_no_audio = concatenate_videoclips([final_video_no_audio, freeze_clip])
        
        # 6. 给延长后的完整视频配上未被截断的音频
        final_video = final_video_no_audio.with_audio(voiceover_audio)
        
    else:
        # 如果视频比音频长，那么只要按音频的长度把多余的视频截断即可
        print("✂️ 视频较长，将按照音频长度进行适配...")
        final_video = final_video_no_audio.subclipped(0, audio_dur).with_audio(voiceover_audio)

    # 6. 渲染并导出成片
    print(f"\n🚀 正在渲染最终视频至: {output_path}")
    print("⏳ 这可能需要几分钟时间，具体取决于你的 CPU 和视频分辨率...")
    
    # 使用 libx264 编码，preset="ultrafast" 可以大幅加快渲染速度
    final_video.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac", 
        preset="ultrafast", 
        threads=4,
        logger="bar" # 显示进度条
    )
    
    # 7. 释放内存
    video.close()
    voiceover_audio.close()
    final_video.close()
    print("\n✅ 渲染完成！你的全自动剪辑视频已生成！")

# ================= 运行区 =================
if __name__ == "__main__":
    # 你的文件路径
    MY_AUDIO = r"E:\系统下载\audio-1775719992471.mp3"
    MY_VIDEO = r"20260405_133300.mp4"
    
    # 大模型返回的 JSON
    MY_JSON = """
    {
  "clips_to_keep": [
    {
      "source_start_sec": 0.0,
      "source_end_sec": 1.1,
      "matched_subtitle": "家人们谁懂啊",
      "reason": "需要引入语境，选取00:00处展示对话界面的核心画面作为开场铺垫。"
    },
    {
      "source_start_sec": 9.0,
      "source_end_sec": 12.7,
      "matched_subtitle": "实测Gemma四二十六b搭配龙虾操控 浏览器",
      "reason": "字幕明确提及操控浏览器，通过语义映射，提前提取00:09处OpenClaw尝试操纵浏览器的核心动态画面。"
    },
    {
      "source_start_sec": 480.0,
      "source_end_sec": 483.4,
      "matched_subtitle": "龙虾回复乱成一团 指令完全不生效",
      "reason": "字幕表达操作失败，精准调度原素材08:00（480秒）处‘给出错误回复，未能执行任务’的画面，完美呼应指令不生效。"
    },
    {
      "source_start_sec": 401.0,
      "source_end_sec": 403.2,
      "matched_subtitle": "原来是模型和龙虾不兼容",
      "reason": "解析错误原因，提取06:41（401秒）处出现错误回复内容的画面，强化不兼容的无奈感。"
    },
    {
      "source_start_sec": 118.0,
      "source_end_sec": 119.9,
      "matched_subtitle": "试着修复一下 再试",
      "reason": "表达重新尝试的操作，匹配01:58（118秒）处用户重新在对话框中输入指令的核心画面。"
    },
    {
      "source_start_sec": 331.0,
      "source_end_sec": 333.3,
      "matched_subtitle": "好不容易能正常打开浏览器",
      "reason": "字幕表达难得的成功，匹配05:31（331秒）处成功弹出搜索窗口的积极反馈画面进行去水极简展示。"
    },
    {
      "source_start_sec": 14.0,
      "source_end_sec": 16.3,
      "matched_subtitle": "结果下一秒直接报错崩盘",
      "reason": "字幕表达突发崩溃，精准调度00:14处浏览器窗口弹出错误提示的核心瞬间，视觉冲击强。"
    },
    {
      "source_start_sec": 74.0,
      "source_end_sec": 75.0,
      "matched_subtitle": "折腾到崩溃",
      "reason": "字幕带有强烈情绪，提取01:14（74秒）处操作日志飞速滚动的画面，渲染繁杂和崩溃的氛围。"
    },
    {
      "source_start_sec": 277.0,
      "source_end_sec": 282.4,
      "matched_subtitle": "看来Gemma四二十六b加龙虾的兼容大坑 只能等官方更新来填了",
      "reason": "片尾总结与无奈放弃，选用04:37（277秒）处停留在终端日志处理界面的画面作为情绪收尾与结束。"
    }
  ]
}
    """
    
    # 导出到当前目录，名字叫 final_output.mp4
    create_final_video(MY_VIDEO, MY_AUDIO, MY_JSON, "final_output.mp4")