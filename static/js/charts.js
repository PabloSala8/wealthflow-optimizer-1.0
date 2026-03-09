function createHealthGauge(canvasId, score, color) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const remaining = 100 - score;
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [score, remaining],
        backgroundColor: [color, 'rgba(45,63,107,0.4)'],
        borderWidth: 0,
        circumference: 270,
        rotation: 225,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '78%',
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
    }
  });
}

function createSweepBarChart(canvasId, labels, values, currentBrokerName) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  const colors = values.map(v => v > 0 ? '#10b981' : v < 0 ? '#ef4444' : '#64748b');
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Annual Sweep Opportunity (USD)',
        data: values,
        backgroundColor: colors,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const v = ctx.raw;
              return ` $${Math.abs(v).toLocaleString('en-US', {minimumFractionDigits:2})} ${v >= 0 ? 'gain' : 'loss'}`;
            }
          }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(45,63,107,0.5)' }, ticks: { color: '#94a3b8' } },
        y: {
          grid: { color: 'rgba(45,63,107,0.5)' },
          ticks: {
            color: '#94a3b8',
            callback: v => '$' + v.toLocaleString('en-US')
          }
        }
      }
    }
  });
}
