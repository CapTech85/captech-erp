// static/js/dashboard-polish.js
document.addEventListener("DOMContentLoaded", function () {
  // Helper: format FR money
  function formatMoney(num) {
    const nf = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return nf.format(Number(num)) + " €";
  }

  // Remove skeleton and animate content
  const placeholders = document.querySelectorAll('.skeleton-placeholder');
  placeholders.forEach(p => p.style.display = 'none');

  const contents = document.querySelectorAll('.content-fade');
  contents.forEach((el, idx) => {
    el.style.transition = 'opacity 420ms ease, transform 420ms ease';
    el.style.opacity = 0;
    el.style.transform = 'translateY(6px)';
    // Staggered reveal
    setTimeout(() => {
      el.style.opacity = 1;
      el.style.transform = 'translateY(0)';
    }, 80 * idx);
  });

  // Count-up animation for KPI numbers
  function animateCount(el, endValue, duration = 900) {
    const start = performance.now();
    const initial = Number(el.textContent.replace(/[^0-9\-,.]/g, '').replace(',', '.')) || 0;
    const to = Number(endValue) || 0;
    function step(ts) {
      const progress = Math.min((ts - start) / duration, 1);
      const current = initial + (to - initial) * progress;
      el.textContent = formatMoney(current);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  document.querySelectorAll('.kpi-value').forEach(el => {
    const raw = el.getAttribute('data-value');
    // if raw is integer client count, render without € sign
    const isInteger = !raw.includes('.');
    if (isInteger && Number(raw) < 10000 && !el.textContent.includes('€')) {
      // simple numeric counter without currency
      const start = performance.now();
      const to = Number(raw || 0);
      const duration = 800;
      function step(ts) {
        const progress = Math.min((ts - start) / duration, 1);
        const current = Math.round(to * progress);
        el.textContent = current;
        if (progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    } else {
      animateCount(el, raw, 900);
    }
  });

  // Initialize Chart.js sparkline if present
  if (window.DASHBOARD_CA_SERIES) {
    const ctx = document.getElementById('caSpark');
    if (ctx) {
      const series = (window.DASHBOARD_CA_SERIES || []).map(v => Number(v || 0));
      const labels = series.map((_, i) => {
        const d = new Date();
        d.setMonth(d.getMonth() - (series.length - 1 - i));
        return d.toLocaleString('default', { month: 'short' });
      });
      new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'CA 12 mois',
            data: series,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37,99,235,0.08)',
            fill: true,
            tension: 0.25,
            pointRadius: 0
          }]
        },
        options: {
          plugins: { legend: { display: false } },
          scales: { x: { display: true }, y: { display: true } },
          maintainAspectRatio: false,
        }
      });
    }
  }
});
