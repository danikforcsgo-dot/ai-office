import requests
from datetime import datetime
from xml.etree import ElementTree
from config import LLM_ENABLED, LLM_FALLBACK


NEWS_SOURCES = {
    "investing": "https://www.investing.com/rss/news.rss",
    "forexlive": "https://www.forexlive.com/feed/news",
    "fxstreet": "https://www.fxstreet.com/rss/news",
    "dailyfx": "https://www.dailyfx.com/feeds/market-news",
}

PAIR_KEYWORDS = {
    "EUR/USD": {"required": ["EUR", "EURO", "EUROZONE", "ECB"], "optional": ["USD", "DOLLAR", "FED"]},
    "GBP/USD": {"required": ["GBP", "POUND", "STERLING", "CABLE", "BOE"], "optional": ["USD", "DOLLAR", "FED"]},
    "USD/JPY": {"required": ["JPY", "YEN", "BOJ"], "optional": ["USD", "DOLLAR", "FED"]},
    "USD/CHF": {"required": ["CHF", "FRANC", "SNB"], "optional": ["USD", "DOLLAR", "FED"]},
    "AUD/USD": {"required": ["AUD", "AUSSIE", "RBA"], "optional": ["USD", "DOLLAR", "FED"]},
    "USD/CAD": {"required": ["CAD", "LOONIE", "BOC"], "optional": ["USD", "DOLLAR", "FED"]},
    "NZD/USD": {"required": ["NZD", "KIWI", "RBNZ"], "optional": ["USD", "DOLLAR", "FED"]},
}

IMPACT_KEYWORDS = {
    "high": ["央行", "利率", "NFP", "CPI", "GDP", "inflation", "rate", "hike", "cut", "Fed", "ECB", "BOE", "BOJ", "央行", "货币政策", "занятость", "безработица"],
    "medium": ["trade", "deficit", "surplus", "PMI", "retail", "manufacturing", "торговля", "дефицит"],
    "low": ["speech", "conference", "interview", "выступление", "пресс-конференция"],
}


def fetch_rss_feed(url: str, timeout: int = 10) -> list[dict]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml,application/xml,text/xml,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            description = item.findtext("description", "")
            items.append({
                "title": title,
                "link": link,
                "date": pub_date,
                "description": description[:200],
            })
        return items
    except Exception as e:
        print(f"[WARN] RSS {url}: {e}")
        return []


def fetch_all_news() -> list[dict]:
    all_news = []
    loaded = 0
    for source, url in NEWS_SOURCES.items():
        items = fetch_rss_feed(url)
        if items:
            loaded += 1
        for item in items:
            item["source"] = source
        all_news.extend(items)
    print(f"[INFO] News: loaded {len(all_news)} items from {loaded}/{len(NEWS_SOURCES)} sources")
    def _parse_date(item):
        try:
            dt = datetime.strptime(item["date"], "%a, %d %b %Y %H:%M:%S %z")
            return dt.replace(tzinfo=None)
        except Exception:
            try:
                return datetime.strptime(item["date"], "%a, %d %b %Y %H:%M:%S")
            except Exception:
                return datetime(2000, 1, 1)

    all_news.sort(key=_parse_date, reverse=True)
    return all_news[:50]


