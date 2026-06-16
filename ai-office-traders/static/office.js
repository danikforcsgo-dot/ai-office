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
let currentDebateIdx = 0;
let debateTimer = null;

const COLORS = {
    bg: '#0a0a1a',
    room: '#12122a',
    roomBorder: '#2a2a5a',
    roomText: '#6a6aaa',
    desk: '#1a1a40',
    floor: '#0d0d22',
    buy: '#00e676',
    sell: '#ff5252',
    neutral: '#ffab00',
    noData: '#444',
    text: '#ffffff',
    textDim: '#666',
};

const DEPT_LAYOUT = {
    'Технологии':          { x: 30,  y: 30,  w: 160, h: 100 },
    'Операционный отдел':  { x: 210, y: 30,  w: 160, h: 100 },
    'Исследования и стратегия': { x: 390, y: 30, w: 160, h: 100 },
    'Технический анализ':  { x: 30,  y: 150, w: 160, h: 100 },
    'ICT / Smart Money':   { x: 210, y: 150, w: 160, h: 100 },
    'M15 Краткосрочный анализ': { x: 390, y: 150, w: 160, h: 100 },
    'Макроэкономика':      { x: 30,  y: 270, w: 160, h: 100 },
    'Квантовый анализ':    { x: 210, y: 270, w: 160, h: 100 },
    'Управление рисками':  { x: 390, y: 270, w: 160, h: 100 },
    'Межрыночный анализ':  { x: 30,  y: 390, w: 160, h: 100 },
    'Сентимент и Новостной анализ': { x: 210, y: 390, w: 160, h: 100 },
    'Прогнозирование':     { x: 390, y: 390, w: 160, h: 100 },
    'Алгоритмическая торговля': { x: 30, y: 510, w: 160, h: 80 },
    'Управление портфелем': { x: 210, y: 510, w: 160, h: 80 },
    'Тестирование стратегий': { x: 390, y: 510, w: 160, h: 80 },
    'Поведенческие финансы': { x: 30, y: 610, w: 160, h: 70 },
    'Волатильность':       { x: 210, y: 610, w: 160, h: 70 },
    'Фундаментальный анализ': { x: 390, y: 610, w: 160, h: 70 },
};

