import os
import requests
import base64
import time
from playwright.sync_api import sync_playwright

# 1. 配置信息（从 GitHub Secrets 读取）
COZE_TOKEN = os.environ.get('COZE_TOKEN')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID')
IMGBB_KEY = os.environ.get('IMGBB_KEY') # 建议也存入Secret

def get_latest_cctv_url():
    """自动获取今日新闻联播的链接"""
    # 简单的搜索逻辑，直接访问央视网列表页
    search_api = "https://search.cctv.com/if7/search.php?qtext=%E6%96%B0%E9%97%BB%E8%81%94%E6%92%AD&type=video"
    # 这里为了演示，我们先假设能直接拿到，如果想更准，可以加一些正则解析
    # 建议初期先用一个固定链接测试，调通流程后再加动态抓取逻辑
    return "https://tv.cctv.com/lm/xwlb/index.shtml" 

def run():
    with sync_playwright() as p:
        print("正在启动云端浏览器...")
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # 访问链接
        target_url = "https://tv.cctv.com/lm/xwlb/index.shtml" # 目标列表页
        # 增加超时时间到 60 秒，并且只要 DOM 加载完就开始截图，不用等所有视频加载完
        page.goto(target_url, timeout=60000, wait_until='domcontentloaded')
        print(f"已打开页面: {target_url}")
        
        # 等待加载并截图
        time.sleep(5) 
        page.screenshot(path="screenshot.jpg", full_page=False)
        print("截图已保存为 screenshot.jpg")
        browser.close()

    # 2. 上传到图床
    print("正在上传图床...")
    with open("screenshot.jpg", "rb") as f:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_KEY},
            files={"image": base64.b64encode(f.read())}
        )
        img_url = res.json()['data']['url']
        print(f"图床链接获取成功: {img_url}")

    # 3. 触发 Coze 工作流
    print("正在通知 Coze 开始写简报...")
    coze_url = "https://api.coze.cn/v1/workflow/run"
    headers = {
        "Authorization": f"Bearer {COZE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "workflow_id": WORKFLOW_ID,
        "parameters": {
            "img_url": img_url
        }
    }
    coze_res = requests.post(coze_url, headers=headers, json=payload)
    print(f"Coze 任务已启动! 响应内容: {coze_res.text}")

if __name__ == "__main__":
    run()
