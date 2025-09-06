// static/js/aprovechamiento.js
document.addEventListener("DOMContentLoaded", function () {
  // --------- refs ----------
  const elDatos = document.getElementById("datosGraficas");
  const formFiltros = document.getElementById("filter-form");

  // Programas
  const btnProgAll = document.getElementById("select-all-prog");
  const btnProgNone = document.getElementById("clear-all-prog");
  const progChecks = document.querySelectorAll('input[name="programas[]"]');

  // Gráficas
  const chkGraficas = document.querySelectorAll(".grafica-check");
  const btnGrafAll = document.getElementById("graficas-all");
  const btnGrafNone = document.getElementById("graficas-none");
  const btnGrafApply = document.getElementById("aplicarGraficas");

  // Canvas IDs
  const CANVAS_IDS = {
    barras: "graficaBarras",
    linea: "graficaLinea",
    pastel: "graficaPastel",
    gauss: "graficaGauss"
  };

  // --------- datos ----------
  let datos = { programas: [], promedios: [], tipos: [] };
  try {
    if (elDatos && (elDatos.textContent || "").trim()) {
      datos = JSON.parse(elDatos.textContent);
    }
  } catch (e) {
    console.error("[Aprovechamiento] JSON inválido:", e);
  }
  console.log("[Aprovechamiento] puntos:", datos.programas ? datos.programas.length : 0);

  // --------- seleccionar/limpiar programas ----------
  if (btnProgAll) {
    btnProgAll.addEventListener("click", function () {
      progChecks.forEach(cb => { cb.checked = true; });
      if (formFiltros) formFiltros.submit();
    });
  }
  if (btnProgNone) {
    btnProgNone.addEventListener("click", function () {
      progChecks.forEach(cb => { cb.checked = false; });
      if (formFiltros) formFiltros.submit();
    });
  }

  // --------- gráficas ----------
  const charts = {};
  const hasChart = typeof Chart !== "undefined";
  const hasDatalabels = typeof ChartDataLabels !== "undefined";
  const basePlugins = hasDatalabels ? [ChartDataLabels] : [];
  const defaultGenLabels = hasChart ? (Chart.defaults?.plugins?.legend?.labels?.generateLabels) : null;

  function activasDesdeUI() {
    return Array.from(chkGraficas)
      .filter(cb => cb.checked)
      .map(cb => cb.value);
  }

  function mostrarOcultarBoxes(activas) {
    document.querySelectorAll(".grafica-box").forEach(box => {
      const tipo = box.id.replace("box-", "");
      box.style.display = activas.includes(tipo) ? "" : "none";
    });
  }

  function destruirGraficasPrevias() {
    Object.values(charts).forEach(ch => {
      if (ch && typeof ch.destroy === "function") ch.destroy();
    });
  }

  function renderGraficas(activas) {
    if (!hasChart) {
      console.error("[Aprovechamiento] Chart.js no cargado.");
      return;
    }

    destruirGraficasPrevias();
    mostrarOcultarBoxes(activas);

    const labels = Array.isArray(datos.programas) ? datos.programas : [];
    const valores = Array.isArray(datos.promedios) ? datos.promedios.map(v => Number(v) || 0) : [];
    const tipos = Array.isArray(datos.tipos) ? datos.tipos : [];

    if (!labels.length) return;

    const colores = tipos.map(t => (t === "antiguo" ? "rgba(75, 192, 192, 0.7)" : "rgba(153, 102, 255, 0.7)"));

    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: 20 },
      plugins: {
        legend: {
          position: "top",
          labels: defaultGenLabels ? {
            generateLabels: function (chart) {
              const arr = defaultGenLabels(chart);
              arr.forEach(l => {
                if (/(Antiguo)/.test(l.text)) l.fillStyle = "rgba(75, 192, 192, 0.7)";
                else if (/(Nuevo)/.test(l.text)) l.fillStyle = "rgba(153, 102, 255, 0.7)";
              });
              return arr;
            }
          } : {}
        },
        datalabels: {
          anchor: "end",
          align: "top",
          formatter: function (v) { return Number(v).toFixed(2); },
          font: { weight: "bold" }
        }
      },
      scales: {
        x: {
          ticks: {
            autoSkip: false,
            maxRotation: 45,
            minRotation: 30,
            callback: function (val) {
              const txt = this.getLabelForValue(val);
              return (txt && txt.length > 20) ? (txt.slice(0, 20) + "…") : txt;
            }
          }
        }
      }
    };

    // Barras
    if (activas.includes("barras")) {
      const ctxB = document.getElementById(CANVAS_IDS.barras);
      if (ctxB) {
        charts.barras = new Chart(ctxB, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [{
              label: "Promedio",
              data: valores,
              backgroundColor: colores,
              borderColor: colores.map(c => c.replace("0.7", "1")),
              borderWidth: 1
            }]
          },
          options: baseOptions,
          plugins: basePlugins
        });
      }
    }

    // Línea
    if (activas.includes("linea")) {
      const ctxL = document.getElementById(CANVAS_IDS.linea);
      if (ctxL) {
        charts.linea = new Chart(ctxL, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: "Promedio",
              data: valores,
              borderColor: "rgba(75, 192, 192, 1)",
              backgroundColor: "rgba(75, 192, 192, 0.2)",
              tension: 0.4,
              fill: true,
              borderWidth: 2
            }]
          },
          options: baseOptions,
          plugins: basePlugins
        });
      }
    }

    // Pastel
    if (activas.includes("pastel")) {
      const ctxP = document.getElementById(CANVAS_IDS.pastel);
      if (ctxP) {
        charts.pastel = new Chart(ctxP, {
          type: "pie",
          data: {
            labels: labels,
            datasets: [{
              data: valores,
              backgroundColor: colores,
              borderColor: "#fff",
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { position: "right", labels: { usePointStyle: true, padding: 20 } },
              datalabels: { formatter: (v) => Number(v).toFixed(2), font: { weight: "bold" } }
            }
          },
          plugins: basePlugins
        });
      }
    }

    // Gauss
    if (activas.includes("gauss")) {
      const ctxG = document.getElementById(CANVAS_IDS.gauss);
      if (ctxG) {
        const gauss = function (data) {
          if (!data.length) return [];
          const mu = data.reduce((a, b) => a + b, 0) / data.length;
          const variance = data.reduce((a, b) => a + Math.pow(b - mu, 2), 0) / data.length || 1e-6;
          return data.map(x => Math.exp(-Math.pow(x - mu, 2) / (2 * variance)));
        };
        charts.gauss = new Chart(ctxG, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: "Distribución Gaussiana",
              data: gauss(valores),
              borderColor: "#FF9800",
              backgroundColor: "rgba(255, 152, 0, 0.2)",
              tension: 0.4,
              fill: true,
              borderWidth: 2
            }]
          },
          options: baseOptions
        });
      }
    }
  }

  function renderDesdeUI() {
    const activas = activasDesdeUI();
    renderGraficas(activas);
  }

  // Eventos del filtro de gráficas
  chkGraficas.forEach(cb => cb.addEventListener("change", renderDesdeUI));
  if (btnGrafAll) btnGrafAll.addEventListener("click", () => { chkGraficas.forEach(cb => cb.checked = true); renderDesdeUI(); });
  if (btnGrafNone) btnGrafNone.addEventListener("click", () => { chkGraficas.forEach(cb => cb.checked = false); renderDesdeUI(); });
  if (btnGrafApply) btnGrafApply.addEventListener("click", renderDesdeUI);

  // Render inicial
  renderDesdeUI();

  // --------- Descargar PDF: solo tabla + gráficas ----------
  document.getElementById("btnDescargarPDF")?.addEventListener("click", function () {
    const { jsPDF } = window.jspdf;

    // Activar modo exportación (oculta filtros y barra)
    document.body.classList.add("export-only");

    const area = document.querySelector(".page-content");
    html2canvas(area, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: "#ffffff"
    })
    .then(canvas => {
      // Quitar modo exportación (volver normal)
      document.body.classList.remove("export-only");

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();
      const imgW = pageW;
      const imgH = canvas.height * imgW / canvas.width;

      let position = 0;
      let heightLeft = imgH;

      pdf.addImage(imgData, "PNG", 0, position, imgW, imgH);
      heightLeft -= pageH;

      while (heightLeft > 0) {
        position -= pageH;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, imgW, imgH);
        heightLeft -= pageH;
      }

      pdf.save("Aprovechamiento.pdf");
    })
    .catch(err => {
      document.body.classList.remove("export-only");
      console.error("[PDF] Error:", err);
      alert("No se pudo generar el PDF. Revisa la consola.");
    });
  });
});
