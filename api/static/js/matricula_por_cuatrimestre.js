// static/js/matricula_por_cuatrimestre.js
document.addEventListener("DOMContentLoaded", function () {
  // ===== Registro opcional del plugin de etiquetas =====
  if (typeof Chart !== "undefined" && typeof ChartDataLabels !== "undefined") {
    Chart.register(ChartDataLabels);
  }
  console.log("[MPC] Chart.js:", (typeof Chart !== "undefined" ? Chart.version : "NO CARGADO"));

  // ===== Helpers =====
  function getEl(...ids) {
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) return el;
    }
    return null;
  }

  function colorFor(i, a = 0.75) {
    const h = (i * 47) % 360; // separación pseudo-prima para variedad
    const s = 70;
    const l = 55;
    const bg = `hsla(${h} ${s}% ${l}% / ${a})`;
    const bd = `hsl(${h} ${s}% ${Math.max(25, l - 15)}%)`;
    return { bg, bd };
  }

  function smooth(arr, k = 2) {
    const out = [];
    for (let i = 0; i < arr.length; i++) {
      let s = 0, c = 0;
      for (let j = i - k; j <= i + k; j++) {
        if (j >= 0 && j < arr.length) { s += (+arr[j] || 0); c++; }
      }
      out.push(s / (c || 1));
    }
    return out;
  }

  function sumArrays(arrays) {
    const n = arrays.reduce((m, a) => Math.max(m, a.length), 0);
    const out = new Array(n).fill(0);
    arrays.forEach(a => a.forEach((v, i) => out[i] += (+v || 0)));
    return out;
  }

  function readDatos() {
    let d = {};
    try {
      const node = document.getElementById("contenedorGraficas");
      if (node?.dataset?.graficaJson) d = JSON.parse(node.dataset.graficaJson);
    } catch (e) {
      console.warn("[MPC] Error parseando data-grafica-json:", e);
    }
    if ((!d || !d.labels) && typeof window !== "undefined" && window.MPC_DATOS) {
      d = window.MPC_DATOS;
    }
    // Normaliza estructura esperada por la vista nueva
    d.labels = Array.isArray(d.labels) ? d.labels : [];
    d.series = Array.isArray(d.series) ? d.series : [];
    d.pie_labels = Array.isArray(d.pie_labels) ? d.pie_labels : [];
    d.pie_values = Array.isArray(d.pie_values) ? d.pie_values : [];
    d.series = d.series.map(s => ({
      label: String(s.label ?? ""),
      data: Array.isArray(s.data) ? s.data.map(v => +v || 0) : []
    }));
    // Fallback: si no vinieron datos de pie, calcúlalos desde las series
    if (!d.pie_labels.length || !d.pie_values.length) {
      d.pie_labels = d.series.map(s => s.label);
      d.pie_values = d.series.map(s => s.data.reduce((a, b) => a + (+b || 0), 0));
    } else {
      d.pie_values = d.pie_values.map(v => +v || 0);
    }
    return d;
  }

  const datos = readDatos();
  const labels = datos.labels;
  const series = datos.series;
  const pieLabels = datos.pie_labels;
  const pieValues = datos.pie_values;

  if (typeof Chart === "undefined") {
    console.error("[MPC] Falta Chart.js (carga el script antes de este).");
    return;
  }
  if (!labels.length || !series.length) {
    console.warn("[MPC] No hay datos para graficar (labels/series vacíos).");
    return;
  }

  // ===== Canvases (soporta IDs nuevos y legados) =====
  const cBarras = getEl("graficaBarras", "chBar");
  const cLinea  = getEl("graficaLinea",  "chLine");
  const cPastel = getEl("graficaPastel", "chPie");
  const cGauss  = getEl("graficaGauss",  "chGauss");

  // ===== Datasets por materia =====
  const dsBarLine = series.map((s, i) => {
    const { bg, bd } = colorFor(i);
    return {
      label: s.label || `Serie ${i + 1}`,
      data: s.data,
      backgroundColor: bg,
      borderColor: bd,
      borderWidth: 2,
      fill: false
    };
  });

  // ===== Config común =====
  const commonScales = { y: { beginAtZero: true, ticks: { precision: 0 } } };
  const useDL = (typeof ChartDataLabels !== "undefined");
  const dlCommon = useDL ? {
    datalabels: {
      color: '#111',
      anchor: 'end',
      align: 'top',
      clamp: true,
      formatter: (value) => (value > 0 ? value : ''),
      font: { weight: '700' }
    }
  } : {};

  // ===== Barras =====
  if (cBarras) {
    new Chart(cBarras, {
      type: 'bar',
      data: { labels, datasets: dsBarLine.map(d => ({ ...d, fill: true })) },
      options: {
        responsive: true,
        scales: commonScales,
        plugins: {
          legend: { position: 'bottom' },
          ...dlCommon
        }
      }
    });
  } else {
    console.warn("[MPC] No se encontró canvas de Barras (graficaBarras/chBar).");
  }

  // ===== Línea =====
  if (cLinea) {
    new Chart(cLinea, {
      type: 'line',
      data: { labels, datasets: dsBarLine.map(d => ({ ...d, fill: false, tension: 0.35 })) },
      options: {
        responsive: true,
        scales: commonScales,
        plugins: {
          legend: { position: 'bottom' },
          ...(useDL ? {
            datalabels: {
              color: '#111',
              align: 'top',
              formatter: (value) => (value > 0 ? value : ''),
              font: { weight: '700' }
            }
          } : {})
        }
      }
    });
  } else {
    console.warn("[MPC] No se encontró canvas de Línea (graficaLinea/chLine).");
  }

  // ===== Pastel (participación por materia) =====
  if (cPastel && pieLabels.length && pieValues.length) {
    const pieBG = pieLabels.map((_, i) => colorFor(i, 0.75).bg);
    const pieBD = pieLabels.map((_, i) => colorFor(i, 0.75).bd);

    new Chart(cPastel, {
      type: 'pie',
      data: {
        labels: pieLabels,
        datasets: [{ data: pieValues, backgroundColor: pieBG, borderColor: pieBD }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          ...(useDL ? {
            datalabels: {
              formatter: (value, ctx) => {
                const total = (ctx.chart.data.datasets[0].data || []).reduce((a, b) => a + (+b || 0), 0);
                if (!total) return '';
                const pct = (value / total) * 100;
                return `${value} (${pct.toFixed(1)}%)`;
              },
              color: '#111',
              font: { weight: '700' }
            }
          } : {})
        }
      }
    });
  } else if (!cPastel) {
    console.warn("[MPC] No se encontró canvas de Pastel (graficaPastel/chPie).");
  }

  // ===== Gauss (suavizado del total de todas las materias) =====
  if (cGauss) {
    const totalPorPeriodo = sumArrays(series.map(s => s.data));
    const suavizado = smooth(totalPorPeriodo, 2);

    new Chart(cGauss, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Total Suavizado',
          data: suavizado,
          backgroundColor: 'hsla(210 70% 70% / .35)',
          borderColor: 'hsl(210 70% 40%)',
          borderWidth: 2,
          fill: true,
          tension: 0.45
        }]
      },
      options: {
        responsive: true,
        scales: commonScales,
        plugins: {
          legend: { display: false },
          ...(useDL ? {
            datalabels: {
              color: '#111',
              align: 'top',
              formatter: (value) => (value > 0 ? Math.round(value) : ''),
              font: { weight: '700' }
            }
          } : {})
        }
      }
    });
  } else {
    console.warn("[MPC] No se encontró canvas de Gauss (graficaGauss/chGauss).");
  }

  // ===== Mostrar/ocultar tarjetas por checks (si existen) =====
  document.querySelectorAll('.mc-chk').forEach(chk => {
    chk.addEventListener('change', () => {
      const map = { barras: 'box-barras', linea: 'box-linea', pastel: 'box-pastel', gauss: 'box-gauss' };
      const id = map[chk.value]; const el = document.getElementById(id);
      if (el) el.style.display = chk.checked ? '' : 'none';
    });
  });

  // ===== Exportar PDF (ignorar .no-print de forma explícita) =====
  const btnPDF = document.getElementById("btnDescargarPDF");
  if (btnPDF && typeof html2pdf !== "undefined") {
    btnPDF.addEventListener("click", () => {
      // Exporta SOLO el contenido (tabla + gráficas)
      const area = document.getElementById("contenidoPDF") || document.getElementById("pdfArea") || document.body;

      // Oculta .no-print por si el clon conserva estilos
      const ocultar = document.querySelectorAll(".no-print");
      ocultar.forEach(el => el.classList.add("hidden-print"));
      document.documentElement.classList.add("printing");

      const opt = {
        margin: 0,
        filename: "matricula_por_cuatrimestre.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          // Ignora cualquier elemento con .no-print (o dentro de .no-print)
          ignoreElements: (el) =>
            el.classList?.contains("no-print") ||
            el.closest?.(".no-print") ||
            el.dataset?.html2canvasIgnore === "true"
        },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
      };

      html2pdf().set(opt).from(area).save().finally(() => {
        // Restaura visibilidad
        ocultar.forEach(el => el.classList.remove("hidden-print"));
        document.documentElement.classList.remove("printing");
      });
    });
  }
});
