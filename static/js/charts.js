const CHART_COLORS = {
  viáticos: '#FF6B35',
  despensas: '#06D6A0',
  servicios: '#118AB2',
  suntuarios: '#EF476F',
  prestamos: '#FFD166',
  trabajo: '#8338EC',
  sueldo: '#2ECC71',
  refacciones: '#E76F51',
  alquiler: '#457B9D',
  'e-commerce': '#F4A261',
  insumos: '#1ABC9C',
  otros: '#9090a8'
};

let donutChartInstance = null;
let lineChartInstance = null;

function getChartFontColor() {
  const html = document.documentElement;
  return html.getAttribute('data-theme') === 'dark' ? '#f0f0f5' : '#1a1a2e';
}

function getChartGridColor() {
  const html = document.documentElement;
  return html.getAttribute('data-theme') === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';
}

function renderDonutChart(gastosPorCategoria) {
  const ctx = document.getElementById('donutChart');
  if (!ctx) return;
  const labels = Object.keys(gastosPorCategoria);
  const values = Object.values(gastosPorCategoria);
  const colors = labels.map(l => CHART_COLORS[l] || '#9090a8');
  const fontColor = getChartFontColor();

  if (donutChartInstance) donutChartInstance.destroy();

  if (values.length === 0) {
    donutChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Sin datos'],
        datasets: [{ data: [1], backgroundColor: ['#2a2a44'], borderWidth: 0 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: fontColor, padding: 16, usePointStyle: true, font: { size: 11 } } }
        }
      }
    });
    return;
  }

  donutChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-card').trim() || '#1e1e32',
        borderWidth: 3,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: fontColor, padding: 16, usePointStyle: true, font: { size: 11, weight: '500' } }
        },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: function(ctx) {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = ((ctx.parsed / total) * 100).toFixed(1);
              return ` $${ctx.parsed.toLocaleString('es', {minimumFractionDigits: 2})} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

function renderLineChart(evolucion) {
  const ctx = document.getElementById('lineChart');
  if (!ctx) return;
  const fontColor = getChartFontColor();
  const gridColor = getChartGridColor();

  if (lineChartInstance) lineChartInstance.destroy();

  if (!evolucion || evolucion.length === 0) {
    lineChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          { label: 'Ingresos', data: [], borderColor: '#06D6A0', backgroundColor: 'rgba(6,214,160,0.1)', fill: true },
          { label: 'Gastos', data: [], borderColor: '#EF476F', backgroundColor: 'rgba(239,71,111,0.1)', fill: true }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, labels: { color: fontColor } }
        }
      }
    });
    return;
  }

  const labels = evolucion.map(e => e.periodo_label);
  const ingresos = evolucion.map(e => e.ingreso);
  const egresos = evolucion.map(e => e.egreso);

  lineChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Ingresos',
          data: ingresos,
          borderColor: '#06D6A0',
          backgroundColor: 'rgba(6, 214, 160, 0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#06D6A0',
          borderWidth: 2.5
        },
        {
          label: 'Gastos',
          data: egresos,
          borderColor: '#EF476F',
          backgroundColor: 'rgba(239, 71, 111, 0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#EF476F',
          borderWidth: 2.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: { color: fontColor, usePointStyle: true, padding: 16, font: { size: 11 } }
        },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: function(ctx) {
              return ` ${ctx.dataset.label}: $${ctx.parsed.y.toLocaleString('es', {minimumFractionDigits: 2})}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: fontColor, font: { size: 10 } }
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: fontColor,
            font: { size: 10 },
            callback: function(value) { return '$' + value.toLocaleString('es'); }
          }
        }
      }
    }
  });
}

function redrawCharts() {
  if (donutChartInstance) {
    const fontColor = getChartFontColor();
    const gridColor = getChartGridColor();
    donutChartInstance.options.plugins.legend.labels.color = fontColor;
    lineChartInstance.options.plugins.legend.labels.color = fontColor;
    lineChartInstance.options.scales.x.ticks.color = fontColor;
    lineChartInstance.options.scales.y.ticks.color = fontColor;
    lineChartInstance.options.scales.x.grid.color = gridColor;
    lineChartInstance.options.scales.y.grid.color = gridColor;
    donutChartInstance.update();
    lineChartInstance.update();
  }
}

if (window.matchMedia) {
  const observer = new MutationObserver(() => redrawCharts());
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}