const ALL_STAFF = [
    { id: 1, name: 'Артём В.', dept: 'Технический анализ', head: true },
    { id: 2, name: 'Дмитрий О.', dept: 'Технический анализ' },
    { id: 3, name: 'Елена С.', dept: 'Технический анализ' },
    { id: 16, name: 'Роман Е.', dept: 'Технический анализ' },
    { id: 27, name: 'Матвей Ж.', dept: 'ICT / Smart Money', head: true },
    { id: 28, name: 'Степан К.', dept: 'ICT / Smart Money' },
    { id: 33, name: 'Пётр З.', dept: 'ICT / Smart Money' },
    { id: 65, name: 'Анастасия М.', dept: 'ICT / Smart Money' },
    { id: 32, name: 'Кирилл П.', dept: 'M15 Краткосрочный анализ', head: true },
    { id: 29, name: 'Олег Б.', dept: 'M15 Краткосрочный анализ' },
    { id: 30, name: 'Анна Г.', dept: 'Макроэкономика', head: true },
    { id: 4, name: 'Андрей К.', dept: 'Макроэкономика' },
    { id: 5, name: 'Мария П.', dept: 'Макроэкономика' },
    { id: 53, name: 'Даниил М.', dept: 'Макроэкономика' },
    { id: 64, name: 'Максим К.', dept: 'Макроэкономика' },
    { id: 8, name: 'Павел С.', dept: 'Квантовый анализ', head: true },
    { id: 9, name: 'Ирина М.', dept: 'Квантовый анализ' },
    { id: 67, name: 'Роман С.', dept: 'Квантовый анализ' },
    { id: 10, name: 'Никита Л.', dept: 'Управление рисками', head: true },
    { id: 11, name: 'Татьяна П.', dept: 'Управление рисками' },
    { id: 76, name: 'Елена К.', dept: 'Управление рисками' },
    { id: 14, name: 'Алексей М.', dept: 'Межрыночный анализ', head: true },
    { id: 12, name: 'Виктор С.', dept: 'Межрыночный анализ' },
    { id: 15, name: 'Юлия В.', dept: 'Межрыночный анализ' },
    { id: 54, name: 'Анна Б.', dept: 'Межрыночный анализ' },
    { id: 71, name: 'Арсений П.', dept: 'Межрыночный анализ' },
    { id: 19, name: 'Екатерина Н.', dept: 'Исследования и стратегия', head: true },
    { id: 24, name: 'Анна Г.', dept: 'Исследования и стратегия' },
    { id: 13, name: 'Наталья Ф.', dept: 'Исследования и стратегия' },
    { id: 74, name: 'София Н.', dept: 'Исследования и стратегия' },
    { id: 75, name: 'Владимир О.', dept: 'Исследования и стратегия' },
    { id: 18, name: 'Максим З.', dept: 'Операционный отдел', head: true },
    { id: 17, name: 'Ксения Б.', dept: 'Операционный отдел' },
    { id: 25, name: 'Игорь М.', dept: 'Операционный отдел' },
    { id: 31, name: 'Денис Я.', dept: 'Операционный отдел' },
    { id: 73, name: 'Иван К.', dept: 'Операционный отдел' },
    { id: 20, name: 'Денис К.', dept: 'Технологии', head: true },
    { id: 26, name: 'Тимур А.', dept: 'Технологии' },
    { id: 55, name: 'Евгений С.', dept: 'Технологии' },
    { id: 68, name: 'Ксения Л.', dept: 'Технологии' },
    { id: 50, name: 'Артём В.', dept: 'Сентимент и Новостной анализ', head: true },
    { id: 51, name: 'Виктория С.', dept: 'Сентимент и Новостной анализ' },
    { id: 72, name: 'Мария В.', dept: 'Сентимент и Новостной анализ' },
    { id: 56, name: 'Полина О.', dept: 'Прогнозирование', head: true },
    { id: 57, name: 'Илья Р.', dept: 'Алгоритмическая торговля', head: true },
    { id: 69, name: 'Дмитрий С.', dept: 'Алгоритмическая торговля' },
    { id: 58, name: 'Сергей В.', dept: 'Управление портфелем', head: true },
    { id: 59, name: 'Ольга М.', dept: 'Управление портфелем' },
    { id: 60, name: 'Никита В.', dept: 'Тестирование стратегий', head: true },
    { id: 61, name: 'Дарья К.', dept: 'Тестирование стратегий' },
    { id: 62, name: 'Александр П.', dept: 'Поведенческие финансы', head: true },
    { id: 63, name: 'Константин Ф.', dept: 'Волатильность', head: true },
    { id: 70, name: 'Екатерина Р.', dept: 'Фундаментальный анализ', head: true },
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
        const cols = Math.ceil(Math.sqrt(deptMembers.length));
        const cellW = (layout.w - 20) / cols;
        const cellH = 28;
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        return {
            ...staff,
            x: layout.x + 10 + col * cellW + cellW / 2,
            y: layout.y + 30 + row * cellH + 10,
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
        ctx.lineWidth = 1;
        roundRect(ctx, layout.x, layout.y, layout.w, layout.h, 8);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = COLORS.roomText;
        ctx.font = 'bold 11px Segoe UI';
        ctx.fillText(name, layout.x + 8, layout.y + 16);
    }

    for (const a of analysts) {
        const report = reports.find(r => r.id === a.id);
        const color = getSignalColor(report);

        ctx.beginPath();
        ctx.arc(a.x, a.y, a.radius + 2, 0, Math.PI * 2);
        ctx.fillStyle = color + '33';
        ctx.fill();

        ctx.beginPath();
        ctx.arc(a.x, a.y, a.radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        if (a.head) {
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        ctx.fillStyle = COLORS.text;
        ctx.font = '9px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText(a.name, a.x, a.y + a.radius + 12);
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
    document.getElementById('modal-name').textContent = analyst.name + (analyst.head ? ' ★' : '');
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
            <div class="modal-dept">Отдел: ${analyst.dept} | Сигналов: ${(report.signals || []).length}</div>
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
        return `<div class="price-item"><span class="price-name">${p.name}</span><span class="price-value ${cls}">${p.price.toFixed(5)}</span></div>`;
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
    const x = analyst.x + rect.left;
    const y = analyst.y + rect.top - 60;
    speechBubble.style.left = Math.min(x, window.innerWidth - 340) + 'px';
    speechBubble.style.top = Math.max(y, 10) + 'px';
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
        if (idx >= debateMsgs.length) {
            hideSpeechBubble();
            return;
        }
        const msg = debateMsgs[idx];
        const analyst = analysts.find(a => a.name.includes(msg.speaker.split(' ')[0]) || msg.speaker.includes(a.name));
        if (analyst) {
            showSpeechBubble(analyst, msg.text);
            addEvent('debate', `<strong>${msg.speaker}</strong>: ${msg.text.slice(0, 120)}...`);
        }
        idx++;
        debateTimer = setTimeout(showNext, 5000);
    }
    showNext();
}

async function runCycle() {
    document.getElementById('status-text').textContent = 'Анализ...';

    try {
        const resp = await fetch('/api/cycle');
        const data = await resp.json();

        if (data.error) {
            addEvent('system', `Ошибка: ${data.error}`);
            document.getElementById('status-text').textContent = 'Ошибка';
            return;
        }

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
            const v = data.global_report.global_verdict || 'NEUTRAL';
            addEvent('signal', `Глобальный вердикт: <strong>${v}</strong>`);
        }

        playDebate(debateMessages);
        document.getElementById('status-text').textContent = 'Готово';

    } catch (e) {
        addEvent('system', `Ошибка сети: ${e.message}`);
        document.getElementById('status-text').textContent = 'Ошибка';
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

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

window.addEventListener('resize', resize);
positionAnalysts();
resize();
addEvent('system', 'Офис загружен. Нажмите "Запустить цикл" для начала анализа.');
