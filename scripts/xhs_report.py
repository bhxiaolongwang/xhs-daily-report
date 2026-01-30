import os
import requests
from datetime import datetime

SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")

def send_wechat(text):
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    requests.post(url, data={
        "title": "📊 小红书数据日报（示例）",
        "desp": text
    })

def main():
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ⚠️ 这是示例数据，用来验证“流程是否跑通”
    content = f"""
## 今日时间
{today}

## 最近 10 条内容（示例）
- 笔记 1：👍 132（+12） ⭐ 45（+5） 💬 18（+2）
- 笔记 2：👍 98（+7） ⭐ 30（+3） 💬 9（+1）
- 笔记 3：👍 210（🔥 异常）
- …

## 总结
- 今日整体互动：📈 上升
- 建议：复刻「异常内容」选题
"""

    send_wechat(content)

if __name__ == "__main__":
    main()
