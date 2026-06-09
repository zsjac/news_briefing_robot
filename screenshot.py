import os
import requests
import time
from playwright.sync_api import sync_playwright

# 1. 配置信息
COZE_TOKEN = os.environ.get('COZE_TOKEN')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID')
IMGBB_KEY = os.environ.get('IMGBB_KEY')

def upload_to_imgbb(file_path):
    with open(file_path, "rb") as f:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_KEY},
            files={"image": f}
        )
        return res.json()['data']['url'] if res.status_code == 200 else None

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # 模拟高清显示器
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # 步骤 1: 寻找今日完整版
        page.goto("https://tv.cctv.com/lm/xwlb/index.shtml", wait_until='domcontentloaded')
        target_link = page.locator("a:has-text('完整版')").first.get_attribute("href")
        
        # 步骤 2: 进入视频页
        print(f"正在进入视频页: {target_link}")
        page.goto(target_link, wait_until='domcontentloaded')
        
        # 【关键技术】通过 JS 强制视频跳转到 34 秒并静音
        # 34 秒通常是主播名字条出现的稳定时刻
        page.evaluate("""() => {
            const video = document.querySelector('video');
            if (video) {
                video.muted = true;
                video.currentTime = 34; 
                video.pause(); 
            }
        }""")
        
        # 等待 3 秒让画面渲染稳定
        time.sleep(3)

        # 步骤 3: 连截 5 帧 (直接针对视频元素截图)
        img_urls = []
        # 定位视频播放器元素，直接对它截图就没有黑边和进度条了
        video_element = page.locator("video")
        
        for i in range(5):
            path = f"frame_{i}.jpg"
            # 【核心修改】只对 video 元素截图，自动获得 16:9 比例
            video_element.screenshot(path=path)
            
            # 上传
            url = upload_to_imgbb(path)
            if url: img_urls.append(url)
            
            # 微调时间（每帧走 0.2 秒）
            page.evaluate("document.querySelector('video').currentTime += 0.2")
            time.sleep(0.5)

        browser.close()

    # 步骤 4: 通知 Coze
    if img_urls:
        coze_url = "https://api.coze.cn/v1/workflow/run"
        headers = {"Authorization": f"Bearer {COZE_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "workflow_id": WORKFLOW_ID,
            "parameters": {"img_list": ",".join(img_urls)}
        }
        requests.post(coze_url, headers=headers, json=payload)
        print(f"✅ 成功发送 {len(img_urls)} 张纯净截图到 Coze")

if __name__ == "__main__":
    run()
