document.addEventListener('DOMContentLoaded', () => {
  const raw = sessionStorage.getItem('auditReport');
  if (!raw) {
    document.getElementById('loadingOverlay').innerHTML =
      '<p style="color:#ef4444">No report data found. <a href="/" style="color:#3b82f6">Run a new audit</a>.</p>';
    return;
  }

  const data = JSON.parse(raw);
  renderReport(data);
});

function renderReport(data) {
  const overlay = document.getElementById('loadingOverlay');
  overlay.style.display = 'none';

  // Meta
  const p = data.portfolio;
  document.getElementById('reportMeta').textContent =
    `${data.current_broker_name} · AUM $${(p.aum).toLocaleString('en-US', {minimumFractionDigits:2})} · ${p.holdings_count} holdings`;

  // Module 1: Health Score
  const health = data.health;
  document.getElementById('moduleHealth').style.display = 'block';
  document.getElementById('healthScoreNum').textContent = health.score;
  document.getElementById('healthScoreNum').style.color = health.band_color;
  document.getElementById('healthBand').textContent = health.band;
  createHealthGauge('healthGauge', health.score, health.band_color);

  const penaltyNames = {
    cash_sweep: 'Cash Sweep Gap',
    options_cost: 'Options Contract Cost',
    maintenance_fee: 'Maintenance Fee',
    acats_exit: 'ACATS Exit Friction',
    mutual_fund_flags: 'Mutual Fund Restrictions',
  };
  const penaltiesDiv = document.getElementById('healthPenalties');
  penaltiesDiv.innerHTML = '<h3 style="color:#94a3b8;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px">Penalty Breakdown</h3>';
  for (const [key, pts] of Object.entries(health.penalties)) {
    const row = document.createElement('div');
    row.className = 'penalty-row';
    row.innerHTML = `
      <span class="penalty-label">${penaltyNames[key] || key}</span>
      <span class="penalty-value ${pts === 0 ? 'zero' : ''}">${pts === 0 ? '0 pts' : '-' + pts + ' pts'}</span>
    `;
    penaltiesDiv.appendChild(row);
  }

  // Module 2: Sweep Bar Chart
  document.getElementById('moduleSweep').style.display = 'block';
  const sweepLabels = [];
  const sweepValues = [];
  for (const [bid, v] of Object.entries(data.comparison)) {
    sweepLabels.push(v.broker_name.replace('Interactive Brokers Pro', 'IBKR Pro'));
    sweepValues.push(v.sweep.annual_loss_usd);
  }
  createSweepBarChart('sweepBarChart', sweepLabels, sweepValues, data.current_broker_name);
  const bestSweep = Math.max(...sweepValues);
  document.getElementById('sweepNote').textContent =
    `Positive = you'd earn more; Negative = you'd earn less. Best opportunity: $${bestSweep.toLocaleString('en-US', {minimumFractionDigits:2})}/yr`;

  // Module 3: Comparison Table
  document.getElementById('moduleTable').style.display = 'block';
  const tbody = document.getElementById('comparisonBody');
  for (const [bid, v] of Object.entries(data.comparison)) {
    const isCurrent = bid === data.current_broker_id;
    const isBest = bid === data.best_broker_id;
    const tr = document.createElement('tr');
    if (isCurrent) tr.className = 'current-broker';
    if (isBest) tr.className = 'best-broker';

    const savings = v.total_annual_savings_usd;
    const savingsClass = savings > 0 ? 'positive' : savings < 0 ? 'negative' : 'neutral';
    const breakeven = v.breakeven_months == null ? 'N/A' : v.breakeven_months === 0 ? '0' : v.breakeven_months + ' mo';

    tr.innerHTML = `
      <td>
        ${v.broker_name}
        ${isCurrent ? '<span class="broker-badge badge-current">Current</span>' : ''}
        ${isBest ? '<span class="broker-badge badge-best">Best</span>' : ''}
      </td>
      <td>${(v.sweep.target_apy * 100).toFixed(2)}%</td>
      <td class="${v.sweep.annual_loss_usd > 0 ? 'positive' : v.sweep.annual_loss_usd < 0 ? 'negative' : 'neutral'}">
        ${v.sweep.annual_loss_usd >= 0 ? '+' : ''}$${Math.abs(v.sweep.annual_loss_usd).toLocaleString('en-US', {minimumFractionDigits:2})}
      </td>
      <td class="${v.options.annual_savings_usd > 0 ? 'positive' : v.options.annual_savings_usd < 0 ? 'negative' : 'neutral'}">
        ${v.options.annual_savings_usd >= 0 ? '+' : ''}$${Math.abs(v.options.annual_savings_usd).toLocaleString('en-US', {minimumFractionDigits:2})}
      </td>
      <td class="${savingsClass}"><strong>${savings >= 0 ? '+' : ''}$${Math.abs(savings).toLocaleString('en-US', {minimumFractionDigits:2})}</strong></td>
      <td>${v.acats_exit_fee === 0 ? '<span class="positive">Free</span>' : '$' + v.acats_exit_fee}</td>
      <td>${breakeven}</td>
      <td>${!isCurrent ? '<button class="btn-cta" onclick="window.open(\'https://www.google.com/search?q=open+account+' + encodeURIComponent(v.broker_name) + '\',\'_blank\')">Switch Now</button>' : ''}</td>
    `;
    tbody.appendChild(tr);
  }

  // Module 4: Executive Summary
  document.getElementById('moduleSummary').style.display = 'block';
  document.getElementById('summaryPanel').textContent = data.executive_summary;

  // Flagged funds
  if (data.mutual_fund_flags && data.mutual_fund_flags.length > 0) {
    document.getElementById('moduleFunds').style.display = 'block';
    document.getElementById('flagNote').textContent =
      `The following mutual funds may have transfer restrictions or redemption fees: ${data.mutual_fund_flags.join(', ')}. Verify with your current broker before initiating an ACATS transfer.`;
  }
}
