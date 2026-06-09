import os
import requests
import time
from playwright.sync_api import sync_playwright

# 1. 配置信息（从环境变量读取）
COZE_TOKEN = os.environ.get('COZE_TOKEN')
WORKFLOW_ID = os.environ.get('WORKFLOW_ID')
IMGBB_KEY = os.environ.get('IMGBB_KEY')

def run():
    with sync_playwright() as p:
        print("正在启动云端浏览器...")
        browser = p.chromium.launch()
        page = browser.new_page()
        
        target_url = "https://tv.cctv.com/lm/xwlb/index.shtml"
        print(f"正在访问: {target_url}")
        
        # 增加超时容错
        try:
            page.goto(target_url, timeout=60000, wait_until='domcontentloaded')
            time.sleep(5) 
            page.screenshot(path="screenshot.jpg")
            print("✅ 截图已保存")
        except Exception as e:
            print(f"❌ 截图过程出错: {e}")
            page.screenshot(path="screenshot.jpg") # 强制截一张
        
        browser.close()

    # 2. 上传到图床
    print("正在上传图床...")
    if not IMGBB_KEY:
        print("❌ 错误：没找到 IMGBB_KEY，请检查 GitHub Secrets 配置！")
        return

    with open("screenshot.jpg", "rb") as f:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_KEY},
            files={"image": f}
        )
        
        # 核心调试：如果失败，打印出 ImgBB 到底说了什么
        if res.status_code != 200:
            print(f"❌ 上传失败！状态码: {res.status_code}")
            print(f"服务器返回信息: {res.text}")
            return

        data = res.json()
        img_url = data['data']['url']
        print(f"✅ 图床链接获取成功: {img_url}")

    # 3. 触发 Coze 工作流
    print("正在通知 Coze...")
    if not COZE_TOKEN or not WORKFLOW_ID:
        print("❌ 错误：缺少 Coze Token 或 Workflow ID")
        return

    coze_url = "https://api.coze.cn/v1/workflow/run"
    headers = {
        "Authorization": f"Bearer {COZE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "workflow_id": WORKFLOW_ID,
        "parameters": {"img_url": img_url}
    }
    
    response = requests.post(coze_url, headers=headers, json=payload)
    print(f"🚀 Coze 响应: {response.text}")

if __name__ == "__main__":
    run()
