let allSessions = [];
let allDaily = [];
let filteredSessions = [];

let revenueChannelChartInstance = null;
let dropoffDeviceChartInstance = null;
let dailyRevenueChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
    setupEventListeners();
    applyFilters();
    setupTheme();
});

// Load data from exported JSON
async function loadDashboardData() {
    try {
        const response = await fetch('dashboard_data.json');
        const data = await response.json();
        allSessions = data.sessions;
        allDaily = data.daily;
        filteredSessions = [...allSessions];
    } catch (error) {
        console.error('Error loading dashboard dataset:', error);
    }
}

// Setup Event Listeners
function setupEventListeners() {
    document.getElementById('channelFilter').addEventListener('change', applyFilters);
    document.getElementById('deviceFilter').addEventListener('change', applyFilters);
    document.getElementById('regionFilter').addEventListener('change', applyFilters);
    document.getElementById('categoryFilter').addEventListener('change', applyFilters);
    
    document.getElementById('resetFiltersBtn').addEventListener('click', () => {
        document.getElementById('channelFilter').value = 'ALL';
        document.getElementById('deviceFilter').value = 'ALL';
        document.getElementById('regionFilter').value = 'ALL';
        document.getElementById('categoryFilter').value = 'ALL';
        applyFilters();
    });

    document.getElementById('improvementSlider').addEventListener('input', updateCalculator);
    document.getElementById('tableSearch').addEventListener('input', renderSessionTable);
}

// Dark / Light Theme Toggle
function setupTheme() {
    const themeBtn = document.getElementById('themeToggleBtn');
    themeBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', nextTheme);
        renderCharts(); // Re-render charts with updated theme colors
    });
}

// Apply Filters
function applyFilters() {
    const channel = document.getElementById('channelFilter').value;
    const device = document.getElementById('deviceFilter').value;
    const region = document.getElementById('regionFilter').value;
    const category = document.getElementById('categoryFilter').value;

    filteredSessions = allSessions.filter(s => {
        if (channel !== 'ALL' && s.Channel !== channel) return false;
        if (device !== 'ALL' && s.Device !== device) return false;
        if (region !== 'ALL' && s.Region !== region) return false;
        if (category !== 'ALL' && s.Product_Category !== category) return false;
        return true;
    });

    updateKPICards();
    renderCharts();
    updateCalculator();
    renderSessionTable();
}

// Update KPI Cards
function updateKPICards() {
    const total = filteredSessions.length;
    if (total === 0) {
        document.getElementById('kpiBrowsePct').innerText = '0.00%';
        document.getElementById('kpiCartPct').innerText = '0.00%';
        document.getElementById('kpiCheckoutPct').innerText = '0.00%';
        document.getElementById('kpiPurchasePct').innerText = '0.00%';
        return;
    }

    const browseCount = filteredSessions.filter(s => s.Reached_Browse === 1).length;
    const cartCount = filteredSessions.filter(s => s.Reached_Add_to_Cart === 1).length;
    const checkoutCount = filteredSessions.filter(s => s.Reached_Checkout === 1).length;
    const purchaseCount = filteredSessions.filter(s => s.Reached_Purchase === 1).length;

    document.getElementById('kpiBrowsePct').innerText = ((browseCount / total) * 100).toFixed(2) + '%';
    document.getElementById('kpiCartPct').innerText = ((cartCount / total) * 100).toFixed(2) + '%';
    document.getElementById('kpiCheckoutPct').innerText = ((checkoutCount / total) * 100).toFixed(2) + '%';
    document.getElementById('kpiPurchasePct').innerText = ((purchaseCount / total) * 100).toFixed(2) + '%';

    document.getElementById('kpiBrowseCount').innerText = `${browseCount.toLocaleString()} sessions`;
    document.getElementById('kpiCartCount').innerText = `${cartCount.toLocaleString()} sessions`;
    document.getElementById('kpiCheckoutCount').innerText = `${checkoutCount.toLocaleString()} sessions`;
    document.getElementById('kpiPurchaseCount').innerText = `${purchaseCount.toLocaleString()} sessions`;
}

