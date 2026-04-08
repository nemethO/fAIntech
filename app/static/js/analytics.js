// analitika oldal - tabkezelés és chartok
Chart.defaults.color = '#9ca3af';
Chart.defaults.borderColor = '#1e2a3a';

let charts = {};

// tab kapcsolas
function switchTab(tab) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('bg-primary', 'text-white');
        b.classList.add('bg-dark-card', 'text-gray-400');
    });
    document.getElementById('panel-' + tab).classList.remove('hidden');
    const btn = document.getElementById('tab-' + tab);
    btn.classList.add('bg-primary', 'text-white');
    btn.classList.remove('bg-dark-card', 'text-gray-400');

    // betoltes ha kell
    if (tab === 'overview') loadOverview();
    if (tab === 'categories') loadCategories();
    if (tab === 'trends') loadTrends();
    if (tab === 'merchants') loadMerchants();
}

// szam formatalas
function fmt(n) {
    return Math.round(n).toLocaleString('hu-HU') + ' Ft';
}

// ==================== ATTEKINTES ====================
let overviewLoaded = false;
async function loadOverview() {
    if (overviewLoaded) return;
    try {
        const resp = await fetch('/analytics/api/overview');
        const data = await resp.json();
        overviewLoaded = true;

        const s = data.summary;
        document.getElementById('ov-prev-label').textContent = data.months.previous.charAt(0).toUpperCase() + data.months.previous.slice(1) + ' megtakarítás';
        document.getElementById('ov-curr-label').textContent = data.months.current.charAt(0).toUpperCase() + data.months.current.slice(1) + ' megtakarítás';
        document.getElementById('ov-prev-savings').textContent = fmt(s.prev_savings);
        document.getElementById('ov-curr-savings').textContent = fmt(s.curr_savings);
        document.getElementById('ov-prev-rate').textContent = s.prev_rate + '% ráta';
        document.getElementById('ov-curr-rate').textContent = s.curr_rate + '% ráta';
        document.getElementById('ov-avg-daily').textContent = fmt(s.avg_daily);
        document.getElementById('ov-top-cat').textContent = s.top_cat;
        document.getElementById('ov-top-amount').textContent = fmt(s.top_cat_amount);
        document.getElementById('ov-comp-title').textContent =
            data.months.previous.charAt(0).toUpperCase() + data.months.previous.slice(1) +
            ' vs. ' + data.months.current + ' kiadások';

        // bar chart: kategoriak osszehasonlitasa
        const comp = data.comparison.filter(c => c.current > 0 || c.previous > 0);
        if (charts.overviewBar) charts.overviewBar.destroy();
        const barCtx = document.getElementById('overviewBarChart');
        if (barCtx) {
            charts.overviewBar = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: comp.map(c => c.name),
                    datasets: [
                        { label: data.months.previous, data: comp.map(c => c.previous), backgroundColor: '#3b82f6', borderRadius: 4 },
                        { label: data.months.current, data: comp.map(c => c.current), backgroundColor: '#60a5fa', borderRadius: 4 },
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + fmt(ctx.parsed.y) } }
                    },
                    scales: {
                        y: { ticks: { callback: v => (v/1000) + 'e' }, grid: { color: '#111827' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        // trend vonal
        if (charts.overviewTrend) charts.overviewTrend.destroy();
        const trendCtx = document.getElementById('overviewTrendChart');
        if (trendCtx) {
            charts.overviewTrend = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: data.trend.map(t => t.label),
                    datasets: [
                        { label: 'Bevétel', data: data.trend.map(t => t.income), borderColor: '#4ade80', backgroundColor: 'rgba(74,222,128,0.05)', fill: true, tension: 0.3, pointRadius: 5, pointBackgroundColor: '#4ade80' },
                        { label: 'Kiadás', data: data.trend.map(t => t.expense), borderColor: '#f87171', backgroundColor: 'rgba(248,113,113,0.05)', fill: true, tension: 0.3, pointRadius: 5, pointBackgroundColor: '#f87171' },
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + fmt(ctx.parsed.y) } }
                    },
                    scales: {
                        y: { ticks: { callback: v => (v/1000) + 'e' }, grid: { color: '#111827' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    } catch (e) {
        console.warn('Áttekintés hiba:', e);
    }
}

// ==================== KATEGORIAK ====================
let categoriesLoaded = false;
async function loadCategories() {
    if (categoriesLoaded) return;
    try {
        const resp = await fetch('/analytics/api/categories');
        const data = await resp.json();
        categoriesLoaded = true;

        const cats = data.categories;
        document.getElementById('cat-radar-sub').textContent =
            data.months.current.charAt(0).toUpperCase() + data.months.current.slice(1) + ' – relatív kiadás arányok';
        document.getElementById('cat-detail-title').textContent =
            data.months.current.charAt(0).toUpperCase() + data.months.current.slice(1) + ' – részletes bontás';
        document.getElementById('cat-change-title').textContent =
            'Változás ' + data.months.previous + ' → ' + data.months.current;

        // radar chart
        const radarCats = cats.filter(c => c.current > 0);
        if (charts.catRadar) charts.catRadar.destroy();
        const radarCtx = document.getElementById('catRadarChart');
        if (radarCtx && radarCats.length > 0) {
            const maxVal = Math.max(...radarCats.map(c => c.current));
            charts.catRadar = new Chart(radarCtx, {
                type: 'radar',
                data: {
                    labels: radarCats.map(c => c.name),
                    datasets: [{
                        data: radarCats.map(c => c.current),
                        backgroundColor: 'rgba(37, 99, 235, 0.2)',
                        borderColor: '#2563eb',
                        pointBackgroundColor: '#60a5fa',
                        pointRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmt(ctx.parsed.r) } } },
                    scales: {
                        r: { grid: { color: '#1e2a3a' }, angleLines: { color: '#1e2a3a' },
                             ticks: { display: false }, suggestedMax: maxVal * 1.1 }
                    }
                }
            });
        }

        // reszletes lista
        const detailEl = document.getElementById('catDetailList');
        const totalSpent = cats.reduce((s, c) => s + c.current, 0);
        detailEl.innerHTML = cats.filter(c => c.current > 0).map(c => {
            const pct = totalSpent > 0 ? (c.current / totalSpent * 100) : 0;
            return `<div class="flex items-center gap-3">
                <span class="text-lg">${c.icon}</span>
                <span class="text-sm flex-1">${c.name}</span>
                <div class="w-32 bg-dark-bg rounded-full h-2 overflow-hidden">
                    <div class="h-full rounded-full" style="width:${pct}%; background:${c.color}"></div>
                </div>
                <span class="text-sm font-semibold w-24 text-right">${fmt(c.current)}</span>
            </div>`;
        }).join('');

        // valtozas kartya
        const changeEl = document.getElementById('catChangeGrid');
        changeEl.innerHTML = cats.filter(c => c.current > 0 || c.previous > 0).map(c => {
            const isUp = c.change_pct > 0;
            const color = isUp ? 'text-red-400' : 'text-green-400';
            return `<div class="flex items-center justify-between bg-dark-bg rounded-lg px-4 py-3">
                <div class="flex items-center gap-2">
                    <span>${c.icon}</span>
                    <span class="text-sm">${c.name}</span>
                </div>
                <span class="text-sm font-semibold ${color}">${isUp ? '+' : ''}${c.change_pct}%</span>
            </div>`;
        }).join('');
    } catch (e) {
        console.warn('Kategóriák hiba:', e);
    }
}

// ==================== TRENDEK ====================
let trendsLoaded = false;
async function loadTrends() {
    if (trendsLoaded) return;
    try {
        const resp = await fetch('/analytics/api/trends');
        const data = await resp.json();
        trendsLoaded = true;
        const months = data.months;

        // koltes tempo
        const p = data.pace;
        document.getElementById('tr-pace-current').textContent = fmt(p.current);
        document.getElementById('tr-pace-projected').textContent = fmt(p.projected);
        document.getElementById('tr-pace-day').textContent = p.day_of_month;

        const bar = document.getElementById('tr-pace-bar');
        const pct = Math.min(p.pace_pct, 150);
        bar.style.width = Math.min(pct, 100) + '%';
        bar.className = 'h-full rounded-full transition-all duration-500 ' +
            (p.pace_pct > 110 ? 'bg-red-500' : p.pace_pct > 90 ? 'bg-yellow-500' : 'bg-green-500');

        const vsEl = document.getElementById('tr-pace-vs');
        if (p.prev_total > 0) {
            const diff = p.pace_pct - 100;
            vsEl.textContent = (diff > 0 ? '+' : '') + diff + '% vs előző hónap';
            vsEl.className = 'text-xs mt-1 ' + (diff > 5 ? 'text-red-400' : diff < -5 ? 'text-green-400' : 'text-gray-400');
        } else {
            vsEl.textContent = 'Nincs előző havi adat';
            vsEl.className = 'text-xs mt-1 text-gray-500';
        }

        // megtakaritasi rata chart
        if (charts.trSavings) charts.trSavings.destroy();
        const savCtx = document.getElementById('trSavingsChart');
        if (savCtx) {
            charts.trSavings = new Chart(savCtx, {
                type: 'bar',
                data: {
                    labels: months.map(m => m.label),
                    datasets: [{
                        data: months.map(m => m.savings_rate),
                        backgroundColor: months.map(m => m.savings_rate >= 0 ? '#4ade80' : '#f87171'),
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.parsed.y + '%' } } },
                    scales: {
                        y: { ticks: { callback: v => v + '%' }, grid: { color: '#111827' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        // napi atlag chart
        if (charts.trAvgDaily) charts.trAvgDaily.destroy();
        const avgCtx = document.getElementById('trAvgDailyChart');
        if (avgCtx) {
            charts.trAvgDaily = new Chart(avgCtx, {
                type: 'bar',
                data: {
                    labels: months.map(m => m.label),
                    datasets: [{
                        data: months.map(m => m.avg_daily),
                        backgroundColor: '#60a5fa',
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmt(ctx.parsed.y) + '/nap' } } },
                    scales: {
                        y: { ticks: { callback: v => (v/1000) + 'e' }, grid: { color: '#111827' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        // tranzakcioszam chart
        if (charts.trTxCount) charts.trTxCount.destroy();
        const txCtx = document.getElementById('trTxCountChart');
        if (txCtx) {
            charts.trTxCount = new Chart(txCtx, {
                type: 'bar',
                data: {
                    labels: months.map(m => m.label),
                    datasets: [{
                        data: months.map(m => m.tx_count),
                        backgroundColor: '#facc15',
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.parsed.y + ' db' } } },
                    scales: {
                        y: { ticks: { stepSize: 1 }, grid: { color: '#111827' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        // kategoria eltolodasok
        const shiftsEl = document.getElementById('trCatShifts');
        const shifts = data.cat_shifts;
        if (shifts.length === 0) {
            shiftsEl.innerHTML = '<p class="text-gray-500 text-sm col-span-3">Nincs elég adat az összehasonlításhoz.</p>';
        } else {
            shiftsEl.innerHTML = shifts.map(s => {
                const up = s.change_pct > 0;
                const icon = up ? '↑' : s.change_pct < 0 ? '↓' : '→';
                const color = up ? 'text-red-400' : s.change_pct < 0 ? 'text-green-400' : 'text-gray-400';
                return `<div class="bg-dark-bg rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-lg">${s.icon}</span>
                        <span class="text-sm font-bold ${color}">${icon} ${Math.abs(s.change_pct)}%</span>
                    </div>
                    <p class="text-sm font-medium">${s.name}</p>
                    <div class="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Előző: ${fmt(s.previous)}</span>
                        <span>Most: ${fmt(s.current)}</span>
                    </div>
                </div>`;
            }).join('');
        }
    } catch (e) {
        console.warn('Trendek hiba:', e);
    }
}

// ==================== KERESKEDOK ====================
let merchantsLoaded = false;
async function loadMerchants() {
    if (merchantsLoaded) return;
    try {
        const resp = await fetch('/analytics/api/merchants');
        const data = await resp.json();
        merchantsLoaded = true;

        const el = document.getElementById('merchantsList');
        if (data.length === 0) {
            el.innerHTML = '<p class="text-gray-500 text-center py-8">Nincs tranzakció ebben a hónapban.</p>';
            return;
        }

        const maxAmount = data[0].amount;
        el.innerHTML = data.map((m, i) => {
            const pct = (m.amount / maxAmount * 100);
            return `<div class="flex items-center gap-4 py-2">
                <span class="text-gray-500 text-sm w-6 text-right">${i + 1}.</span>
                <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-baseline mb-1">
                        <span class="text-sm font-medium truncate">${m.name}</span>
                        <span class="text-sm text-gray-400 ml-2">${m.count}x</span>
                    </div>
                    <div class="w-full bg-dark-bg rounded-full h-1.5 overflow-hidden">
                        <div class="h-full rounded-full bg-primary" style="width: ${pct}%"></div>
                    </div>
                </div>
                <span class="text-sm font-semibold w-28 text-right">${fmt(m.amount)}</span>
            </div>`;
        }).join('');
    } catch (e) {
        console.warn('Kereskedők hiba:', e);
    }
}

// elso tab betoltese
document.addEventListener('DOMContentLoaded', () => loadOverview());
