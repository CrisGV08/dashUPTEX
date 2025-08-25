document.addEventListener("DOMContentLoaded", function () {
  const contenedor = document.getElementById("contenedorGraficas");

  // === Datos crudos por tipo ===
  const dataAntiguos = JSON.parse(contenedor.dataset.antiguos || "{}"); // { "2023-Lic ...": {periodos} }
  const dataNuevos   = JSON.parse(contenedor.dataset.nuevos   || "{}");

  // Catálogos de nombres de carreras (desde el template)
  const carrerasAnt  = JSON.parse(contenedor.dataset.carrerasAntiguos || "[]"); // ["Lic ...", ...]
  const carrerasNvo  = JSON.parse(contenedor.dataset.carrerasNuevos  || "[]");

  // === Controles ===
  const selectAnio          = document.getElementById("filtroAnio");
  const selectCuatrimestre  = document.getElementById("filtroCuatrimestre");
  const selectPrograma      = document.getElementById("filtroPrograma");   // "antiguo" | "nuevo" | "todos"
  const selectCarreras      = document.getElementById("filtroCarreras");

  // === Choices.js ===
  if (selectAnio.choices) { try { selectAnio.choices.destroy(); } catch(_){} }
  if (selectCarreras.choices) { try { selectCarreras.choices.destroy(); } catch(_){} }

  const choicesAño = new Choices(selectAnio, {
    removeItemButton: true,
    placeholderValue: 'Selecciona uno o más años',
    searchEnabled: false
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
    return { ...dataAntiguos, ...dataNuevos }; // todos
  };

  const buildAniosFromData = (obj) => {
    const set = new Set(Object.keys(obj).map(k => k.split("-")[0]));
    return Array.from(set).sort((a,b) => (+a)-(+b));
  };

  const buildCarrerasFromTipo = (tipo) => {
    if (tipo === 'antiguo') return [...carrerasAnt].sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'}));
    if (tipo === 'nuevo')   return [...carrerasNvo].sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'}));
    // todos: union única
    return Array.from(new Set([...carrerasAnt, ...carrerasNvo]))
      .sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'}));
  };

  function repoblarAnios(tipo, keepSelection=false){
    const data = getActiveData();
    const anios = buildAniosFromData(data);
    const prev = keepSelection ? choicesAño.getValue(true) : [];
    choicesAño.clearStore();
    const opts = anios.map(a => ({ value: a, label: a, selected: keepSelection && prev.includes(a) }));
    choicesAño.setChoices(opts, 'value', 'label', true);
  }

  function repoblarCarreras(tipo, keepSelection=false){
    const fuente = buildCarrerasFromTipo(tipo);
    const prev = keepSelection ? choicesCarreras.getValue(true) : [];
    choicesCarreras.clearStore();
    const opts = fuente.map(c => ({ value: c, label: c, selected: keepSelection && prev.includes(c) }));
    choicesCarreras.setChoices(opts, 'value', 'label', true);
  }

  // === Filtrado de datos para gráficas ===
  function filtrarDatos() {
    const tipoPrograma = selectPrograma.value;
    const data = getActiveData(); // ya respeta el tipo

    const aniosSeleccionados = Array.from(selectAnio.selectedOptions).map(opt => opt.value);
    const cuatriSeleccionado = selectCuatrimestre.value; // "Todos" o nombre exacto
    const carrerasSeleccionadas = Array.from(selectCarreras.selectedOptions).map(opt => opt.value);

    const resultados = [];

    for (let key in data) {
      const [anio, ...nombreArr] = key.split("-");
      const nombre = nombreArr.join("-");
      const valores = data[key];

      const coincideAnio    = aniosSeleccionados.length === 0 || aniosSeleccionados.includes(anio);
      const coincideCarrera = carrerasSeleccionadas.length === 0 || carrerasSeleccionadas.includes(nombre);

      if (!coincideAnio || !coincideCarrera) continue;

      // Cuatrimestre (si no es "Todos", zero-out el resto)
      let ea = valores["Enero - Abril"] || 0;
      let ma = valores["Mayo - Agosto"] || 0;
      let sd = valores["Septiembre - Diciembre"] || 0;

      if (cuatriSeleccionado !== 'Todos') {
        ea = (cuatriSeleccionado === 'Enero - Abril')         ? ea : 0;
        ma = (cuatriSeleccionado === 'Mayo - Agosto')         ? ma : 0;
        sd = (cuatriSeleccionado === 'Septiembre - Diciembre')? sd : 0;
      }

      resultados.push({ nombre, año: anio, eneAbr: ea, mayAgo: ma, sepDic: sd });
    }

    return resultados;
  }

  // === Gráficas (tus funciones, intactas) ===
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
        plugins: { legend: { position: 'top' }, tooltip: { enabled: true } },
        responsive: true
      }
    });
  }

  function graficarLinea(labels, dataTotal) {
    if (chartLinea) chartLinea.destroy();
    const ctx = document.getElementById("graficaLinea");
    chartLinea = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ label: 'Total por carrera', data: dataTotal, borderColor: '#9575cd', borderWidth: 2, fill: false }] },
      options: { responsive: true }
    });
  }

  function graficarPastel(labels, dataTotal) {
    if (chartPastel) chartPastel.destroy();
    const ctx = document.getElementById("graficaPastel");
    chartPastel = new Chart(ctx, {
      type: 'pie',
      data: {
        labels,
        datasets: [{ label: 'Distribución', data: dataTotal, backgroundColor: labels.map(() => `hsl(${Math.random() * 360}, 60%, 70%)`) }]
      },
      options: { responsive: true }
    });
  }

  function graficarGauss(dataTotal) {
    if (chartGauss) chartGauss.destroy();
    const ctx = document.getElementById("graficaGauss");
    chartGauss = new Chart(ctx, {
      type: 'bar',
      data: { labels: dataTotal.map((_, i) => `Carrera ${i + 1}`), datasets: [{ label: 'Frecuencia', data: dataTotal, backgroundColor: '#fdd835' }] },
      options: { responsive: true }
    });
  }

  function actualizarGraficas() {
    const filtrados = filtrarDatos();
    const etiquetas = filtrados.map(f => `${f.nombre} (${f.año})`);
    const eneAbr = filtrados.map(f => f.eneAbr);
    const mayAgo = filtrados.map(f => f.mayAgo);
    const sepDic = filtrados.map(f => f.sepDic);
    const total  = filtrados.map(f => f.eneAbr + f.mayAgo + f.sepDic);

    const sumTotal = total.reduce((a, b) => a + b, 0) || 1; // evitar división por 0
    const promedios = total.map(t => Math.round((t / sumTotal) * 100));

    graficarBarras(etiquetas, eneAbr, mayAgo, sepDic);
    graficarLinea(etiquetas, total);
    graficarPastel(etiquetas, total);
    graficarGauss(promedios);
  }

  // === Inicialización ===
  repoblarAnios(selectPrograma.value, /*keep*/ false);
  repoblarCarreras(selectPrograma.value, /*keep*/ false);
  actualizarGraficas();

  // === Eventos ===
  selectPrograma.addEventListener('change', () => {
    repoblarAnios(selectPrograma.value, /*keep*/ false);
    repoblarCarreras(selectPrograma.value, /*keep*/ false);
    actualizarGraficas();
  });
  selectAnio.addEventListener('change', actualizarGraficas);
  selectCuatrimestre.addEventListener('change', actualizarGraficas);
  selectCarreras.addEventListener('change', actualizarGraficas);

  // PDF
  document.getElementById("btnDescargarPDF").addEventListener("click", function () {
    html2pdf().from(document.querySelector(".admin-panel")).save("matricula_anual.pdf");
  });
});