// Render Charts
function renderCharts() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#f9fafb' : '#1f2937';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';

    // 1. Revenue by Channel Chart
    const channels = ['Email', 'Google Ads', 'Social Media', 'Organic'];
    const channelRevenues = channels.map(ch => {
        return filteredSessions
            .filter(s => s.Channel === ch)
            .reduce((sum, s) => sum + (s.Total_Revenue || 0), 0);
    });

    const ctx1 = document.getElementById('revenueChannelChart').getContext('2d');
    if (revenueChannelChartInstance) revenueChannelChartInstance.destroy();

    revenueChannelChartInstance = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: channels,
            datasets: [{
                label: 'Revenue ($)',
                data: channelRevenues,
                backgroundColor: [
                    '#3b82f6', // Email
                    '#1e3a8a', // Google Ads
                    '#ea580c', // Social Media
                    '#7e22ce'  // Organic
                ],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `$${ctx.raw.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`
                    }
                }
            },
            scales: {
                x: { ticks: { color: textColor }, grid: { display: false } },
                y: {
                    ticks: {
                        color: textColor,
                        callback: (val) => `$${(val / 1000).toFixed(0)}K`
                    },
                    grid: { color: gridColor }
                }
            }
        }
    });

    // 2. Drop Off Rate by Device Chart
    const devices = ['Desktop', 'Mobile', 'Tablet'];
    const deviceDropOffs = devices.map(dev => {
        const devSessions = filteredSessions.filter(s => s.Device === dev);
        if (devSessions.length === 0) return 0;
        const devPurchases = devSessions.filter(s => s.Reached_Purchase === 1).length;
        return (1 - (devPurchases / devSessions.length)).toFixed(2);
    });

    const ctx2 = document.getElementById('dropoffDeviceChart').getContext('2d');
    if (dropoffDeviceChartInstance) dropoffDeviceChartInstance.destroy();

    dropoffDeviceChartInstance = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: devices,
            datasets: [{
                label: 'Drop Off Rate',
                data: deviceDropOffs,
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Drop Off Rate: ${ctx.raw}`
                    }
                }
            },
            scales: {
                x: { min: 0, max: 1.0, ticks: { color: textColor }, grid: { color: gridColor } },
                y: { ticks: { color: textColor }, grid: { display: false } }
            }
        }
    });

    // 3. Sum of Revenue by Day (Line Chart)
    const dailyMap = {};
    filteredSessions.forEach(s => {
        const date = s.Date;
        if (!dailyMap[date]) dailyMap[date] = 0;
        dailyMap[date] += (s.Total_Revenue || 0);
    });

    const sortedDates = Object.keys(dailyMap).sort();
    const dailyRevenueVals = sortedDates.map(d => dailyMap[d]);

    const ctx3 = document.getElementById('dailyRevenueChart').getContext('2d');
    if (dailyRevenueChartInstance) dailyRevenueChartInstance.destroy();

    dailyRevenueChartInstance = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: sortedDates.map(d => d.split('-')[2]), // Display day of month
            datasets: [{
                label: 'Sum of Revenue',
                data: dailyRevenueVals,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Revenue: $${ctx.raw.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`
                    }
                }
            },
            scales: {
                x: { ticks: { color: textColor }, grid: { display: false } },
                y: {
                    ticks: {
                        color: textColor,
                        callback: (val) => `$${(val / 1000).toFixed(0)}K`
                    },
                    grid: { color: gridColor }
                }
            }
        }
    });
}

// Update Interactive ABM Revenue Recovery Simulator
function updateCalculator() {
    const sliderVal = parseInt(document.getElementById('improvementSlider').value);
    document.getElementById('sliderValue').innerText = `${sliderVal}% Improvement`;

    const checkoutCount = filteredSessions.filter(s => s.Reached_Checkout === 1).length;
    const purchaseCount = filteredSessions.filter(s => s.Reached_Purchase === 1).length;
    const abandoners = Math.max(0, checkoutCount - purchaseCount);

    // Calculate AOV for filtered converted sessions
    const totalRev = filteredSessions.reduce((sum, s) => sum + (s.Total_Revenue || 0), 0);
    const aov = purchaseCount > 0 ? (totalRev / purchaseCount) : 1089.26;

    const recoveredOrders = Math.round(abandoners * (sliderVal / 100));
    const projectedRevenue = recoveredOrders * aov;

    document.getElementById('calcOrders').innerText = `${recoveredOrders.toLocaleString()} orders`;
    document.getElementById('calcRevenue').innerText = `$${projectedRevenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Render Session Data Explorer Table
function renderSessionTable() {
    const tbody = document.getElementById('sessionTableBody');
    const query = document.getElementById('tableSearch').value.toLowerCase().trim();

    const displaySessions = filteredSessions.filter(s => {
        if (!query) return true;
        return (
            s.Session_ID.toLowerCase().includes(query) ||
            s.User_ID.toLowerCase().includes(query) ||
            s.Channel.toLowerCase().includes(query) ||
            s.Device.toLowerCase().includes(query) ||
            s.Region.toLowerCase().includes(query) ||
            s.Product_Category.toLowerCase().includes(query)
        );
    }).slice(0, 50); // Top 50 rows for fast UI rendering

    tbody.innerHTML = displaySessions.map(s => {
        const stageClass = `stage-${s.Reached_Purchase ? 4 : (s.Reached_Checkout ? 3 : (s.Reached_Add_to_Cart ? 2 : 1))}`;
        return `
            <tr>
                <td><strong>${s.Session_ID}</strong></td>
                <td>${s.User_ID}</td>
                <td>${s.Date}</td>
                <td>${s.Channel}</td>
                <td>${s.Device}</td>
                <td>${s.Region}</td>
                <td>${s.Product_Category}</td>
                <td><span class="stage-badge ${stageClass}">${s.Max_Stage_Reached}</span></td>
                <td>$${(s.Total_Revenue || 0).toFixed(2)}</td>
            </tr>
        `;
    }).join('');
}
