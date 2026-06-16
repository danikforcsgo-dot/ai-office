import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from m15_data import get_multi_tf_data, detect_htf_bias, detect_bos_choch, detect_fvg, detect_order_blocks, detect_liquidity_zones


def multi_tf_analysis(symbol: str, pair_name: str) -> dict:
    data = get_multi_tf_data(symbol)
    d1 = data["d1"]
    h4 = data["h4"]
    m15 = data["m15"]

    d1_bias = detect_htf_bias(d1)
    h4_bias = detect_htf_bias(h4) if not h4.empty else "UNKNOWN"
    m15_structure = detect_bos_choch(m15)
    fvgs = detect_fvg(m15)
    obs = detect_order_blocks(m15)
    liquidity = detect_liquidity_zones(m15)

    m15_signal = "NEUTRAL"
    if "BULLISH" in m15_structure.get("bos", "") or "BULLISH" in m15_structure.get("choch", ""):
        m15_signal = "BUY"
    elif "BEARISH" in m15_structure.get("bos", "") or "BEARISH" in m15_structure.get("choch", ""):
        m15_signal = "SELL"

    htf_signal = "NEUTRAL"
    if d1_bias == "BULLISH" and h4_bias == "BULLISH":
        htf_signal = "BUY"
    elif d1_bias == "BEARISH" and h4_bias == "BEARISH":
        htf_signal = "SELL"

    conflict = (htf_signal != "NEUTRAL" and m15_signal != "NEUTRAL" and htf_signal != m15_signal)

    if conflict:
        if htf_signal == "BUY" and m15_signal == "SELL":
            resolution = "HTF бычий, M15 медвежий — ЖДАТЬ отката до зоны спроса на M15 перед покупкой"
        else:
            resolution = "HTF медвежий, M15 бычий — ЖДАТЬ отскока к зоне предложения на M15 перед продажей"
    elif htf_signal == m15_signal and htf_signal != "NEUTRAL":
        resolution = f"СОВПАДЕНИЕ: HTF и M15 указывают {htf_signal} — ВХОД РЕКОМЕНДОВАН"
    else:
        resolution = "Нет чёткого сигнала — ЖДАТЬ"

    return {
        "pair": pair_name,
        "symbol": symbol,
        "d1_bias": d1_bias,
        "h4_bias": h4_bias,
        "m15_bos": m15_structure.get("bos", "NO DATA"),
        "m15_choch": m15_structure.get("choch", "NO DATA"),
        "m15_signal": m15_signal,
        "htf_signal": htf_signal,
        "conflict": conflict,
        "resolution": resolution,
        "fvgs": fvgs,
        "order_blocks": obs,
        "liquidity": liquidity,
    }


def run_multi_tf_analysis(prices: list[dict]) -> list[dict]:
    results = []
    for p in prices:
        try:
            result = multi_tf_analysis(p["symbol"], p["name"])
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Multi-TF {p['name']}: {e}")
    return results


def format_multi_tf(results: list[dict]) -> str:
    lines = []
    for r in results:
        status = "КОНФЛИКТ!" if r["conflict"] else "OK"
        color = "RED" if r["conflict"] else "GREEN"
        lines.append(f"  [{color}]{r['pair']}[/] | D1={r['d1_bias']} H4={r['h4_bias']} M15={r['m15_signal']} | {status}")
        lines.append(f"    Resolution: {r['resolution']}")
        if r["fvgs"]:
            for f in r["fvgs"][:1]:
                lines.append(f"    FVG: {f['type']} [{f['gap_bottom']}-{f['gap_top']}] age={f['age_candles']}")
        if r["order_blocks"]:
            for ob in r["order_blocks"][:1]:
                lines.append(f"    OB: {ob['type']} [{ob['low']}-{ob['high']}] age={ob['age_candles']}")
        if r["liquidity"]:
            liq = r["liquidity"]
            lines.append(f"    Liquidity: BSL={liq.get('bsl_level')} SSL={liq.get('ssl_level')} Target={liq.get('target')}")
    return "\n".join(lines)
