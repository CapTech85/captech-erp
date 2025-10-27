// static/js/dashboard.js
document.addEventListener("DOMContentLoaded", function () {
  const el = document.getElementById("caSpark");
  if (!el) return;
  const series = (window.DASHBOARD_CA_SERIES || []).map(v => Number(v || 0));
  const labels = series.map((_,i) => {
    const d = new Date();
    d.setMonth(d.getMonth() - (series.length - 1 - i));
    return d.toLocaleString('default', { month: 'short' });
  });

  new Chart(el, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "CA 12 mois",
        data: series,
        borderColor: "#2563eb",
        backgroundColor: "rgba(37,99,235,0.08)",
        fill: true,
        tension: 0.25,
        pointRadius: 0
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { display: true },
        y: { display: true }
      },
      maintainAspectRatio: false,
    }
  });
});
