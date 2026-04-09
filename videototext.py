import cv2
import numpy as np
import os
import base64
import json
from openai import OpenAI

# ================= 配置区域 =================
API_BASE_URL = "http://127.0.0.1:1234/v1"
API_KEY = "lmstudio"
MODEL_ID = "unsloth/gemma-4-26B-A4B-it-GGUF" # 你的模型 ID

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def create_grid_image(frames, batch_index, output_folder, target_width=960, target_height=540):
    """将最多 4 张图片拼成 2x2 的宫格图，不足 4 张用黑图填充"""
    # 创建纯黑图片作为填充底板
    black_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    resized_frames = []

    for frame in frames:
        # 强制缩放至统一尺寸，防止拼接报错
        resized = cv2.resize(frame, (target_width, target_height))
        resized_frames.append(resized)

    # 如果不足 4 张，用黑底填充
    while len(resized_frames) < 4:
        resized_frames.append(black_frame)

    # 拼接：先横向拼成两排，再纵向拼成完整的一张
    top_row = cv2.hconcat([resized_frames[0], resized_frames[1]])
    bottom_row = cv2.hconcat([resized_frames[2], resized_frames[3]])
    grid_img = cv2.vconcat([top_row, bottom_row])

    # 保存宫格图
    grid_path = os.path.join(output_folder, f"grid_{batch_index:03d}.jpg")
    cv2.imwrite(grid_path, grid_img)
    return grid_path

def extract_and_grid_video(video_path, output_folder, interval_sec=5):
    """按指定秒数抽帧，打时间戳，并生成宫格图"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    frame_count = 0
    current_batch_frames = []
    grid_paths = []
    batch_index = 1

    print(f"开始处理视频: {video_path} (每 {interval_sec} 秒抽 1 帧)")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 按时间间隔抽帧
        if frame_count % int(fps * interval_sec) == 0:
            current_time_sec = int(frame_count // fps)
            mins, secs = divmod(current_time_sec, 60)
            time_str = f"{mins:02d}:{secs:02d}"

      
            # 获取文字大小
            (text_width, text_height), baseline = cv2.getTextSize(time_str, cv2.FONT_HERSHEY_SIMPLEX, 3.0, 5)
            # 画一个黑色实心矩形作为底色
            cv2.rectangle(frame, (40, 80 - text_height - 10), (50 + text_width + 10, 80 + baseline), (0, 0, 0), -1)
            # 在黑框上写白字（或者红字）
            cv2.putText(frame, time_str, (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 3.0, (255, 255, 255), 5, cv2.LINE_AA)
            current_batch_frames.append(frame)

            # 凑齐 4 张，生成一次宫格图
            if len(current_batch_frames) == 4:
                grid_path = create_grid_image(current_batch_frames, batch_index, output_folder)
                grid_paths.append(grid_path)
                print(f"已生成第 {batch_index} 张宫格图...")
                current_batch_frames = []
                batch_index += 1

        frame_count += 1

    cap.release()

    # 处理最后不足 4 张的尾巴
    if len(current_batch_frames) > 0:
        grid_path = create_grid_image(current_batch_frames, batch_index, output_folder)
        grid_paths.append(grid_path)
        print(f"已生成最后 1 张宫格图 (包含黑底填充)...")

    return grid_paths

def analyze_grid_with_ai(grid_path, focus_points):
    """向大模型提交一张宫格图和关注点提示词"""
    base64_image = encode_image_to_base64(grid_path)
    
    # 将你的业务需求动态注入 Prompt
    prompt = f"""
    你现在是一个严格的视频审查员。我传给你的是一张 2x2 的宫格图。
    里面包含 4 张按时间顺序排列的截图（顺序：1.左上 -> 2.右上 -> 3.左下 -> 4.右下）。

    【强制规则 - 仔细阅读】：
    1. 每一张子图的左上角都有一个带有黑色背景的时间戳（如 00:04）。你**只允许**读取这个位置的时间！绝对禁止读取 Windows 任务栏的时间或任何其他数字！
    2. 即使画面没变化，你也必须输出 4 条记录，对应 4 张子图的确切时间。
    3. 状态判定：只要描述中出现“保持不变”、“无变化”、“空白”、“一致”，status 必须输出 "useless"。只有在操作发生时才是 "core"。

    【请关注以下重点】：
    {focus_points}

    请严格输出 JSON 数组，格式如下：
    [
    {{"time": "读取左上角时间1", "action": "描述", "status": "core/useless"}},
    {{"time": "读取右上角时间2", "action": "描述", "status": "core/useless"}},
    ...
    ]
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API 调用失败: {e}")
        return "[]"

def process_video_pipeline(video_path, focus_points):
    """执行全流程"""
    temp_folder = "./grid_temp"
    
    # 1. 抽帧并生成宫格图
    grid_images = extract_and_grid_video(video_path, temp_folder, interval_sec=5)
    
    all_results = []
    
    print("\n================ 开始 AI 解读 ================")
    # 2. 依次将宫格图发给大模型（因为每张图包含 20 秒内容，一次发一张即可，防爆显存）
    for i, grid_path in enumerate(grid_images):
        print(f"正在让 AI 解读第 {i+1}/{len(grid_images)} 张宫格图...")
        result_text = analyze_grid_with_ai(grid_path, focus_points)
        
        # 清洗 JSON 格式
        clean_text = result_text.replace('```json', '').replace('```', '').strip()
        try:
            batch_log = json.loads(clean_text)
            if isinstance(batch_log, list):
                all_results.extend(batch_log)
        except json.JSONDecodeError:
            print(f"警告：此张图 JSON 解析失败，模型原始返回：\n{result_text}")
            
    print("\n================ 最终 AI 解读 JSON 报告 ================")
    final_json_str = json.dumps(all_results, ensure_ascii=False, indent=2)
    print(final_json_str)
    
    # 将结果保存到文件
    with open("video_analysis_report.json", "w", encoding="utf-8") as f:
        f.write(final_json_str)
    print("分析报告已保存至 video_analysis_report.json")

# ================= 执行入口 =================
if __name__ == "__main__":
    # 替换为你实际的视频路径
    my_video = r"20260405_133300.mp4"
    
    # 这里动态传入你想让 AI 关注的核心点（比如录教程和展示功能的区别）
    my_focus = """
    这是我录制的一段 ai模型和openclaw能力的展示。
    重点关注：openclaw的对话过程，对话中的错误回复，openclaw成功操纵浏览器
    忽略：右下角的系统时间跳动、系统桌面背景和图标。
    """
    
    process_video_pipeline(my_video, my_focus)