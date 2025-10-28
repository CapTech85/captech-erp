// static/js/dashboard-polish.js
// Handles skeleton hide, content fade, count-up, and Chart.js dark-mode adaption

document.addEventListener("DOMContentLoaded", function () {
  // Helpers
  function formatMoney(num) {
    const nf = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return nf.format(Number(num || 0)) + " €";
  }

  // Remove skeletons
  document.querySelectorAll('.skeleton-placeholder').forEach(p => p.remove());

  // Fade-in content with stagger
  document.querySelectorAll('.content-fade').forEach((el, idx) => {
    el.style.opacity = 0;
    el.style.transform = 'translateY(6px)';
    el.style.transition = 'opacity 420ms ease, transform 420ms ease';
    setTimeout(() => {
      el.style.opacity = 1;
      el.style.transform = 'translateY(0)';
    }, 90 * idx);
  });

  // Count-up numbers
  function animateCount(el, endRaw, duration = 900) {
    const start = performance.now();
    const initialText = el.textContent || "";
    let initial = 0;
    // try to extract numeric start
    const found = initialText.replace(/\s/g, '').match(/[\d,.]+/);
    if (found) {
      initial = Number(found[0].replace(',', '.'));
    }
    const target = Number(endRaw) || 0;
    function step(ts) {
      const t = Math.min((ts - start) / duration, 1);
      const current = initial + (target - initial) * t;
      el.textContent = formatMoney(current);
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  document.querySelectorAll('.kpi-value').forEach(el => {
    const raw = el.getAttribute('data-value') || el.textContent;
    // If integer small number, show plain integer
    if (!String(raw).includes('.') && Number(raw) < 10000 && !el.textContent.includes('€')) {
      const start = performance.now();
      const to = Number(raw || 0);
      function step(ts) {
        const p = Math.min((ts - start) / 800, 1);
        el.textContent = Math.round(to * p);
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    } else {
      animateCount(el, raw, 900);
    }
  });

  // Chart.js sparkline init supporting dark mode
  function initSparkline() {
    const ctx = document.getElementById('caSpark');
    if (!ctx) return;
    const series = (window.DASHBOARD_CA_SERIES || []).map(v => Number(v || 0));
    const labels = series.map((_, i) => {
      const d = new Date();
      d.setMonth(d.getMonth() - (series.length - 1 - i));
      return d.toLocaleString('default', { month: 'short' });
    });

    const isDark = document.documentElement.classList.contains('dark');
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(2,6,23,0.06)';
    const tickColor = isDark ? '#94a3b8' : '#475569';
    const lineColor = isDark ? '#60a5fa' : '#2563eb';
    const fillColor = isDark ? 'rgba(96,165,250,0.06)' : 'rgba(37,99,235,0.08)';

    // Destroy existing chart if present (safe re-init)
    if (ctx._chart) {
      ctx._chart.destroy();
    }

    ctx._chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'CA 12 mois',
          data: series,
          borderColor: lineColor,
          backgroundColor: fillColor,
          fill: true,
          tension: 0.25,
          pointRadius: 0
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: tickColor }, grid: { color: gridColor } },
          y: { ticks: { color: tickColor }, grid: { color: gridColor } }
        },
        maintainAspectRatio: false,
        animation: {
          duration: 600
        }
      }
    });
  }

  initSparkline();

  // Re-init chart when theme toggled (observe root class changes)
  const observer = new MutationObserver(function () {
    initSparkline();
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
});
