import os, requests, subprocess, time

# 1. 变量读取
COZE_TOKEN = os.environ.get('COZE_TOKEN')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID')
IMGBB_KEY = os.environ.get('IMGBB_KEY')

def run():
    # 步骤 A: 找到今日新闻联播页面 (以列表页作为入口)
    # 央视网列表页
    list_page = "https://tv.cctv.com/lm/xwlb/index.shtml"
    
    # 步骤 B: 使用 yt-dlp 配合 ffmpeg 抽帧
    # -ss 00:00:34: 跳到34秒 | -frames:v 5: 截5帧 | -q:v 2: 高质量
    # 我们直接让 yt-dlp 寻找页面内的视频流并交给 ffmpeg 处理
    print("🚀 正在提取高清原始视频帧...")
    
    # 这是一个组合命令：找链接 -> 传给 ffmpeg -> 输出 5 张图
    # 我们尝试从列表页自动抓取最新的地址
    try:
        cmd = f'ffmpeg -ss 00:00:34 -i $(yt-dlp -g --playlist-items 1 "{list_page}") -frames:v 5 -q:v 2 frame_%d.jpg'
        subprocess.run(cmd, shell=True, check=True)
        print("✅ 高清帧提取完成")
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return

    # 步骤 C: 批量上传到 ImgBB
    img_urls = []
    for i in range(1, 6):
        file_name = f"frame_{i}.jpg"
        if os.path.exists(file_name):
            with open(file_name, "rb") as f:
                res = requests.post("https://api.imgbb.com/1/upload", params={"key": IMGBB_KEY}, files={"image": f})
                if res.status_code == 200:
                    img_urls.append(res.json()['data']['url'])
    
    # 步骤 D: 通知 Coze
    if img_urls:
        print(f"✅ 成功获取 {len(img_urls)} 张高清图，通知 Coze...")
        requests.post(
            "https://api.coze.cn/v1/workflow/run",
            headers={"Authorization": f"Bearer {COZE_TOKEN}", "Content-Type": "application/json"},
            json={"workflow_id": WORKFLOW_ID, "parameters": {"img_list": ",".join(img_urls)}}
        )

if __name__ == "__main__":
    run()
