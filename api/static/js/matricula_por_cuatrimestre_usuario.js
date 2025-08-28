// static/js/matricula_por_cuatrimestre_usuario.js
document.addEventListener("DOMContentLoaded", function () {
  if (typeof Chart !== "undefined" && typeof ChartDataLabels !== "undefined") {
    Chart.register(ChartDataLabels);
  }

  function colorFor(i, a = 0.75) {
    const h = (i * 47) % 360, s = 70, l = 55;
    return {
      bg: `hsla(${h} ${s}% ${l}% / ${a})`,
      bd: `hsl(${h} ${s}% ${Math.max(25, l - 15)}%)`
    };
  }
  function smooth(arr, k = 2) {
    const out = [];
    for (let i = 0; i < arr.length; i++) {
      let s = 0, c = 0;
      for (let j = i - k; j <= i + k; j++) if (j >= 0 && j < arr.length) { s += (+arr[j] || 0); c++; }
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
    } catch {}
    if ((!d || !d.labels) && typeof window !== "undefined" && window.MPC_DATOS) {
      d = window.MPC_DATOS;
    }
    d.labels = Array.isArray(d.labels) ? d.labels : [];
    d.series = Array.isArray(d.series) ? d.series : [];
    d.pie_labels = Array.isArray(d.pie_labels) ? d.pie_labels : [];
    d.pie_values = Array.isArray(d.pie_values) ? d.pie_values : [];
    d.series = d.series.map(s => ({ label: String(s.label ?? ""), data: (s.data || []).map(v => +v || 0) }));
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

  if (typeof Chart === "undefined") { console.error("[MPC] Falta Chart.js"); return; }
  if (!labels.length || !series.length) { console.warn("[MPC] Sin datos para graficar."); return; }

  const cBarras = document.getElementById("graficaBarras");
  const cLinea  = document.getElementById("graficaLinea");
  const cPastel = document.getElementById("graficaPastel");
  const cGauss  = document.getElementById("graficaGauss");

  const dsBarLine = series.map((s, i) => {
    const { bg, bd } = colorFor(i);
    return { label: s.label || `Serie ${i+1}`, data: s.data, backgroundColor: bg, borderColor: bd, borderWidth: 2, fill: false };
  });

  const commonScales = { y: { beginAtZero: true, ticks: { precision: 0 } } };
  const useDL = (typeof ChartDataLabels !== "undefined");
  const dlCommon = useDL ? {
    datalabels: { color:'#111', anchor:'end', align:'top', clamp:true, formatter:(v)=> v>0? v:'', font:{weight:'700'} }
  } : {};

  // Barras
  if (cBarras) {
    new Chart(cBarras, {
      type: 'bar',
      data: { labels, datasets: dsBarLine.map(d => ({ ...d, fill: true })) },
      options: { responsive: true, scales: commonScales, plugins: { legend:{ position:'bottom' }, ...dlCommon } }
    });
  }
  // Línea
  if (cLinea) {
    new Chart(cLinea, {
      type: 'line',
      data: { labels, datasets: dsBarLine.map(d => ({ ...d, tension:0.35 })) },
      options: { responsive: true, scales: commonScales, plugins: { legend:{ position:'bottom' }, ...(useDL? { datalabels:{ color:'#111', align:'top', formatter:(v)=> v>0? v:'', font:{weight:'700'} } }: {}) } }
    });
  }
  // Pastel
  if (cPastel && pieLabels.length && pieValues.length) {
    const pieBG = pieLabels.map((_, i) => colorFor(i, 0.75).bg);
    const pieBD = pieLabels.map((_, i) => colorFor(i, 0.75).bd);
    new Chart(cPastel, {
      type: 'pie',
      data: { labels: pieLabels, datasets: [{ data: pieValues, backgroundColor: pieBG, borderColor: pieBD }] },
      options: { responsive: true, plugins: { legend:{ position:'bottom' }, ...(useDL? { datalabels:{ formatter:(value, ctx)=>{ const t=(ctx.chart.data.datasets[0].data||[]).reduce((a,b)=>a+(+b||0),0); if(!t)return''; const p=(value/t)*100; return `${value} (${p.toFixed(1)}%)`; }, color:'#111', font:{weight:'700'} } }: {}) } }
    });
  }
  // Gauss (total suavizado)
  if (cGauss) {
    const total = series.reduce((acc, s) => acc.map((v,i)=> v + (+s.data[i]||0)), new Array(labels.length).fill(0));
    const suavizado = smooth(total, 2);
    new Chart(cGauss, {
      type: 'line',
      data: { labels, datasets: [{ label:'Total Suavizado', data:suavizado, backgroundColor:'hsla(210 70% 70% / .35)', borderColor:'hsl(210 70% 40%)', borderWidth:2, fill:true, tension:0.45 }] },
      options: { responsive: true, scales: commonScales, plugins: { legend:{ display:false }, ...(useDL? { datalabels:{ color:'#111', align:'top', formatter:(v)=> v>0? Math.round(v):'', font:{weight:'700'} } }: {}) } }
    });
  }

  // Exportar PDF (sin filtros)
  const btnPDF = document.getElementById("btnDescargarPDF");
  if (btnPDF && typeof html2pdf !== "undefined") {
    btnPDF.addEventListener("click", () => {
      const area = document.getElementById("contenidoPDF") || document.body;
      const ocultar = document.querySelectorAll(".no-print");
      ocultar.forEach(el => el.classList.add("hidden-print"));
      const opt = {
        margin: 0,
        filename: "matricula_por_cuatrimestre.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: {
          scale: 2, useCORS: true,
          ignoreElements: (el) => el.classList?.contains("no-print") || el.closest?.(".no-print") || el.dataset?.html2canvasIgnore === "true"
        },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
      };
      html2pdf().set(opt).from(area).save().finally(() => {
        ocultar.forEach(el => el.classList.remove("hidden-print"));
      });
    });
  }
});
