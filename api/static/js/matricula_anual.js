document.addEventListener("DOMContentLoaded", function () {
  const contenedor = document.getElementById("contenedorGraficas");

  const dataAntiguos = JSON.parse(contenedor.dataset.antiguos || "{}");
  const dataNuevos = JSON.parse(contenedor.dataset.nuevos || "{}");
  const data = { ...dataAntiguos, ...dataNuevos };

  // Filtro de Año
  const selectAnio = document.getElementById("filtroAnio");
  const selectCuatrimestre = document.getElementById("filtroCuatrimestre");
  const selectPrograma = document.getElementById("filtroPrograma");
  const selectCarreras = document.getElementById("filtroCarreras");

  const añosUnicos = [...new Set(Object.keys(data).map(k => k.split("-")[0]))];
  const carrerasUnicas = [...new Set(Object.keys(data).map(k => k.split("-").slice(1).join("-")))];

  const choicesAño = new Choices(selectAnio, {
    removeItemButton: true,
    placeholderValue: 'Selecciona uno o más años'
  });

  const choicesCarreras = new Choices(selectCarreras, {
    removeItemButton: true,
    placeholderValue: 'Selecciona una o más carreras'
  });

  choicesAño.setChoices(añosUnicos.map(a => ({ value: a, label: a })), 'value', 'label', false);
  choicesCarreras.setChoices(carrerasUnicas.map(c => ({ value: c, label: c })), 'value', 'label', false);

  // Función para filtrar datos
  function filtrarDatos() {
    const añosSeleccionados = Array.from(selectAnio.selectedOptions).map(opt => opt.value);
    const cuatriSeleccionado = selectCuatrimestre.value;
    const tipoPrograma = selectPrograma.value;
    const carrerasSeleccionadas = Array.from(selectCarreras.selectedOptions).map(opt => opt.value);

    const resultados = [];

    for (let key in data) {
      const [año, ...nombreArr] = key.split("-");
      const nombre = nombreArr.join("-");
      const valores = data[key];

      const coincideAño = añosSeleccionados.length === 0 || añosSeleccionados.includes(año);
      const coincideCarrera = carrerasSeleccionadas.length === 0 || carrerasSeleccionadas.includes(nombre);

      if (coincideAño && coincideCarrera) {
        resultados.push({
          nombre,
          año,
          eneAbr: valores["Enero - Abril"] || 0,
          mayAgo: valores["Mayo - Agosto"] || 0,
          sepDic: valores["Septiembre - Diciembre"] || 0
        });
      }
    }

    return resultados;
  }

  // Función para graficar
  function actualizarGraficas() {
    const filtrados = filtrarDatos();
    const etiquetas = filtrados.map(f => `${f.nombre} (${f.año})`);
    const eneAbr = filtrados.map(f => f.eneAbr);
    const mayAgo = filtrados.map(f => f.mayAgo);
    const sepDic = filtrados.map(f => f.sepDic);
    const total = filtrados.map(f => f.eneAbr + f.mayAgo + f.sepDic);

    const sumTotal = total.reduce((a, b) => a + b, 0);
    const promedios = total.map(t => Math.round((t / sumTotal) * 100));

    // ======= GRÁFICAS =======
    graficarBarras(etiquetas, eneAbr, mayAgo, sepDic);
    graficarLinea(etiquetas, total);
    graficarPastel(etiquetas, total);
    graficarGauss(promedios);
  }

  // Inicializar gráficos
  let chartBarras, chartLinea, chartPastel, chartGauss;

  function graficarBarras(labels, eneAbr, mayAgo, sepDic) {
    if (chartBarras) chartBarras.destroy();
    const ctx = document.getElementById("graficaBarras");
    chartBarras = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Enero - Abril', data: eneAbr, backgroundColor: '#ef9a9a' },
          { label: 'Mayo - Agosto', data: mayAgo, backgroundColor: '#80cbc4' },
          { label: 'Septiembre - Diciembre', data: sepDic, backgroundColor: '#90caf9' }
        ]
      },
      options: {
        plugins: {
          legend: { position: 'top' },
          tooltip: { enabled: true }
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
        datasets: [{
          label: 'Total por carrera',
          data: dataTotal,
          borderColor: '#9575cd',
          borderWidth: 2,
          fill: false
        }]
      },
      options: {
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
        datasets: [{
          label: 'Distribución',
          data: dataTotal,
          backgroundColor: labels.map(() => `hsl(${Math.random() * 360}, 60%, 70%)`)
        }]
      },
      options: {
        responsive: true
      }
    });
  }

  function graficarGauss(dataTotal) {
    if (chartGauss) chartGauss.destroy();
    const ctx = document.getElementById("graficaGauss");
    chartGauss = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: dataTotal.map((_, i) => `Carrera ${i + 1}`),
        datasets: [{
          label: 'Frecuencia',
          data: dataTotal,
          backgroundColor: '#fdd835'
        }]
      },
      options: {
        responsive: true
      }
    });
  }

  // Primer render
  actualizarGraficas();

  // Re-render al cambiar filtros
  selectAnio.addEventListener('change', actualizarGraficas);
  selectCuatrimestre.addEventListener('change', actualizarGraficas);
  selectPrograma.addEventListener('change', actualizarGraficas);
  selectCarreras.addEventListener('change', actualizarGraficas);

  // Botón de PDF
  document.getElementById("btnDescargarPDF").addEventListener("click", function () {
    html2pdf().from(document.querySelector(".admin-panel")).save("matricula_anual.pdf");
  });
});
