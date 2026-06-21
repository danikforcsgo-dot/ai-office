const chartContainer = document.getElementById("chart");
const priceEl = document.getElementById("current-price");
const changeEl = document.getElementById("price-change");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const signalsList = document.getElementById("signals-list");
const confluenceArea = document.getElementById("confluence-area");
const buyCountEl = document.getElementById("buy-count");
const sellCountEl = document.getElementById("sell-count");
const tickerHighEl = document.getElementById("ticker-high");
const tickerLowEl = document.getElementById("ticker-low");
const tickerVolumeEl = document.getElementById("ticker-volume");
const orderbookAsks = document.getElementById("orderbook-asks");
const orderbookBids = document.getElementById("orderbook-bids");
const orderbookSpread = document.getElementById("orderbook-spread");

let allSignals = [];
let currentFilter = "all";
let currentInterval = "4h";

const chart = LightweightCharts.createChart(chartContainer, {
    layout: {
        background: { color: "#0d1117" },
        textColor: "#8b949e",
    },
    grid: {
        vertLines: { color: "#161b22" },
        horzLines: { color: "#161b22" },
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
    },
    timeScale: {
        borderColor: "#30363d",
        timeVisible: true,
        secondsVisible: false,
    },
    rightPriceScale: {
        borderColor: "#30363d",
    },
});

const candleSeries = chart.addCandlestickSeries({
    upColor: "#3fb950",
    downColor: "#f85149",
    borderDownColor: "#f85149",
    borderUpColor: "#3fb950",
    wickDownColor: "#f85149",
    wickUpColor: "#3fb950",
});

const volumeSeries = chart.addHistogramSeries({
    priceFormat: { type: "volume" },
    priceScaleId: "",
});

volumeSeries.priceScale().applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 },
});

function formatPrice(p) {
    return parseFloat(p).toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
    });
}

function formatVolume(v) {
    if (v >= 1e9) return (v / 1e9).toFixed(2) + "B";
    if (v >= 1e6) return (v / 1e6).toFixed(2) + "M";
    if (v >= 1e3) return (v / 1e3).toFixed(2) + "K";
    return v.toFixed(2);
}

function updatePriceDisplay(candle) {
    priceEl.textContent = formatPrice(candle.close);
    const openPrice = candle.open;
    const closePrice = candle.close;
    const pct = ((closePrice - openPrice) / openPrice) * 100;
    const sign = pct >= 0 ? "+" : "";
    changeEl.textContent = `${sign}${pct.toFixed(2)}%`;
    changeEl.className = pct >= 0 ? "price-up" : "price-down";
}

function handleCandle(candle) {
    candleSeries.update(candle);
    volumeSeries.update({
        time: candle.time,
        value: candle.volume,
        color: candle.close >= candle.open ? "rgba(63,185,80,0.3)" : "rgba(248,81,73,0.3)",
    });
    updatePriceDisplay(candle);
}

function handleTicker(ticker) {
    tickerHighEl.textContent = formatPrice(ticker.high);
    tickerLowEl.textContent = formatPrice(ticker.low);
    tickerVolumeEl.textContent = formatVolume(ticker.quoteVolume);
}

function handleDepth(depth) {
    const maxQty = Math.max(
        ...depth.asks.slice(0, 10).map(([, q]) => q),
        ...depth.bids.slice(0, 10).map(([, q]) => q)
    );

    orderbookAsks.innerHTML = depth.asks
        .slice(0, 10)
        .reverse()
        .map(([price, qty]) => {
            const pct = (qty / maxQty) * 100;
            return `<div class="orderbook-row ask">
                <div class="bg" style="width: ${pct}%"></div>
                <span>${formatPrice(price)}</span>
                <span>${qty.toFixed(4)}</span>
            </div>`;
        })
        .join("");

    orderbookBids.innerHTML = depth.bids
        .slice(0, 10)
        .map(([price, qty]) => {
            const pct = (qty / maxQty) * 100;
            return `<div class="orderbook-row bid">
                <div class="bg" style="width: ${pct}%"></div>
                <span>${formatPrice(price)}</span>
                <span>${qty.toFixed(4)}</span>
            </div>`;
        })
        .join("");

    if (depth.asks.length > 0 && depth.bids.length > 0) {
        const bestAsk = depth.asks[0][0];
        const bestBid = depth.bids[0][0];
        const spread = bestAsk - bestBid;
        const spreadPct = ((spread / bestAsk) * 100).toFixed(3);
        orderbookSpread.textContent = `Спред: ${formatPrice(spread)} (${spreadPct}%)`;
    }
}

