// static/js/tasa_de_titulacion.js
document.addEventListener("DOMContentLoaded", () => {
  // === Datos desde el template ===
  const datos = JSON.parse(document.getElementById("jsonDatos").textContent || "[]");

  // === Elementos UI ===
  const filtroAnio = document.getElementById("filtro_anio");
  const filtroPrograma = document.getElementById("filtro_programa");
  const filtroGrafica = document.getElementById("filtro_grafica");
  const btnAplicar = document.getElementById("aplicarFiltros");
  const btnReset = document.getElementById("resetFiltros");
  const btnPDF = document.getElementById("btnDescargarPDF");
  const contDescargable = document.getElementById("seccionDescargable");
  const panelFiltros = document.querySelector(".filtros");

  // === Canvas ===
  const ctxLinea = document.getElementById("graficaLinea").getContext("2d");
  const ctxBarras = document.getElementById("graficaBarras").getContext("2d");
  const ctxPastel = document.getElementById("graficaPastel").getContext("2d");
  const ctxGauss = document.getElementById("graficaGauss").getContext("2d");

  // === Gráficas (Chart.js instances) ===
  let chartLinea, chartBarras, chartPastel, chartGauss;

  // === Helpers ===
  const uniq = (arr) => [...new Set(arr)];
  const fmtPct = (v) => `${(Number(v) || 0).toFixed(2)}%`;
  const fmtNum = (v) => new Intl.NumberFormat().format(Number(v) || 0);

  // Normal PDF options
  const pdfOpts = {
    margin: [10, 10, 10, 10],
    filename: "tasa_titulacion.pdf",
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
  };

  // === Inicializar Choices.js ===
  let chAnio, chPrograma, chGrafica;
  function initChoices() {
    const common = { removeItemButton: true, searchPlaceholderValue: "Buscar…" };
    chAnio = new Choices(filtroAnio, { ...common, shouldSort: true });
    chPrograma = new Choices(filtroPrograma, { ...common, shouldSort: true });
    chGrafica = new Choices(filtroGrafica, { ...common, shouldSort: false });
  }

  // === Cargar opciones (todas seleccionadas por defecto) ===
  function poblarFiltros() {
    const anios = uniq(datos.map(d => d.anio_ingreso)).sort((a, b) => a - b);
    const programas = uniq(datos.map(d => d.programa)).sort((a, b) => a.localeCompare(b));

    // Limpiar selects nativos antes de Choices
    [filtroAnio, filtroPrograma].forEach(sel => { sel.innerHTML = ""; });

    anios.forEach(anio => {
      const opt = new Option(String(anio), String(anio), true, true);
      filtroAnio.add(opt);
    });

    programas.forEach(p => {
      const opt = new Option(p, p, true, true);
      filtroPrograma.add(opt);
    });

    // Todas las gráficas seleccionadas
    Array.from(filtroGrafica.options).forEach(opt => (opt.selected = true));
  }

  function getSeleccion(selectEl, instance) {
    // Si hay Choices, usarlo; si no, leer del select
    if (instance) return instance.getValue(true);
    return Array.from(selectEl.selectedOptions).map(o => o.value);
  }

  function filtrarDatos() {
    const aniosSel = getSeleccion(filtroAnio, chAnio).map(String);
    const progsSel = getSeleccion(filtroPrograma, chPrograma);
    return datos
      .filter(d => aniosSel.includes(String(d.anio_ingreso)) && progsSel.includes(d.programa))
      .sort((a, b) => a.anio_ingreso - b.anio_ingreso || a.programa.localeCompare(b.programa));
  }

  function destroyCharts() {
    [chartLinea, chartBarras, chartPastel, chartGauss].forEach(ch => ch && ch.destroy());
    chartLinea = chartBarras = chartPastel = chartGauss = null;
  }

  function toggleAllChartsVisibility(hide = true) {
    document.querySelectorAll(".grafica").forEach(div => (div.style.display = hide ? "none" : "block"));
  }

  // === Campana de Gauss: curva teórica con media y desviación de las tasas ===
  function generarCurvaGauss(valores) {
    if (!valores.length) return { x: [], y: [] };
    const xs = valores.map(v => Number(v) || 0);
    const n = xs.length;
    const mean = xs.reduce((a, b) => a + b, 0) / n;
    const variance = xs.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / Math.max(1, (n - 1));
    const std = Math.sqrt(variance) || 1;

    // Dominio +- 3 sigma
    const minX = Math.max(0, mean - 3 * std);
    const maxX = Math.min(100, mean + 3 * std);
    const steps = 60;
    const X = Array.from({ length: steps }, (_, i) => minX + (i * (maxX - minX)) / (steps - 1));
    const Y = X.map(x => (1 / (std * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - mean) / std, 2)));

    // Escala Y a % para que “quepa” mejor
    const maxY = Math.max(...Y) || 1;
    const Yp = Y.map(y => (y / maxY) * 100);
    return { x: X, y: Yp };
  }

  // === Crear gráficas según selección ===
  function renderGraficas() {
    const filtrados = filtrarDatos();
    const visibles = getSeleccion(filtroGrafica, chGrafica);

    destroyCharts();
    toggleAllChartsVisibility(true);
    if (!filtrados.length) return;

    const etiquetas = filtrados.map(d => `${d.programa} (${d.anio_ingreso})`);
    const tasas = filtrados.map(d => Number(d.tasa_titulacion) || 0);
    const eficiencia = filtrados.map(d => Number(d.eficiencia_terminal) || 0);
    const titulados = filtrados.map(d => Number(d.titulados) || 0);

    const commonOpts = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v = ctx.parsed.y ?? ctx.parsed ?? 0;
              const label = ctx.dataset?.label || "";
              return /%/.test(label) ? `${label}: ${fmtPct(v)}` : `${label}: ${fmtNum(v)}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (v) => v % 1 === 0 ? v : v, // entero si aplica
          }
        }
      }
    };

    const datalabelsAvailable = !!window.ChartDataLabels;
    if (datalabelsAvailable) {
      Chart.register(window.ChartDataLabels);
      commonOpts.plugins.datalabels = {
        anchor: "end",
        align: "top",
        formatter: (v, ctx) => {
          const lbl = ctx.dataset?.label || "";
          return /%/.test(lbl) ? fmtPct(v) : fmtNum(v);
        },
        clamp: true,
        clip: false
      };
    }

    // --- Línea: Tasa de Titulación (%) ---
    if (visibles.includes("linea")) {
      document.getElementById("graficaLinea").parentElement.style.display = "block";
      chartLinea = new Chart(ctxLinea, {
        type: "line",
        data: {
          labels: etiquetas,
          datasets: [{
            label: "Tasa de Titulación (%)",
            data: tasas,
            borderWidth: 2,
            fill: false,
            tension: 0.3
          }]
        },
        options: {
          ...commonOpts,
          scales: {
            ...commonOpts.scales,
            y: { ...commonOpts.scales.y, max: 100, ticks: { callback: (v) => `${v}%` } }
          }
        }
      });
    }

    // --- Barras: Eficiencia Terminal (%) vs Tasa (%) ---
    if (visibles.includes("barras")) {
      document.getElementById("graficaBarras").parentElement.style.display = "block";
      chartBarras = new Chart(ctxBarras, {
        type: "bar",
        data: {
          labels: etiquetas,
          datasets: [
            { label: "Eficiencia Terminal (%)", data: eficiencia, borderWidth: 1 },
            { label: "Tasa de Titulación (%)", data: tasas, borderWidth: 1 }
          ]
        },
        options: {
          ...commonOpts,
          scales: {
            ...commonOpts.scales,
            y: { ...commonOpts.scales.y, max: 100, ticks: { callback: (v) => `${v}%` } }
          }
        }
      });
    }

    // --- Pastel: Participación por Titulados ---
    if (visibles.includes("pastel")) {
      document.getElementById("graficaPastel").parentElement.style.display = "block";
      chartPastel = new Chart(ctxPastel, {
        type: "pie",
        data: {
          labels: etiquetas,
          datasets: [{ label: "Titulados", data: titulados }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "right" },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const total = ctx.dataset.data.reduce((a, b) => a + (Number(b) || 0), 0) || 1;
                  const val = Number(ctx.parsed) || 0;
                  const pct = (val / total) * 100;
                  return `${ctx.label}: ${fmtNum(val)} (${fmtPct(pct)})`;
                }
              }
            },
            ...(datalabelsAvailable && {
              datalabels: {
                formatter: (v, ctx) => {
                  const total = ctx.dataset.data.reduce((a, b) => a + (Number(b) || 0), 0) || 1;
                  const pct = (Number(v) / total) * 100;
                  return fmtPct(pct);
                }
              }
            })
          }
        }
      });
    }

    // --- Gauss: Curva normal teórica de tasas (%) ---
    if (visibles.includes("gauss")) {
      document.getElementById("graficaGauss").parentElement.style.display = "block";
      const { x, y } = generarCurvaGauss(tasas);
      chartGauss = new Chart(ctxGauss, {
        type: "line",
        data: {
          labels: x.map(v => v.toFixed(1)), // eje X en %
          datasets: [{
            label: "Campana de Gauss (tasas %)",
            data: y,
            fill: false,
            borderWidth: 2,
            tension: 0.25
          }]
        },
        options: {
          ...commonOpts,
          scales: {
            x: { title: { display: true, text: "Tasa (%)" } },
            y: { title: { display: true, text: "Densidad (esc.)" } }
          },
          plugins: {
            ...commonOpts.plugins,
            tooltip: {
              callbacks: {
                label: (ctx) => `y: ${ctx.parsed.y.toFixed(1)} (x: ${ctx.label}%)`
              }
            },
            datalabels: datalabelsAvailable ? { display: false } : undefined
          }
        }
      });
    }
  }

  // === Exportación a PDF (tabla + gráficas) ===
  async function descargarPDF() {
    try {
      // Oculta filtros para PDF y fuerza un reflow
      const prev = panelFiltros.style.display;
      panelFiltros.style.display = "none";
      await new Promise(r => setTimeout(r, 50));

      await html2pdf().set(pdfOpts).from(contDescargable).save();
      // Restaurar
      panelFiltros.style.display = prev || "";
    } catch (e) {
      console.error(e);
      alert("No se pudo generar el PDF.");
      panelFiltros.style.display = "";
    }
  }

  // === Eventos ===
  btnAplicar?.addEventListener("click", renderGraficas);
  btnReset?.addEventListener("click", () => {
    // Reseleccionar todo
    chAnio?.setChoiceByValue(uniq(datos.map(d => String(d.anio_ingreso))));
    chPrograma?.setChoiceByValue(uniq(datos.map(d => d.programa)));
    chGrafica?.setChoiceByValue(["linea", "barras", "pastel", "gauss"]);
    renderGraficas();
  });
  btnPDF?.addEventListener("click", descargarPDF);

  // === Init ===
  poblarFiltros();
  initChoices();
  renderGraficas();
});
