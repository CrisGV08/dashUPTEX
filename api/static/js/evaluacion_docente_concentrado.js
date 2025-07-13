const coloresPorAnio = {
  '2020': '#FF6384',
  '2021': '#36A2EB',
  '2022': '#FFCE56',
  '2023': '#4BC0C0',
  '2024': '#9966FF',
  '2025': '#FF9F40',
  '2026': '#00C49F',
  '2027': '#FF8042',
  '2028': '#FF6666',
  '2029': '#bab0ac'
};

document.addEventListener('DOMContentLoaded', function () {
  if (!datosEvaluacion || datosEvaluacion.length === 0) return;

  const selectCiclos = document.getElementById('selectCiclos');
  const checkboxes = document.querySelectorAll('.grafica-check');
  const btnPDF = document.getElementById('btnDescargarPDF');
  const charts = {};

  const choices = new Choices(selectCiclos, {
    removeItemButton: true,
    placeholderValue: 'Selecciona ciclos...',
    searchEnabled: false
  });

  const ciclosUnicos = [...new Set(datosEvaluacion.map(d => d.ciclo))];
  choices.setChoices(
    ciclosUnicos.map(c => ({ value: c, label: c })),
    'value',
    'label',
    false
  );

  function graficarTodo(filtroCiclos) {
    const filtrados = datosEvaluacion.filter(d =>
      filtroCiclos.length === 0 || filtroCiclos.includes(d.ciclo)
    );

    const etiquetas = filtrados.map(d => d.ciclo);
    const promedios = filtrados.map(d => d.promedio);

    if (document.querySelector('input[value="lineal"]').checked) {
      if (!charts.lineal) charts.lineal = crearGrafica('graficaLineal', 'line');
      actualizarGrafica(charts.lineal, etiquetas, promedios, 'Promedio por Año (Línea)');
    } else if (charts.lineal) { charts.lineal.destroy(); charts.lineal = null; }

    if (document.querySelector('input[value="barras"]').checked) {
      if (!charts.barras) charts.barras = crearGrafica('graficaBarras', 'bar');
      actualizarGrafica(charts.barras, etiquetas, promedios, 'Promedio por Año (Barras)');
    } else if (charts.barras) { charts.barras.destroy(); charts.barras = null; }

    if (document.querySelector('input[value="pastel"]').checked) {
      if (!charts.pastel) charts.pastel = crearGrafica('graficaPastel', 'pie');
      actualizarGrafica(charts.pastel, etiquetas, promedios, 'Distribución de Promedios');
    } else if (charts.pastel) { charts.pastel.destroy(); charts.pastel = null; }

    if (document.querySelector('input[value="gauss"]').checked) {
      if (!charts.gauss) charts.gauss = crearGrafica('graficaGauss', 'line');
      const curva = generarCurvaGaussiana(promedios);
      actualizarGrafica(charts.gauss, curva.labels, curva.valores, 'Curva de Gauss');
    } else if (charts.gauss) { charts.gauss.destroy(); charts.gauss = null; }
  }

  function crearGrafica(id, tipo) {
    const ctx = document.getElementById(id).getContext('2d');
    return new Chart(ctx, {
      type: tipo,
      data: {
        labels: [],
        datasets: [{
          label: '',
          data: [],
          fill: false,
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
          tooltip: { enabled: true }
        }
      }
    });
  }

  function actualizarGrafica(chart, etiquetas, valores, etiqueta) {
    chart.data.labels = etiquetas;
    chart.data.datasets[0].data = valores;
    chart.data.datasets[0].label = etiqueta;

        const colores = etiquetas.map(e => {
        const anio = e.toString().substring(0, 4);  // extrae los 4 primeros caracteres
        return coloresPorAnio[anio] || '#cccccc';
        });

    if (chart.config.type === 'pie') {
      chart.data.datasets[0].backgroundColor = colores;
    } else if (chart.config.type === 'bar') {
      chart.data.datasets[0].backgroundColor = colores;
      chart.data.datasets[0].borderColor = colores;
      chart.data.datasets[0].borderWidth = 1;
    } else if (chart.config.type === 'line') {
    const color = '#36A2EB'; // o cualquier color personalizado para la curva de Gauss
    chart.data.datasets[0].borderColor = color;
    chart.data.datasets[0].backgroundColor = color;
    chart.data.datasets[0].pointBackgroundColor = color;
    chart.data.datasets[0].pointBorderColor = color;
}

    chart.update();
  }

  function generarCurvaGaussiana(datos) {
    if (datos.length < 2) return { labels: [], valores: [] };
    const media = datos.reduce((a, b) => a + b, 0) / datos.length;
    const varianza = datos.reduce((acc, x) => acc + Math.pow(x - media, 2), 0) / datos.length;
    const desviacion = Math.sqrt(varianza);
    const labels = [], valores = [];

    for (let x = media - 3 * desviacion; x <= media + 3 * desviacion; x += 0.1) {
      const y = (1 / (desviacion * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - media) / desviacion, 2));
      labels.push(x.toFixed(1));
      valores.push((y * 100).toFixed(2));
    }
    return { labels, valores };
  }

  selectCiclos.addEventListener('change', () => {
    graficarTodo(choices.getValue(true));
  });

  checkboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      graficarTodo(choices.getValue(true));
    });
  });

 btnPDF.addEventListener('click', () => {
  const contenedorTemporal = document.createElement('div');
  contenedorTemporal.style.padding = '40px';
  contenedorTemporal.style.fontFamily = 'Segoe UI, sans-serif';
  contenedorTemporal.style.color = '#333';
  contenedorTemporal.style.maxWidth = '800px';
  contenedorTemporal.style.margin = '0 auto';
  contenedorTemporal.style.textAlign = 'center';

  // Título
  const titulo = document.createElement('h1');
  titulo.textContent = '📘 Reporte de Evaluación Docente';
  titulo.style.fontSize = '22px';
  titulo.style.marginBottom = '10px';
  contenedorTemporal.appendChild(titulo);

  // Fecha
  const fecha = document.createElement('p');
  const hoy = new Date();
  fecha.textContent = `Generado el ${hoy.toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })}`;
  fecha.style.marginBottom = '30px';
  contenedorTemporal.appendChild(fecha);

  // Tabla
  const tablaOriginal = document.querySelector('.table-responsive table');
  if (tablaOriginal) {
    const tablaClon = tablaOriginal.cloneNode(true);
    tablaClon.style.margin = '0 auto 40px auto';
    tablaClon.style.width = '100%';
    tablaClon.style.borderCollapse = 'collapse';
    tablaClon.querySelectorAll('th, td').forEach(cell => {
      cell.style.padding = '8px';
      cell.style.border = '1px solid #ccc';
    });
    contenedorTemporal.appendChild(tablaClon);
  }

  // Gráficas
  const ids = ['graficaLineal', 'graficaBarras', 'graficaPastel', 'graficaGauss'];
  ids.forEach(id => {
    const canvas = document.getElementById(id);
    if (canvas && canvas.offsetParent !== null) {
      const imagen = new Image();
      imagen.src = canvas.toDataURL('image/png');
      imagen.style.display = 'block';
      imagen.style.margin = '20px auto';
      imagen.style.maxWidth = '100%';
      imagen.style.height = 'auto';

      const subtitulo = document.createElement('h4');
      subtitulo.textContent =
        id.includes('Lineal') ? '📈 Gráfica Línea' :
        id.includes('Barras') ? '📊 Gráfica Barras' :
        id.includes('Pastel') ? '🥧 Gráfica Pastel' :
        id.includes('Gauss') ? '📉 Curva Gaussiana' : '';
      subtitulo.style.marginTop = '20px';
      subtitulo.style.fontSize = '16px';

      contenedorTemporal.appendChild(subtitulo);
      contenedorTemporal.appendChild(imagen);
    }
  });

  // Descargar PDF
  document.body.appendChild(contenedorTemporal);

  html2pdf().from(contenedorTemporal).set({
    margin: 0,
    filename: 'Reporte_Evaluacion_Docente.pdf',
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { format: 'a4', orientation: 'portrait' }
  }).save().then(() => {
    document.body.removeChild(contenedorTemporal);
  });
});






  graficarTodo([]); // inicial
});
