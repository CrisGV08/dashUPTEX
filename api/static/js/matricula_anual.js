// static/js/matricula_anual.js
document.addEventListener("DOMContentLoaded", function () {
  const contenedor = document.getElementById("contenedorGraficas");
  if (!contenedor) return;

  // === Datos crudos por tipo (inyectados desde el template) ===
  // Estructura: { "YYYY-NombreCarrera": { "Enero - Abril": n, "Mayo - Agosto": n, "Septiembre - Diciembre": n } }
  const dataAntiguos = JSON.parse(contenedor.dataset.antiguos || "{}");
  const dataNuevos   = JSON.parse(contenedor.dataset.nuevos   || "{}");

  // === Controles ===
  const selectAnio          = document.getElementById("filtroAnio");
  const selectCuatrimestre  = document.getElementById("filtroCuatrimestre");
  const selectPrograma      = document.getElementById("filtroPrograma");   // "antiguo" | "nuevo" | "todos"
  const selectCarreras      = document.getElementById("filtroCarreras");

  // === Choices.js (mejora selects múltiples) ===
  // NOTA: No repoblamos carreras para no vaciar sus opciones originales (IDs/nombres)
  if (selectAnio && selectAnio.choices) { try { selectAnio.choices.destroy(); } catch(_){} }
  if (selectCarreras && selectCarreras.choices) { try { selectCarreras.choices.destroy(); } catch(_){} }

  const choicesAño = new Choices(selectAnio, {
    removeItemButton: true,
    placeholderValue: 'Selecciona uno o más años',
    searchEnabled: false,
    shouldSort: false
  });
  const choicesCarreras = new Choices(selectCarreras, {
    removeItemButton: true,
    placeholderValue: 'Selecciona una o más carreras',
    searchPlaceholderValue: 'Buscar...',
    shouldSort: true,
    shouldSortItems: true,
  });
  selectAnio.choices = choicesAño;
  selectCarreras.choices = choicesCarreras;

  // === Utilidades ===
  const getActiveData = () => {
    const tipo = selectPrograma.value;
    if (tipo === 'antiguo') return dataAntiguos;
    if (tipo === 'nuevo')   return dataNuevos;
    // "todos": unir ambos diccionarios
    return { ...dataAntiguos, ...dataNuevos };
  };

  const buildAniosFromData = (obj) => {
    const set = new Set(Object.keys(obj).map(k => k.split("-")[0]));
    return Array.from(set).sort((a,b) => (+a)-(+b));
  };

  // Limita años a los que existen en el dataset activo
  function repoblarAnios(keepSelection=false){
    const data = getActiveData();
    const anios = buildAniosFromData(data);
    const prev = keepSelection ? choicesAño.getValue(true) : [];
    choicesAño.clearStore();
    const opts = anios.map(a => ({ value: a, label: a, selected: keepSelection && prev.includes(a) }));
    choicesAño.setChoices(opts, 'value', 'label', true);
  }

  // Devuelve los **nombres** de carreras seleccionadas (no los IDs)
  function getCarreraNamesSeleccionadas(){
    return Array.from(selectCarreras.selectedOptions || []).map(opt => opt.textContent.trim());
  }

  // === Filtrado de datos para gráficas ===
  function filtrarDatos() {
    const data = getActiveData();

    const aniosSeleccionados = Array.from(selectAnio.selectedOptions || []).map(opt => opt.value);
    const cuatriSeleccionado = selectCuatrimestre.value; // "Todos" o nombre exacto
    const carrerasSeleccionadasNombres = getCarreraNamesSeleccionadas();

    const resultados = [];

    for (let key in data) {
      // key = "YYYY-NombreCarrera" (el nombre puede contener guiones)
      const [anio, ...nombreArr] = key.split("-");
      const nombre = nombreArr.join("-");
      const valores = data[key];

      const coincideAnio    = aniosSeleccionados.length === 0 || aniosSeleccionados.includes(anio);
      const coincideCarrera = carrerasSeleccionadasNombres.length === 0 || carrerasSeleccionadasNombres.includes(nombre);

      if (!coincideAnio || !coincideCarrera) continue;

      // Periodos
      let ea = valores["Enero - Abril"] || 0;
      let ma = valores["Mayo - Agosto"] || 0;
      let sd = valores["Septiembre - Diciembre"] || 0;

      // Si se selecciona solo un cuatrimestre, los otros van a 0
      if (cuatriSeleccionado !== 'Todos') {
        ea = (cuatriSeleccionado === 'Enero - Abril')          ? ea : 0;
        ma = (cuatriSeleccionado === 'Mayo - Agosto')          ? ma : 0;
        sd = (cuatriSeleccionado === 'Septiembre - Diciembre') ? sd : 0;
      }

      resultados.push({ nombre, año: anio, eneAbr: ea, mayAgo: ma, sepDic: sd });
    }

    return resultados;
  }

  // === Gráficas ===
  let chartBarras, chartLinea, chartPastel, chartGauss;

  function graficarBarras(labels, eneAbr, mayAgo, sepDic) {
    if (chartBarras) chartBarras.destroy();
    const ctx = document.getElementById("graficaBarras");
    chartBarras = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Enero - Abril', data: eneAbr },
          { label: 'Mayo - Agosto', data: mayAgo },
          { label: 'Septiembre - Diciembre', data: sepDic }
        ]
      },
      options: {
        plugins: {
          legend: { labels: { font: { size: 16 } } },
          tooltip: {
            bodyFont: { size: 16 },
            titleFont: { size: 16 }
          }
        },
        scales: {
          x: { ticks: { font: { size: 16 } } },
          y: { ticks: { font: { size: 16 } } }
        },
        responsive: true
      }
    });
  }

  function graficarLinea(labels, dataTotal) {
    if (chartLinea) chartLinea.destroy();
    const ctx = document.getElementById("graficaLinea");
    chartLinea = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{ label: 'Total por carrera', data: dataTotal, borderWidth: 2, fill: false }]
      },
      options: {
        plugins: {
          legend: { labels: { font: { size: 16 } } },
          tooltip: {
            bodyFont: { size: 16 },
            titleFont: { size: 16 }
          }
        },
        scales: {
          x: { ticks: { font: { size: 16 } } },
          y: { ticks: { font: { size: 16 } } }
        },
        responsive: true
      }
    });
  }

  function graficarPastel(labels, dataTotal) {
    if (chartPastel) chartPastel.destroy();
    const ctx = document.getElementById("graficaPastel");
    chartPastel = new Chart(ctx, {
      type: 'pie',
      data: {
        labels,
        datasets: [{ label: 'Distribución', data: dataTotal }]
      },
      options: {
        plugins: {
          legend: { labels: { font: { size: 16 } } },
          tooltip: {
            bodyFont: { size: 16 },
            titleFont: { size: 16 }
          }
        },
        responsive: true
      }
    });
  }

  // ==== Barras con nombres reales de carreras (para "Gauss") ====
  function graficarGauss(labels, dataTotal) {
    if (chartGauss) chartGauss.destroy();
    const ctx = document.getElementById("graficaGauss");
    chartGauss = new Chart(ctx, {
      type: 'bar',  // mantenemos barras
      data: {
        labels,     // nombres de las carreras
        datasets: [{ label: 'Frecuencia', data: dataTotal }]
      },
      options: {
        plugins: {
          legend: { labels: { font: { size: 16 } } },
          tooltip: {
            bodyFont: { size: 16 },
            titleFont: { size: 16 }
          }
        },
        scales: {
          x: {
            ticks: {
              font: { size: 16 },
              autoSkip: false,     // intenta no saltarse etiquetas
              maxRotation: 45,     // rota si son largas
              minRotation: 0
            }
          },
          y: { ticks: { font: { size: 16 } } }
        },
        responsive: true
      }
    });
  }

  function actualizarGraficas() {
    const filtrados = filtrarDatos();

    // Etiquetas “largas” con nombre + año para barras/linea/pastel
    const etiquetas = filtrados.map(f => `${f.nombre} (${f.año})`);
    // Solo nombre de la carrera para la “gauss”
    const etiquetasNombres = filtrados.map(f => f.nombre);

    const eneAbr = filtrados.map(f => f.eneAbr);
    const mayAgo = filtrados.map(f => f.mayAgo);
    const sepDic = filtrados.map(f => f.sepDic);
    const total  = filtrados.map(f => f.eneAbr + f.mayAgo + f.sepDic);

    // Vector simple de porcentajes para la “gauss”
    const sumTotal = total.reduce((a, b) => a + b, 0) || 1; // evitar división por 0
    const promedios = total.map(t => Math.round((t / sumTotal) * 100));

    graficarBarras(etiquetas, eneAbr, mayAgo, sepDic);
    graficarLinea(etiquetas, total);
    graficarPastel(etiquetas, total);
    graficarGauss(etiquetasNombres, promedios);  // nombres reales aquí
  }

  // === Inicialización ===
  repoblarAnios(/*keep*/ false);
  actualizarGraficas();

  // === Eventos (reactivo a filtros) ===
  selectPrograma.addEventListener('change', () => {
    repoblarAnios(/*keep*/ true);
    actualizarGraficas();
  });
  selectAnio.addEventListener('change', actualizarGraficas);
  selectCuatrimestre.addEventListener('change', actualizarGraficas);
  selectCarreras.addEventListener('change', actualizarGraficas);

  // === Exportar PDF (html2pdf) — oculta filtros y botones durante la exportación ===
  const btnPDF = document.getElementById("btnDescargarPDF");
  if (btnPDF) {
    btnPDF.addEventListener("click", async function () {
      const panel = document.querySelector(".admin-panel");
      if (!panel) return;

      // 1) Activar modo export (oculta .filtros, .btn-admin, .btn-pdf vía CSS)
      panel.classList.add("pdf-export");

      const opt = {
        margin:       [10, 10, 10, 10],
        filename:     "matricula_anual.pdf",
        image:        { type: "jpeg", quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true },
        jsPDF:        { unit: "mm", format: "a4", orientation: "portrait" }
      };

      try {
        await html2pdf().set(opt).from(panel).save();
      } finally {
        // 2) Volver a mostrar filtros/botones
        panel.classList.remove("pdf-export");
      }
    });
  }
});
