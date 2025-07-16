document.addEventListener("DOMContentLoaded", function () {
  const datos = JSON.parse(document.getElementById("contenedorGraficas").dataset.graficaJson || "{}");

  if (!datos.labels || !datos.valores || datos.labels.length === 0) {
    console.warn("No hay datos para graficar.");
    return;
  }

  const labels = datos.labels;
  const valores = datos.valores;

  // === BARRAS ===
  new Chart(document.getElementById("graficaBarras"), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Matrícula por Periodo',
        data: valores,
        backgroundColor: 'rgba(54, 162, 235, 0.6)'
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  // === LÍNEA ===
  new Chart(document.getElementById("graficaLinea"), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Tendencia de Matrícula',
        data: valores,
        fill: true,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  // === PASTEL ===
  new Chart(document.getElementById("graficaPastel"), {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        label: 'Distribución',
        data: valores,
        backgroundColor: labels.map((_, i) =>
          `hsl(${i * 360 / labels.length}, 70%, 70%)`
        )
      }]
    },
    options: {
      responsive: true
    }
  });

  // === GAUSSIANA ===
  const media = valores.reduce((a, b) => a + b, 0) / valores.length;
  const desviacion = Math.sqrt(valores.map(v => Math.pow(v - media, 2)).reduce((a, b) => a + b) / valores.length);

  const gaussData = labels.map((_, i) => {
    const x = i;
    return Math.exp(-Math.pow(x - (labels.length / 2), 2) / (2 * Math.pow(desviacion, 2))) * 100;
  });

  new Chart(document.getElementById("graficaGauss"), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Curva Gaussiana (Simulada)',
        data: gaussData,
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true
    }
  });

  // === EXPORTAR PDF ===
  const btnPDF = document.getElementById("btnDescargarPDF");
  if (btnPDF) {
    btnPDF.addEventListener("click", () => {
      const elemento = document.querySelector(".admin-panel");
      const opt = {
        margin: 0,
        filename: "matricula_cuatrimestre.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
      };
      html2pdf().set(opt).from(elemento).save();
    });
  }
});