def classify_news_for_pair(news_item: dict, pair_name: str) -> dict:
    kw_config = PAIR_KEYWORDS.get(pair_name)
    if not kw_config:
        return {"pair": pair_name, "title": news_item.get("title", ""), "source": news_item.get("source", "unknown"), "date": news_item.get("date", ""), "impact": "low", "relevance": 0, "sentiment": "neutral", "sentiment_score": 0}

    if LLM_ENABLED:
        try:
            from llm_client import get_llm, news_llm_analysis
            llm = get_llm()
            llm_result = news_llm_analysis([news_item], pair_name, llm)
            if llm_result and llm_result.get("sentiment") != "NEUTRAL":
                return {
                    "pair": pair_name,
                    "title": news_item["title"],
                    "source": news_item.get("source", "unknown"),
                    "date": news_item.get("date", ""),
                    "impact": llm_result.get("impact", "low"),
                    "relevance": 3 if llm_result.get("impact") == "high" else 2 if llm_result.get("impact") == "medium" else 1,
                    "sentiment": llm_result.get("sentiment", "neutral"),
                    "sentiment_score": 1.0 if llm_result.get("sentiment") == "positive" else -1.0 if llm_result.get("sentiment") == "negative" else 0,
                    "llm_summary": llm_result.get("summary", ""),
                    "llm": True,
                }
        except Exception as e:
            if not LLM_FALLBACK:
                raise
            print(f"[WARN] LLM news analysis failed: {e}")

    title = news_item.get("title", "").upper()
    desc = news_item.get("description", "").upper()
    text = title + " " + desc
    has_required = any(kw.upper() in text for kw in kw_config["required"])
    has_optional = any(kw.upper() in text for kw in kw_config["optional"])
    if has_required and has_optional:
        relevance = 3
    elif has_required:
        relevance = 2
    elif has_optional:
        relevance = 1
    else:
        relevance = 0
    impact = "low"
    for level, kws in IMPACT_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in text.lower():
                impact = level
                break
        if impact != "low":
            break

    positive = ["rally", "surge", "jump", "gain", "strong", "bullish", "rise", "soar", "upbeat",
                "рост", "укрепление", "бычий", "рост", "взлёт", "прибыль"]
    negative = ["fall", "drop", "decline", "weak", "bearish", "slump", "crash", "plunge", "downturn",
                "падение", "ослабление", "медвежий", "снижение", "кризис", "убыток"]
    text_lower = text.lower()
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    total = pos_count + neg_count
    if total > 0:
        score = (pos_count - neg_count) / total
    else:
        score = 0
    if score > 0.2:
        sentiment = "positive"
    elif score < -0.2:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "pair": pair_name,
        "title": news_item["title"],
        "source": news_item.get("source", "unknown"),
        "date": news_item.get("date", ""),
        "impact": impact,
        "relevance": relevance,
        "sentiment": sentiment,
        "sentiment_score": round(score, 2),
    }


def analyze_news_for_all_pairs(prices: list[dict]) -> list[dict]:
    news = fetch_all_news()
    if not news:
        return [{"pair": p["name"], "news_count": 0, "high_impact": 0, "sentiment_summary": "NO DATA"} for p in prices]
    results = []
    for p in prices:
        pair_name = p["name"]
        classified = [classify_news_for_pair(n, pair_name) for n in news]
        relevant = [c for c in classified if c["relevance"] >= 2]
        high_impact = [c for c in relevant if c["impact"] == "high"]
        sentiments = [c["sentiment"] for c in relevant]
        pos = sentiments.count("positive")
        neg = sentiments.count("negative")
        if pos > neg:
            summary = "POSITIVE"
        elif neg > pos:
            summary = "NEGATIVE"
        else:
            summary = "NEUTRAL"
        if summary == "POSITIVE" and len(high_impact) > 0:
            signal = "BUY"
        elif summary == "NEGATIVE" and len(high_impact) > 0:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        avg_score = 0
        scores = [n.get("sentiment_score", 0) for n in relevant]
        if scores:
            avg_score = sum(scores) / len(scores)

        results.append({
            "pair": pair_name,
            "news_count": len(relevant),
            "high_impact": len(high_impact),
            "sentiment_summary": summary,
            "signal": signal,
            "avg_sentiment": round(avg_score, 2),
            "top_news": relevant[:3],
        })
    return results


def format_news(results: list[dict]) -> str:
    lines = []
    for r in results:
        icon = "+" if r["sentiment_summary"] == "POSITIVE" else "-" if r["sentiment_summary"] == "NEGATIVE" else "="
        lines.append(f"  {icon} {r['pair']}: {r['news_count']} новостей, {r['high_impact']} высокого влияния, sentiment={r['sentiment_summary']}")
        for n in r.get("top_news", [])[:2]:
            lines.append(f"    [{n['impact']}] {n['title'][:80]}")
    return "\n".join(lines)
