import os
import json
import requests
from datetime import datetime

SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")
DATA_DIR = "data"

def send_wechat(text):
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    requests.post(url, data={
        "title": "📊 小红书数据日报",
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
    # ✅ now 的作用域在函数里
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 从人工输入文件读取
    input_file = "manual/input.json"
    if not os.path.exists(input_file):
        # 文件不存在就用示例数据
        notes = [
            {"title": "示例笔记 1", "like": 100, "collect": 30, "comment": 10}
        ]
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            notes = json.load(f)

    # 构建存档
    daily_data = {
        "time": now,
        "notes": notes
    }
    save_daily_data(daily_data)

    # 构建推送消息
    message = f"## 📅 今日时间\n{now}\n\n## 📌 最近内容\n"
    for n in notes:
        message += f"- {n['title']}: 👍 {n['like']} ⭐ {n['collect']} 💬 {n['comment']}\n"
    message += "\n✅ 数据已存档"

    send_wechat(message)

if __name__ == "__main__":
    main()