function renderConfluence(confluence) {
    if (!confluence) {
        confluenceArea.innerHTML = '<div class="no-confluence">Нет согласованного сигнала (нужно 2+ скрипта)</div>';
        return;
    }

    const dirClass = confluence.direction.toLowerCase();
    const confPct = Math.round(confluence.confluence_score * 100);
    const categories = Object.entries(confluence.categories)
        .map(([cat, count]) => `<span>${cat}: ${count}</span>`)
        .join("");

    confluenceArea.innerHTML = `
        <div class="confluence-card ${dirClass}">
            <div class="confluence-header">
                <span class="confluence-label">Конфлюенция</span>
                <span class="confluence-direction ${dirClass}">${confluence.direction}</span>
            </div>
            <div class="confluence-score">
                <div class="confluence-bar">
                    <div class="confluence-fill ${dirClass}" style="width: ${confPct}%"></div>
                </div>
                <span class="confluence-pct ${dirClass}">${confPct}%</span>
            </div>
            <div class="confluence-scripts">
                <span class="buy-scripts">${confluence.buy_count} BUY</span>
                <span class="sell-scripts">${confluence.sell_count} SELL</span>
                <span>из ${confluence.total_loaded}</span>
            </div>
            <div class="confluence-categories">${categories}</div>
        </div>
    `;
}

function renderSignals(signals) {
    allSignals = signals;
    const buyCount = signals.filter((s) => s.direction === "BUY").length;
    const sellCount = signals.filter((s) => s.direction === "SELL").length;
    buyCountEl.textContent = `${buyCount} BUY`;
    sellCountEl.textContent = `${sellCount} SELL`;

    const filtered = currentFilter === "all" ? signals : signals.filter((s) => s.direction === currentFilter);

    if (filtered.length === 0) {
        signalsList.innerHTML = '<div class="no-signals">Нет активных сигналов</div>';
        return;
    }

    signalsList.innerHTML = filtered
        .map((s) => {
            const dirClass = s.direction.toLowerCase();
            const confPct = Math.round(s.confidence * 100);
            const rules = s.rules_matched.slice(0, 2).map((r) => `<span>${r.substring(0, 40)}${r.length > 40 ? "..." : ""}</span>`).join("");
            return `
                <div class="signal-card ${dirClass}" onclick="window.open('${s.url}', '_blank')">
                    <div class="signal-top">
                        <span class="signal-direction ${dirClass}">${s.direction}</span>
                        <span class="signal-source">${s.author}</span>
                    </div>
                    <div class="signal-name">${s.script_name}</div>
                    <div class="signal-confidence">
                        <div class="confidence-bar">
                            <div class="confidence-fill ${dirClass}" style="width: ${confPct}%"></div>
                        </div>
                        <span class="confidence-text">${confPct}%</span>
                    </div>
                    <div class="signal-rules">${rules}</div>
                </div>
            `;
        })
        .join("");
}

document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentFilter = btn.dataset.filter;
        renderSignals(allSignals);
    });
});

document.querySelectorAll(".interval-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".interval-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentInterval = btn.dataset.interval;
        const url = new URL(window.location);
        url.searchParams.set("interval", currentInterval);
        window.location.href = url.toString();
    });
});

const urlParams = new URLSearchParams(window.location.search);
const savedInterval = urlParams.get("interval");
if (savedInterval) {
    currentInterval = savedInterval;
    document.querySelectorAll(".interval-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.interval === savedInterval);
    });
}

function connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws?interval=${currentInterval}`);

    ws.onopen = () => {
        statusDot.className = "dot connected";
        statusText.textContent = "Подключено";
    };

    ws.onclose = () => {
        statusDot.className = "dot disconnected";
        statusText.textContent = "Отключение... Переподключение";
        setTimeout(connect, 3000);
    };

    ws.onerror = () => {
        ws.close();
    };

    ws.onmessage = (evt) => {
        const msg = JSON.parse(evt.data);
        if (msg.type === "history") {
            candleSeries.setData(msg.data);
            volumeSeries.setData(
                msg.data.map((c) => ({
                    time: c.time,
                    value: c.volume,
                    color: c.close >= c.open ? "rgba(63,185,80,0.3)" : "rgba(248,81,73,0.3)",
                }))
            );
            if (msg.data.length > 0) {
                updatePriceDisplay(msg.data[msg.data.length - 1]);
            }
        } else if (msg.type === "kline") {
            handleCandle(msg.data);
        } else if (msg.type === "signals") {
            renderConfluence(msg.data.confluence);
            renderSignals(msg.data.individual);
        } else if (msg.type === "ticker") {
            handleTicker(msg.data);
        } else if (msg.type === "depth") {
            handleDepth(msg.data);
        }
    };
}

chart.timeScale().fitContent();
connect();

window.addEventListener("resize", () => {
    chart.applyOptions({
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight,
    });
});
