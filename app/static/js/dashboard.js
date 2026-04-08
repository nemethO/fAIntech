// dashboard chartok - Chart.js
document.addEventListener('DOMContentLoaded', async () => {
    // kozos chart beallitasok
    Chart.defaults.color = '#9ca3af';
    Chart.defaults.borderColor = '#1e2a3a';
    Chart.defaults.font.family = 'system-ui, sans-serif';

    // 1) bevetel vs kiadas vonaldiagram
    try {
        const resp = await fetch('/api/dashboard/chart');
        const data = await resp.json();

        const ctx = document.getElementById('incomeExpenseChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => d.label),
                    datasets: [
                        {
                            label: 'Bevétel',
                            data: data.map(d => d.income),
                            borderColor: '#4ade80',
                            backgroundColor: 'rgba(74, 222, 128, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4,
                            pointBackgroundColor: '#4ade80',
                        },
                        {
                            label: 'Kiadás',
                            data: data.map(d => d.expense),
                            borderColor: '#f87171',
                            backgroundColor: 'rgba(248, 113, 113, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4,
                            pointBackgroundColor: '#f87171',
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: ctx => ctx.dataset.label + ': ' +
                                    ctx.parsed.y.toLocaleString('hu-HU') + ' Ft'
                            }
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: v => (v / 1000) + 'e'
                            },
                            grid: { color: '#111827' }
                        },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    } catch (e) {
        console.warn('Chart betoltes hiba:', e);
    }

    // 2) kategoria fankdiagram - switchCatView-bol jon (inline script)
    if (typeof switchCatView === 'function') {
        // ha van havi adat azt mutatjuk, kulonben osszeset
        const hasMonthly = typeof catMonthly !== 'undefined' && catMonthly.length > 0;
        switchCatView(hasMonthly ? 'monthly' : 'all');
    }
});
