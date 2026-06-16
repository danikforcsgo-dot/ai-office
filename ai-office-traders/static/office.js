const canvas = document.getElementById('office-canvas');
const ctx = canvas.getContext('2d');
const eventFeed = document.getElementById('event-feed');
const speechBubble = document.getElementById('speech-bubble');

let W, H;
let analysts = [];
let reports = [];
let prices = [];
let debateMessages = [];
let traderStats = {};
let autoMode = false;
let autoInterval = null;
let debateTimer = null;

const COLORS = {
    bg: '#0a0a1a',
    room: '#12122a',
    roomBorder: '#ffd700',
    roomText: '#ffd700',
    floor: '#0d0d22',
    buy: '#00ff88',
    sell: '#ff0066',
    neutral: '#ffaa00',
    noData: '#444',
    text: '#ffffff',
    textDim: '#666',
};

const DEPT_LAYOUT = {
    'Trading': { x: 30, y: 30, w: 560, h: 500 },
};

const ALL_STAFF = [
    { id: 1, name: 'CTO ★', dept: 'Trading', head: true },
    { id: 2, name: 'Sr. Analyst', dept: 'Trading' },
    { id: 3, name: 'M15 Trader', dept: 'Trading' },
    { id: 4, name: 'Risk Manager', dept: 'Trading' },
    { id: 5, name: 'FVG Specialist', dept: 'Trading' },
    { id: 6, name: 'Kill Zone', dept: 'Trading' },
    { id: 7, name: 'News Filter', dept: 'Trading' },
    { id: 8, name: 'ATR Analyst', dept: 'Trading' },
    { id: 9, name: 'Journal', dept: 'Trading' },
    { id: 10, name: 'Backtester', dept: 'Trading' },
    { id: 11, name: 'Data Eng.', dept: 'Trading' },
    { id: 12, name: 'Psychology', dept: 'Trading' },
    { id: 13, name: 'Data Quality', dept: 'Trading' },
    { id: 14, name: 'Alert Monitor', dept: 'Trading' },
];

function resize() {
    const area = document.getElementById('office-area');
    W = area.clientWidth;
    H = area.clientHeight;
    canvas.width = W;
    canvas.height = H;
    draw();
}

function getSignalColor(report) {
    if (!report) return COLORS.noData;
    const s = report.summary || '';
    if (s.includes('BULLISH')) return COLORS.buy;
    if (s.includes('BEARISH')) return COLORS.sell;
    return COLORS.neutral;
}

function positionAnalysts() {
    analysts = ALL_STAFF.map(staff => {
        const layout = DEPT_LAYOUT[staff.dept];
        if (!layout) return null;
        const deptMembers = ALL_STAFF.filter(s => s.dept === staff.dept);
        const idx = deptMembers.indexOf(staff);
        const cols = 4;
        const cellW = (layout.w - 20) / cols;
        const cellH = 35;
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        return {
            ...staff,
            x: layout.x + 10 + col * cellW + cellW / 2,
            y: layout.y + 40 + row * cellH + 10,
            radius: staff.head ? 14 : 10,
        };
    }).filter(Boolean);
}

function draw() {
    ctx.fillStyle = COLORS.floor;
    ctx.fillRect(0, 0, W, H);

    for (const [name, layout] of Object.entries(DEPT_LAYOUT)) {
        ctx.fillStyle = COLORS.room;
        ctx.strokeStyle = COLORS.roomBorder;
        ctx.lineWidth = 2;
        roundRect(ctx, layout.x, layout.y, layout.w, layout.h, 12);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = COLORS.roomText;
        ctx.font = 'bold 14px Segoe UI';
        ctx.fillText(name, layout.x + 15, layout.y + 25);
    }

    for (const a of analysts) {
        const report = reports.find(r => r.id === a.id);
        const color = getSignalColor(report);

        ctx.beginPath();
        ctx.arc(a.x, a.y, a.radius + 3, 0, Math.PI * 2);
        ctx.fillStyle = color + '33';
        ctx.fill();

        ctx.beginPath();
        ctx.arc(a.x, a.y, a.radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        if (a.head) {
            ctx.strokeStyle = '#ffd700';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        ctx.fillStyle = COLORS.text;
        ctx.font = '10px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText(a.name, a.x, a.y + a.radius + 14);
        ctx.textAlign = 'left';
    }
}

function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
}

canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    for (const a of analysts) {
        const dx = mx - a.x;
        const dy = my - a.y;
        if (dx * dx + dy * dy < (a.radius + 5) * (a.radius + 5)) {
            showAnalystModal(a);
            return;
        }
    }
    closeModal();
});

