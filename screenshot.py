import os
import requests
import time
import base64
from playwright.sync_api import sync_playwright

# 1. 配置信息 (从 GitHub Secrets 读取)
COZE_TOKEN = os.environ.get('COZE_TOKEN')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID')
IMGBB_KEY = os.environ.get('IMGBB_KEY')

def upload_to_imgbb(file_path):
    """上传本地图片到图床并返回 URL"""
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": IMGBB_KEY},
                files={"image": f}
            )
            if res.status_code == 200:
                return res.json()['data']['url']
            else:
                print(f"上传失败: {res.text}")
                return None
    except Exception as e:
        print(f"上传出错: {e}")
        return None

def run():
    with sync_playwright() as p:
        # 启动高清浏览器环境
        print("🚀 启动云端浏览器...")
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 步骤 1: 在列表页寻找“完整版”链接
        print("正在寻找今日【完整版】视频链接...")
        page.goto("https://tv.cctv.com/lm/xwlb/index.shtml", wait_until='domcontentloaded')
        try:
            # 自动定位包含“完整版”字样的第一个链接
            target_link = page.locator("a:has-text('完整版')").first.get_attribute("href")
            print(f"✅ 成功锁定目标: {target_link}")
        except Exception as e:
            print(f"❌ 自动寻找失败，使用保底逻辑: {e}")
            target_link = "https://tv.cctv.com/lm/xwlb/index.shtml"

        # 步骤 2: 进入视频页并等待
        page.goto(target_link, timeout=60000, wait_until='domcontentloaded')
        print("已进入视频页，正在等待 23 秒到达指定帧...")
        time.sleep(23) # 硬等23秒到达主播画面

        # 步骤 3: 连截 5 帧并裁剪 (16:9 核心区域)
        img_urls = []
        for i in range(5):
            path = f"frame_{i}.jpg"
            print(f"正在截取并裁剪第 {i+1} 帧...")
            # clip 参数精准裁剪：x,y 为起始坐标，width,height 为尺寸
            page.screenshot(path=path, clip={'x': 320, 'y': 180, 'width': 1280, 'height': 720})
            
            # 步骤 4: 上传图片
            url = upload_to_imgbb(path)
            if url:
                img_urls.append(url)
                print(f"✅ 第 {i+1} 帧上传成功: {url}")
            
            time.sleep(0.3) # 每帧间隔 0.3 秒
        
        browser.close()

    # 步骤 5: 将 5 张图的列表发给 Coze
    if not img_urls:
        print("❌ 未成功获取任何截图，任务中止")
        return

    print(f"正在通知 Coze 处理 {len(img_urls)} 张图片...")
    coze_url = "https://api.coze.cn/v1/workflow/run"
    headers = {
        "Authorization": f"Bearer {COZE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "workflow_id": WORKFLOW_ID,
        "parameters": {
            # 将 5 个 URL 用逗号连接成一个长字符串发给 Coze
            "img_list": ",".join(img_urls) 
        }
    }
    
    try:
        response = requests.post(coze_url, headers=headers, json=payload)
        print(f"🎉 任务全流程完成！Coze 响应: {response.text}")
    except Exception as e:
        print(f"❌ 最后发送给 Coze 时出错: {e}")

if __name__ == "__main__":
    run()
