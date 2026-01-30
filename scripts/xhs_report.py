import os
import json
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 配置
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")
DATA_DIR = "data"
INPUT_FILE = "manual/input.json"
IMG_DIR = "charts"
TOTAL_IMG = os.path.join(IMG_DIR, "total_chart.png")

# 确保文件夹存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

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

# 绘制总趋势图（加 MA7 / MA14）
def plot_total_trends(notes_titles, historical):
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(len(historical))]
    plt.figure(figsize=(10,6))
    colors = ['r','g','b','c','m','y','k']

    for idx, title in enumerate(notes_titles):
        likes, collects, comments = [], [], []
        for day in historical:
            note = next((n for n in day["notes"] if n["title"]==title), None)
            if note:
                likes.append(note["like"])
                collects.append(note["collect"])
                comments.append(note["comment"])
            else:
                likes.append(0)
                collects.append(0)
                comments.append(0)

        color = colors[idx % len(colors)]
        plt.plot(dates, likes, '-o', label=f"{title} 👍", color=color)
        plt.plot(dates, collects, '-s', label=f"{title} ⭐", color=color, alpha=0.6)
        plt.plot(dates, comments, '-^', label=f"{title} 💬", color=color, alpha=0.4)

        # MA7 / MA14
        ma7 = [sum(likes[max(0,i-6):i+1])/min(7,i+1) for i in range(len(likes))]
        ma14 = [sum(likes[max(0,i-13):i+1])/min(14,i+1) for i in range(len(likes))]
        plt.plot(dates, ma7, '--', color=color, alpha=0.5, label=f"{title} MA7")
        plt.plot(dates, ma14, ':', color=color, alpha=0.5, label=f"{title} MA14")

        # 异常标注
        for i, v in enumerate(likes):
            if len(ma7)>=i+1 and v > ma7[i]*1.5:
                plt.text(dates[i], v, "🔥", fontsize=10)

    plt.title("📊 小红书笔记趋势（含 MA7 / MA14）")
    plt.xticks(rotation=45)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(TOTAL_IMG)
    plt.close()
    return TOTAL_IMG

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
    historical.append(daily_data)

    # 构建文字内容
    message = f"## 📅 今日时间\n{now}\n\n## 📌 内容分析\n"
    notes_titles = []

    for note in notes:
        title = note["title"]
        notes_titles.append(title)
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

        message += f"- {title}\n👍 {like} (+{like_inc}) ⭐ {collect} (+{collect_inc}) 💬 {comment} (+{comment_inc}) {abnormal}\n"
        for idea in replicate_ideas:
            message += f"💡 {idea}\n"

    # 生成总图
    img_path = plot_total_trends(notes_titles, historical)

    # 微信推送文字 + 总图
    send_wechat(message, img_path)

if __name__ == "__main__":
    main()
