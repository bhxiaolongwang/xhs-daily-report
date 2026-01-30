import os
import json
import requests
from datetime import datetime, timedelta

SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")
DATA_DIR = "data"
INPUT_FILE = "manual/input.json"

def send_wechat(text):
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    requests.post(url, data={"title": "📊 小红书数据日报", "desp": text})

def save_daily_data(data):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = f"{DATA_DIR}/{date_str}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_previous_data(days=7):
    result = []
    for i in range(days, 0, -1):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        file_path = f"{DATA_DIR}/{date_str}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                result.append(json.load(f))
    return result

def calculate_ma(note_title, historical, field, window):
    values = []
    for day in historical[-window:]:
        for note in day["notes"]:
            if note["title"] == note_title:
                values.append(note.get(field, 0))
                break
    if values:
        return sum(values)/len(values)
    return 0

def generate_replicate_ideas(title):
    # 简单示例，可自定义生成策略
    return [f"{title}（复刻点子 {i+1}）" for i in range(3)]

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 读取今天数据
    if not os.path.exists(INPUT_FILE):
        notes = [{"title": "示例笔记 1", "like": 100, "collect": 30, "comment": 10}]
    else:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            notes = json.load(f)

    # 保存今天快照
    daily_data = {"time": now, "notes": notes}
    save_daily_data(daily_data)

    # 读取历史数据（7天）
    historical = load_previous_data(days=14)

    message = f"## 📅 今日时间\n{now}\n\n## 📌 内容分析\n"

    for note in notes:
        title = note["title"]
        like = note["like"]
        collect = note["collect"]
        comment = note["comment"]

        # 增量计算（昨天 vs 今天）
        yesterday_data = historical[-1]["notes"] if historical else []
        yesterday_note = next((n for n in yesterday_data if n["title"]==title), None)
        like_inc = like - yesterday_note["like"] if yesterday_note else like
        collect_inc = collect - yesterday_note["collect"] if yesterday_note else collect
        comment_inc = comment - yesterday_note["comment"] if yesterday_note else comment

        # 移动平均
        ma7_like = calculate_ma(title, historical, "like", 7)
        ma14_like = calculate_ma(title, historical, "like", 14)

        # 异常标注
        abnormal = "🔥 异常好！" if like > ma7_like*1.5 else ""

        # 生成复刻选题
        replicate_ideas = generate_replicate_ideas(title) if abnormal else []

        message += f"- {title}\n"
        message += f"  👍 {like} (+{like_inc}) ⭐ {collect} (+{collect_inc}) 💬 {comment} (+{comment_inc}) {abnormal}\n"
        if replicate_ideas:
            for idea in replicate_ideas:
                message += f"    💡 {idea}\n"

    message += "\n✅ 数据已存档，可用于趋势分析与选题优化"

    send_wechat(message)

if __name__ == "__main__":
    main()
