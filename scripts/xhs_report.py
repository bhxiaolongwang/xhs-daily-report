import os
import json
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import cm
import numpy as np

# ---------------- 配置 ----------------
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")
DATA_DIR = "data"
INPUT_FILE = "manual/input.json"
IMG_DIR = "charts"
TOTAL_IMG = os.path.join(IMG_DIR, "total_chart.png")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# ---------------- 微信推送 ----------------
def send_wechat(text, img_path=None):
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    data = {"title": "📊 小红书数据日报", "desp": text}
    files = {}
    if img_path and os.path.exists(img_path):
        files["file"] = open(img_path, "rb")
    requests.post(url, data=data, files=files)

# ---------------- 数据保存/读取 ----------------
def save_daily_data(data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(os.path.join(DATA_DIR, f"{date_str}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_historical(days=14):
    historical = []
    for i in range(days, 0, -1):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        path = os.path.join(DATA_DIR, f"{date_str}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                historical.append(json.load(f))
    return historical

# ---------------- 复刻选题 ----------------
def generate_replicate_ideas(title):
    return [f"{title}（💡复刻点子 {i+1}）" for i in range(3)]

# ---------------- 绘图 ----------------
def plot_total_trends(notes_titles, historical):
    dates = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(len(historical))]
    plt.figure(figsize=(12,6))

    today_notes = historical[-1]["notes"]
    yesterday_notes = historical[-2]["notes"] if len(historical)>=2 else []

    # 计算今天增量 & Top3
    increment_list = []
    for note in today_notes:
        yesterday_note = next((n for n in yesterday_notes if n["title"]==note["title"]), None)
        inc = note["like"] - yesterday_note["like"] if yesterday_note else note["like"]
        increment_list.append((note["title"], inc))
    top3_notes = [x[0] for x in sorted(increment_list, key=lambda x:x[1], reverse=True)[:3]]
    max_inc_val = max([x[1] for x in increment_list]) if increment_list else 0
    mid_inc_val = sorted([x[1] for x in increment_list])[len(increment_list)//2] if increment_list else 0
    top_note = top3_notes[0] if top3_notes else None

    # 颜色渐变函数
    def get_color(val):
        if max_inc_val == 0: return "gray"
        norm = min(max(val / max_inc_val, 0), 1)
        return cm.autumn(norm)  # autumn cmap 红-橙-黄

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

        yesterday_note = next((n for n in yesterday_notes if n["title"]==title), None)
        inc = likes[-1] - yesterday_note["like"] if yesterday_note else likes[-1]
        line_color = get_color(inc)

        # 背景渐变高亮（Top3异常笔记）
        if title in top3_notes:
            plt.gca().add_patch(
                patches.Rectangle((len(dates)-1-0.5, 0), 1, max(likes)*1.2,
                                  color=line_color, alpha=0.12, zorder=0)
            )

        # 绘制折线
        lw = 3 if title in top3_notes else 2
        alpha = 1 if title in top3_notes else 0.8
        plt.plot(dates, likes, '-o', label=f"{title} 👍", color=line_color, linewidth=lw, alpha=alpha)
        plt.plot(dates, collects, '-s', label=f"{title} ⭐", color=line_color, alpha=0.6, linewidth=1.5)
        plt.plot(dates, comments, '-^', label=f"{title} 💬", color=line_color, alpha=0.4, linewidth=1.5)

        # MA7 / MA14
        ma7 = [sum(likes[max(0,i-6):i+1])/min(7,i+1) for i in range(len(likes))]
        ma14 = [sum(likes[max(0,i-13):i+1])/min(14,i+1) for i in range(len(likes))]
        plt.plot(dates, ma7, '--', color=line_color, alpha=0.5, linewidth=1.2)
        plt.plot(dates, ma14, ':', color=line_color, alpha=0.5, linewidth=1.2)

        # 异常点 🔥
        for i,v in enumerate(likes):
            if len(ma7)>=i+1 and v>ma7[i]*1.5:
                plt.scatter(dates[i],v,s=120,color='red',zorder=5)
                plt.text(dates[i], v*1.02, "🔥", fontsize=12,fontweight='bold',ha='center')

        # 点赞最高点 🏆
        max_idx = likes.index(max(likes))
        plt.text(dates[max_idx], likes[max_idx]*1.05, "🏆", fontsize=12,fontweight='bold',ha='center')

        # Top1
        if title == top_note:
            plt.annotate("🏅 Top1",
                         xy=(len(dates)-1, likes[-1]*1.05),
                         xytext=(len(dates)-1, likes[-1]*1.18),
                         arrowprops=dict(facecolor='gold', shrink=0.05),
                         ha='center', fontsize=12,fontweight='bold', color='gold')

        # Top3异常箭头
        if title in top3_notes and title != top_note:
            plt.annotate("⬆️ Top异常",
                         xy=(len(dates)-1, likes[-1]*1.05),
                         xytext=(len(dates)-1, likes[-1]*1.12),
                         arrowprops=dict(facecolor=line_color, shrink=0.05),
                         ha='center', fontsize=10,fontweight='bold', color=line_color)

    plt.title("📊 小红书笔记趋势（终极可视化版）", fontsize=14,fontweight='bold')
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(alpha=0.3)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(TOTAL_IMG)
    plt.close()
    return TOTAL_IMG

# ---------------- 主函数 ----------------
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not os.path.exists(INPUT_FILE):
        notes = [{"title": "示例笔记 1", "like": 100, "collect":30, "comment":10}]
    else:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            notes = json.load(f)

    daily_data = {"time": now, "notes": notes}
    save_daily_data(daily_data)

    historical = load_historical(days=14)
    historical.append(daily_data)

    message = f"## 📅 今日时间\n{now}\n\n## 📌 内容分析\n"
    notes_titles = []

    yesterday_notes = historical[-2]["notes"] if len(historical)>=2 else []
    increment_list = []
    for note in notes:
        yesterday_note = next((n for n in yesterday_notes if n["title"]==note["title"]), None)
        inc = note["like"] - yesterday_note["like"] if yesterday_note else note["like"]
        increment_list.append((note["title"], inc))
    top3_notes = [x[0] for x in sorted(increment_list, key=lambda x:x[1], reverse=True)[:3]]
    top_note = top3_notes[0] if top3_notes else None

    replicate_summary = []
    for note in notes:
        title = note["title"]
        notes_titles.append(title)
        like = note["like"]
        collect = note["collect"]
        comment = note["comment"]

        yesterday_note = next((n for n in yesterday_notes if n["title"]==title), None)
        like_inc = like - yesterday_note["like"] if yesterday_note else like
        collect_inc = collect - yesterday_note["collect"] if yesterday_note else collect
        comment_inc = comment - yesterday_note["comment"] if yesterday_note else comment

        likes_history = [n["like"] for day in historical[-7:] for n in day["notes"] if n["title"]==title]
        ma7_like = sum(likes_history)/len(likes_history) if likes_history else 0
        abnormal = "🔥 异常好！" if like>ma7_like*1.5 else ""
        replicate_ideas = generate_replicate_ideas(title) if abnormal else []
        replicate_summary += replicate_ideas

        top_marker = "🏅 Top1" if title==top_note else ""
        message += f"**{title}** {abnormal} {top_marker}\n"
        message += f"👍 {like} (+{like_inc})   ⭐ {collect} (+{collect_inc})   💬 {comment} (+{comment_inc})\n"
        for idea in replicate_ideas:
            message += f"💡 {idea}\n"
        message += "—"*30 + "\n"

    if replicate_summary:
        message += "\n## 📝 今日复刻建议摘要\n"
        for i, idea in enumerate(replicate_summary,1):
            message += f"{i}. {idea}\n"

    img_path = plot_total_trends(notes_titles, historical)
    send_wechat(message, img_path)

if __name__ == "__main__":
    main()
