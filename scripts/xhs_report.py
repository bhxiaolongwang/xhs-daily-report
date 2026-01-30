import os
import json
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Server酱Key
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")
DATA_DIR = "data"
INPUT_FILE = "manual/input.json"
IMG_DIR = "charts"

# 确保文件夹存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

# 微信推送函数
def send_wechat(text, img_path=None):
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    data = {"title": "📊 小红书数据日报", "desp": text}
    files = {}
    if img_path and os.path.exists(img_path):
        files["file"] = open(img_path, "rb")
    requests.post(url, data=data, files=files)

# 保存每日数据
def save_daily_data(data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(DATA_DIR, f"{date_str}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 读取历史数据
def load_historical(days=14):
    historical = []
    for i in range(days, 0, -1):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        file_path = os.path.join(DATA_DIR, f"{date_str}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                historical.append(json.load(f))
    return historical

# 生成复刻选题
def generate_replicate_ideas(title):
    return [f"{title}（复刻点子 {i+1}）" for i in range(3)]

# 绘制趋势图
def plot_trends(title, historical):
    dates = []
    likes = []
    collects = []
    comments = []
    for day in historical:
        note = next((n for n in day["notes"] if n["title"]==title), None)
        if note:
            dates.append(day["time"].split()[0])
            likes.append(note["like"])
            collects.append(note["collect"])
            comments.append(note["comment"])
    if not dates:
        return None
    plt.figure(figsize=(6,4))
    plt.plot(dates, likes, '-o', label='👍 Likes')
    plt.plot(dates, collects, '-s', label='⭐ Collects')
    plt.plot(dates, comments, '-^', label='💬 Comments')
    # 异常标注
    ma7_like = sum(likes[-7:])/min(len(likes),7)
    for i, v in enumerate(likes):
        if v > ma7_like*1.5:
            plt.text(dates[i], v, "🔥", fontsize=12)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    safe_title = title[:10].replace(" ", "_")
    img_path = os.path.join(IMG_DIR, f"{safe_title}.png")
    plt.savefig(img_path)
    plt.close()
    return img_path

# 主函数
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 读取今天数据
    if not os.path.exists(INPUT_FILE):
        notes = [{"title": "示例笔记 1", "like": 100, "collect": 30, "comment": 10}]
    else:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            notes = json.load(f)

    # 保存今日快照
    daily_data = {"time": now, "notes": notes}
    save_daily_data(daily_data)

    # 历史数据
    historical = load_historical(days=14)
    historical.append(daily_data)  # 包括今天

    # 遍历笔记
    for note in notes:
        title = note["title"]
        like = note["like"]
        collect = note["collect"]
        comment = note["comment"]

        # 昨日数据
        yesterday_data = historical[-2]["notes"] if len(historical)>=2 else []
        yesterday_note = next((n for n in yesterday_data if n["title"]==title), None)
        like_inc = like - yesterday_note["like"] if yesterday_note else like
        collect_inc = collect - yesterday_note["collect"] if yesterday_note else collect
        comment_inc = comment - yesterday_note["comment"] if yesterday_note else comment

        # MA7 计算
        likes_history = [n["like"] for day in historical[-7:] for n in day["notes"] if n["title"]==title]
        ma7_like = sum(likes_history)/len(likes_history) if likes_history else 0
        abnormal = "🔥 异常好！" if like > ma7_like*1.5 else ""
        replicate_ideas = generate_replicate_ideas(title) if abnormal else []

        # 构建文字
        text = f"- {title}\n👍 {like} (+{like_inc}) ⭐ {collect} (+{collect_inc}) 💬 {comment} (+{comment_inc}) {abnormal}"
        for idea in replicate_ideas:
            text += f"\n💡 {idea}"

        # 生成图表
        img_path = plot_trends(title, historical)

        # 微信推送
        send_wechat(text, img_path)

if __name__ == "__main__":
    main()