function showAnalystModal(analyst) {
    const report = reports.find(r => r.id === analyst.id);
    document.getElementById('modal-name').textContent = analyst.name;
    document.getElementById('modal-role').textContent = analyst.dept;

    const body = document.getElementById('modal-body');
    if (!report) {
        body.innerHTML = '<div class="modal-section"><div class="modal-section-title">Нет данных</div></div>';
    } else {
        const signal = (report.summary || '').includes('BULLISH') ? 'BUY' :
                       (report.summary || '').includes('BEARISH') ? 'SELL' : 'NEUTRAL';
        const sigClass = signal === 'BUY' ? 'buy' : signal === 'SELL' ? 'sell' : 'neutral';

        let findingsHtml = '';
        for (const f of (report.findings || [])) {
            const parts = [];
            for (const [k, v] of Object.entries(f)) {
                if (k === 'signal') continue;
                const val = Array.isArray(v) ? v.join(', ') : typeof v === 'object' ? JSON.stringify(v).slice(0, 60) : v;
                if (val && val !== 'NEUTRAL' && val !== 'None') {
                    parts.push(`<strong>${k}:</strong> ${val}`);
                }
            }
            if (parts.length) {
                findingsHtml += `<div class="modal-finding">${parts.join(' | ')}</div>`;
            }
        }

        body.innerHTML = `
            <div class="modal-section">
                <span class="modal-signal ${sigClass}">${signal}</span>
            </div>
            <div class="modal-section">
                <div class="modal-section-title">Находки</div>
                <div class="modal-findings">${findingsHtml || 'Нет данных'}</div>
            </div>
        `;
    }

    document.getElementById('analyst-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('analyst-modal').classList.remove('active');
}

function addEvent(type, text) {
    const time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const item = document.createElement('div');
    item.className = `event-item ${type}`;
    item.innerHTML = `<div class="event-time">${time}</div><div class="event-text">${text}</div>`;
    eventFeed.insertBefore(item, eventFeed.firstChild);
    if (eventFeed.children.length > 50) {
        eventFeed.removeChild(eventFeed.lastChild);
    }
}

function updatePricesBar() {
    const bar = document.getElementById('prices-bar');
    bar.innerHTML = prices.map(p => {
        const chg = p.price - p.open;
        const cls = chg >= 0 ? 'price-up' : 'price-down';
        return `<div class="price-item"><span class="price-name">${p.name}</span><span class="price-value ${cls}">${p.price.toFixed(2)}</span></div>`;
    }).join('');
}

function updateStats() {
    if (!traderStats.balance) return;
    const pnlColor = traderStats.total_pnl >= 0 ? 'green' : 'red';
    document.getElementById('stat-balance').textContent = `$${traderStats.balance.toFixed(0)}`;
    document.getElementById('stat-pnl').textContent = `$${(traderStats.total_pnl || 0).toFixed(2)}`;
    document.getElementById('stat-pnl').className = `stat-value ${pnlColor}`;
    document.getElementById('stat-positions').textContent = `${traderStats.open_positions || 0}/3`;
    document.getElementById('stat-winrate').textContent = `${traderStats.win_rate || 0}%`;
}

function showSpeechBubble(analyst, text) {
    speechBubble.style.display = 'block';
    speechBubble.querySelector('.speaker').textContent = analyst.name;
    speechBubble.querySelector('.text').textContent = text.slice(0, 200);
    const rect = canvas.getBoundingClientRect();
    speechBubble.style.left = Math.min(analyst.x + rect.left, window.innerWidth - 340) + 'px';
    speechBubble.style.top = Math.max(analyst.y + rect.top - 60, 10) + 'px';
}

function hideSpeechBubble() {
    speechBubble.style.display = 'none';
}

function playDebate(messages) {
    const debateMsgs = messages.filter(m => m.type === 'opening' || m.type === 'counter' || m.type === 'judge');
    if (!debateMsgs.length) return;
    let idx = 0;
    clearInterval(debateTimer);
    function showNext() {
        if (idx >= debateMsgs.length) { hideSpeechBubble(); return; }
        const msg = debateMsgs[idx];
        const analyst = analysts.find(a => a.name.includes(msg.speaker.split(' ')[0]) || msg.speaker.includes(a.name));
        if (analyst) {
            showSpeechBubble(analyst, msg.text);
            addEvent('debate', `<strong>${msg.speaker}</strong>: ${msg.text.slice(0, 100)}...`);
        }
        idx++;
        debateTimer = setTimeout(showNext, 5000);
    }
    showNext();
}

async function runCycle() {
    const btn = document.getElementById('runBtn');
    btn.disabled = true;
    btn.textContent = 'SCANNING...';
    document.getElementById('statusDot').className = 'status-dot blue';
    document.getElementById('statusAuto').textContent = 'Scanning...';
    try {
        const resp = await fetch('/api/cycle');
        const data = await resp.json();
        if (data.error) { addEvent('system', `Ошибка: ${data.error}`); return; }
        reports = data.analyst_reports || [];
        prices = data.prices || [];
        debateMessages = data.debate || [];
        traderStats = data.trader_stats || {};
        positionAnalysts();
        draw();
        updatePricesBar();
        updateStats();
        addEvent('system', `Цикл завершён. Аналитиков: ${reports.length}`);
        for (const msg of debateMessages.slice(0, 3)) {
            addEvent('debate', `<strong>${msg.speaker}</strong>: ${msg.text.slice(0, 100)}...`);
        }
        if (data.global_report) {
            addEvent('signal', `Глобальный вердикт: <strong>${data.global_report.global_verdict}</strong>`);
        }
        playDebate(debateMessages);
        document.getElementById('status-text').textContent = 'Готово';
    } catch (e) {
        addEvent('system', `Ошибка сети: ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.textContent = 'ANALYZE';
    }
}

function toggleAuto() {
    autoMode = !autoMode;
    const btn = document.querySelectorAll('.toolbar-btn')[1];
    if (autoMode) {
        btn.classList.add('active');
        btn.textContent = 'Стоп';
        autoInterval = setInterval(runCycle, 15 * 60 * 1000);
        runCycle();
    } else {
        btn.classList.remove('active');
        btn.textContent = 'Авто';
        clearInterval(autoInterval);
    }
}

document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
window.addEventListener('resize', resize);
positionAnalysts();
resize();
addEvent('system', 'Офис загружен. Нажмите "Запустить цикл" для начала анализа.');
