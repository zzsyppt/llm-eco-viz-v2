"""
News Blueprint  ·  page & size & keyword filter
==============================================
- /news         : 首屏（默认 page=1, size=15）
- /news/api     : ?page=2&size=20
核心函数 fetch_llm_news() 会：
  • 先用 NewsAPI 查询串过滤 (OR 关键字)
  • 再本地二次过滤标题，确保关键词命中
  • 如果不足 size 条，自动翻下页补足（最大尝试 3 页，总 PageSize≤100）
"""
from __future__ import annotations
import os, requests, html
from datetime import datetime
from typing import List, Dict, Optional
from flask import Blueprint, jsonify, render_template, request

news_bp = Blueprint("news", __name__, url_prefix="/news")

# ---- 公共工具 ------------------------------------------------------------- #
def _clean(s: Optional[str]) -> str:
    """简单 HTML 实体反转 + 去换行"""
    return "" if s is None else html.unescape(s).replace("\n", " ").strip()

KEYWORDS = [
    "AI", "人工智能", "大模型", "生成式AI", "GPT", "ChatGPT", "LLM", "大语言模型", 
    "豆包", "深度学习", "机器学习", "深度神经网络", "Transformer", "Chatbot", 
    "对话系统", "自然语言处理", "NLP", "语音识别", "计算机视觉", "图像识别", 
    "自动驾驶", "智能机器人", 
    "人工智慧", "大型模型", "生成式AI", "大語言模型", "深度學習", "機器學習", 
    "深度神經網絡", "對話系統", "自然語言處理", "語音識別", "電腦視覺", 
    "圖像識別", "自動駕駛", "智慧機器人"
]

def _match(title: str) -> bool:
    """标题是否包含任一关键词（不区分大小写）"""
    low = title.lower()
    return any(k.lower() in low for k in KEYWORDS)

# ---- 抓取函数 ------------------------------------------------------------- #
def fetch_llm_news(page: int = 1, size: int = 15) -> List[Dict]:
    """
    尝试最多 3 页，返回 >= size 条（若 NewsAPI 本身不足则返回可用条数）
    """
    api_key = os.getenv("NEWSAPI_KEY") or "37cd0910baaa4ce69df4848485463008"
    if not api_key:
        print("[news] 缺少 NEWSAPI_KEY")
        return []

    query = "人工智能 大模型"
    url   = "https://newsapi.org/v2/everything"

    collected: List[Dict] = []
    cur_page, tries = page, 0

    while len(collected) < size and tries < 5:
        params = {
            "q": query, "language": "zh", "sortBy": "publishedAt",
            "pageSize": min(200, size*2),  # 一次多拿点，最多 100
            "page": cur_page, "apiKey": api_key,
        }
        try:
            r = requests.get(url, params=params, timeout=8)
            r.raise_for_status()
        except Exception as e:
            print("[news] NewsAPI error:", e)
            break

        raw_items = r.json().get("articles", [])
        # 二次精过滤
        for a in raw_items:
            if not a.get("urlToImage"):        # 必须有图
                continue
            title = a.get("title") or ""
            if not _match(title):
                continue
            collected.append({
                "title"   : _clean(title),
                "url"     : a.get("url"),
                "summary" : _clean(a.get("description")),
                "img"     : a.get("urlToImage"),
                "provider": a.get("source", {}).get("name", ""),
                "time"    : (a.get("publishedAt") or "")[:16].replace("T", " "),
            })
            if len(collected) >= size:
                break

        cur_page += 1
        tries    += 1

    return collected[:size]

# ---- 路由 ----------------------------------------------------------------- #
@news_bp.route("/", methods=["GET"])
def news_page():
    arts = fetch_llm_news(size=15)          # 首页默认 15 条
    return render_template(
        "news.html",
        articles=arts,
        total=len(arts),
        year=datetime.utcnow().year,
    )

@news_bp.route("/api", methods=["GET"])
def news_api():
    page = max(1, int(request.args.get("page", 1)))
    size = max(5, int(request.args.get("size", 15)))
    arts = fetch_llm_news(page, size)
    return jsonify({"total": len(arts), "articles": arts})
