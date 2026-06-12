// Optimized dashboard with caching and lazy loading
let spendingChart = null;
let pieChart = null;
let dataCache = {};

// Debounce function to prevent excessive requests
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Cache data in localStorage
function getCachedData(key, ttlMinutes = 5) {
    const cached = localStorage.getItem(key);
    if (!cached) return null;
    
    const data = JSON.parse(cached);
    const now = new Date().getTime();
    
    if (now - data.timestamp > ttlMinutes * 60 * 1000) {
        localStorage.removeItem(key);
        return null;
    }
    
    return data.value;
}

function setCachedData(key, value) {
    const data = {
        value: value,
        timestamp: new Date().getTime()
    };
    localStorage.setItem(key, JSON.stringify(data));
}

async function loadDashboard() {
    try {
        // Load stats with caching
        let stats = getCachedData('dashboard_stats');
        if (!stats) {
            const statsResponse = await fetch('/api/stats');
            stats = await statsResponse.json();
            setCachedData('dashboard_stats', stats);
        }
        
        updateUI(stats);
        
        // Load transactions
        let transactions = getCachedData('recent_transactions');
        if (!transactions) {
            const transactionsResponse = await fetch('/api/transactions?limit=10');
            transactions = await transactionsResponse.json();
            setCachedData('recent_transactions', transactions);
        }
        updateTransactionsTable(transactions);
        
        // Load charts
        const now = new Date();
        const month = now.getMonth() + 1;
        const year = now.getFullYear();
        
        let report = getCachedData(`monthly_report_${year}_${month}`);
        if (!report) {
            const reportResponse = await fetch(`/api/monthly_report?year=${year}&month=${month}`);
            report = await reportResponse.json();
            setCachedData(`monthly_report_${year}_${month}`, report);
        }
        updateCharts(report);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Error loading data', 'error');
    }
}

function updateUI(stats) {
    document.getElementById('monthly-income').innerText = `$${stats.current_month_income.toFixed(2)}`;
    document.getElementById('monthly-expense').innerText = `$${stats.current_month_expense.toFixed(2)}`;
    document.getElementById('monthly-savings').innerText = `$${stats.current_month_savings.toFixed(2)}`;
    document.getElementById('avg-expense').innerText = `$${stats.avg_monthly_expense.toFixed(2)}`;
    
    const expenseTrend = document.getElementById('expense-trend');
    if (stats.current_month_expense > stats.previous_month_expense) {
        expenseTrend.innerHTML = '↑ vs last month';
        expenseTrend.className = 'trend-up';
    } else {
        expenseTrend.innerHTML = '↓ vs last month';
        expenseTrend.className = 'trend-down';
    }
}

function updateTransactionsTable(transactions) {
    const tbody = document.querySelector('#recent-transactions tbody');
    tbody.innerHTML = '';
    
    transactions.slice(0, 5).forEach(t => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td data-label="Date">${t.date}</td>
            <td data-label="Description">${t.description}</td>
            <td data-label="Category">${t.icon || '📌'} ${t.category_name || 'Uncategorized'}</td>
            <td data-label="Amount" class="${t.type === 'income' ? 'text-success' : 'text-danger'}">$${t.amount.toFixed(2)}</td>
        `;
    });
}

async function updateCharts(report) {
    const ctx = document.getElementById('spending-chart');
    if (!ctx) return;
    
    if (spendingChart) spendingChart.destroy();
    
    // Get last 6 months data
    const now = new Date();
    const last6Months = [];
    const monthlyTotals = [];
    
    for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const monthName = d.toLocaleString('default', { month: 'short' });
        last6Months.push(monthName);
        
        let monthData = getCachedData(`monthly_report_${d.getFullYear()}_${d.getMonth() + 1}`);
        if (!monthData) {
            const response = await fetch(`/api/monthly_report?year=${d.getFullYear()}&month=${d.getMonth() + 1}`);
            monthData = await response.json();
            setCachedData(`monthly_report_${d.getFullYear()}_${d.getMonth() + 1}`, monthData);
        }
        monthlyTotals.push(monthData.expense);
    }
    
    spendingChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: last6Months,
            datasets: [{
                label: 'Monthly Expenses',
                data: monthlyTotals,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            },
            plugins: {
                legend: { labels: { color: '#fff' } },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#fff' } },
                x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#fff' } }
            }
        }
    });
    
    // Pie chart
    const pieCtx = document.getElementById('pie-chart');
    if (pieCtx && report.categories) {
        if (pieChart) pieChart.destroy();
        
        pieChart = new Chart(pieCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: report.categories.map(c => c.name),
                datasets: [{
                    data: report.categories.map(c => c.total),
                    backgroundColor: report.categories.map(c => c.color),
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '60%',
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#fff', font: { size: 12 } } }
                }
            }
        });
    }
}

// Debounced resize handler
window.addEventListener('resize', debounce(() => {
    if (spendingChart) spendingChart.resize();
    if (pieChart) pieChart.resize();
}, 250));

// Lazy load dashboard
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadDashboard);
} else {
    loadDashboard();
}

// Prefetch data for faster navigation
function prefetchData() {
    // Prefetch common data in background
    const now = new Date();
    const nextMonth = now.getMonth() + 2;
    if (nextMonth <= 12) {
        fetch(`/api/monthly_report?year=${now.getFullYear()}&month=${nextMonth}`)
            .then(r => r.json())
            .then(data => setCachedData(`monthly_report_${now.getFullYear()}_${nextMonth}`, data));
    }
}

// Start prefetching after page load
setTimeout(prefetchData, 2000);