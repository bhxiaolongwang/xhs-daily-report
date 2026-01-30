import os
import json
import requests
from datetime import datetime

SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")
DATA_DIR = "data"

def send_wechat(text):
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    requests.post(url, data={
        "title": "📊 小红书数据日报（示例）",
        "desp": text
    })

def save_daily_data(data):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = f"{DATA_DIR}/{date_str}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 示例数据（之后会替换为真实小红书数据）
    notes = [
        {"title": "笔记 1", "like": 132, "collect": 45, "comment": 18},
        {"title": "笔记 2", "like": 98, "collect": 30, "comment": 9},
        {"title": "笔记 3", "like": 210, "collect": 80, "comment": 40},
    ]

    daily_data = {
        "time": now,
        "notes": notes
    }

    save_daily_data(daily_data)

    message = f"""
## 📅 今日时间
{now}

## 📌 最近内容（示例）
""" 

    for n in notes:
        message += f"- {n['title']}：👍 {n['like']} ⭐ {n['collect']} 💬 {n['comment']}\n"

    message += "\n✅ 数据已存档，可用于增量与趋势分析"

    send_wechat(message)

if __name__ == "__main__":
    main()
