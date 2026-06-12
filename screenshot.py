import os
import requests
import subprocess
import time

# 1. 从环境变量读取配置 (由 main.yml 传入)
COZE_TOKEN = os.environ.get('COZE_TOKEN')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID')
IMGBB_KEY = os.environ.get('IMGBB_KEY')

# 获取来自 Coze 远程指令的网址 (如果存在)
REMOTE_URL = os.environ.get('TARGET_URL')

def run():
    # --- 步骤 A: 确定抓取目标 ---
    if REMOTE_URL and REMOTE_URL.strip():
        # 如果 Coze 传了具体的 .shtml 链接，直接使用
        target_page = REMOTE_URL.strip()
        print(f"📡 接收到 Coze 远程指令，抓取目标: {target_page}")
    else:
        # 如果是定时运行，去列表页找最新的
        target_page = "https://tv.cctv.com/lm/xwlb/index.shtml"
        print(f"⏰ 定时任务运行，入口页面: {target_page}")

    # --- 步骤 B: 使用 FFmpeg 执行高清抽帧 ---
    # 我们使用 yt-dlp 找到视频流，然后让 ffmpeg 在 34 秒处连截 5 帧
    print("🚀 正在提取高清原始视频帧（1080P无损模式）...")
    
    try:
        # 核心命令：
        # --playlist-items 1: 确保只抓取页面中最新的那个视频
        # -ss 00:00:34: 精准定位到主播画面
        # -q:v 2: 最高质量参数
        cmd = f'ffmpeg -ss 00:00:34 -i $(yt-dlp -g --playlist-items 1 "{target_page}") -frames:v 5 -q:v 2 frame_%d.jpg'
        
        # 执行命令
        subprocess.run(cmd, shell=True, check=True)
        print("✅ 高清帧提取成功")
    except Exception as e:
        print(f"❌ 视频流处理失败: {e}")
        return

    # --- 步骤 C: 批量上传到 ImgBB 图床 ---
    img_urls = []
    print("正在上传至图床...")
    for i in range(1, 6):
        file_name = f"frame_{i}.jpg"
        if os.path.exists(file_name):
            try:
                with open(file_name, "rb") as f:
                    res = requests.post(
                        "https://api.imgbb.com/1/upload", 
                        params={"key": IMGBB_KEY}, 
                        files={"image": f}
                    )
                    if res.status_code == 200:
                        url = res.json()['data']['url']
                        img_urls.append(url)
                        print(f"  - 第 {i} 张上传成功: {url}")
            except Exception as e:
                print(f"  - 第 {i} 张上传出错: {e}")
    
    # --- 步骤 D: 将结果反馈给 Coze ---
    if img_urls:
        print(f"✅ 共获取 {len(img_urls)} 张高清图，正在通知 Coze 处理...")
        coze_url = "https://api.coze.cn/v1/workflow/run"
        headers = {
            "Authorization": f"Bearer {COZE_TOKEN}", 
            "Content-Type": "application/json"
        }
        payload = {
            "workflow_id": WORKFLOW_ID,
           "parameters": {
                            "img_list": img_urls  # 直接传列表，不要加 .join
                         }
            }
        }
        
        try:
            response = requests.post(coze_url, headers=headers, json=payload)
            print(f"🎉 任务闭环完成！Coze 响应: {response.text}")
        except Exception as e:
            print(f"❌ 反馈给 Coze 失败: {e}")
    else:
        print("❌ 未能获取到任何有效图片链接，流程中止。")

if __name__ == "__main__":
    run()
