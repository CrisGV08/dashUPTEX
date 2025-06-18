document.addEventListener("DOMContentLoaded", () => {
    const etiquetas = JSON.parse(document.getElementById("labels-data").textContent);
    const totales = JSON.parse(document.getElementById("totales-data").textContent);
    const programas = JSON.parse(document.getElementById("programas-data").textContent);

    const ctxLinea = document.getElementById("grafico-linea");
    const ctxBarras = document.getElementById("grafico-barras");
    const ctxPastel = document.getElementById("grafico-pastel");
    const ctxGauss = document.getElementById("grafico-gauss");

    let charts = {
        linea: crearLinea(etiquetas, totales),
        barras: crearBarras(etiquetas, programas),
        pastel: crearPastel(etiquetas, programas),
        gauss: crearGauss(etiquetas, totales)
    };

    document.querySelectorAll(".grafico-check").forEach(chk => {
        chk.addEventListener("change", () => {
            const container = document.getElementById(`grafico-${chk.value}-container`);
            container.style.display = chk.checked ? "block" : "none";
        });
    });

    document.getElementById("filtro-ciclos").addEventListener("change", actualizarGraficas);
    document.getElementById("filtro-carreras").addEventListener("change", actualizarGraficas);

    function actualizarGraficas() {
        const ciclosSeleccionados = Array.from(document.getElementById("filtro-ciclos").selectedOptions).map(opt => opt.value);
        const carrerasSeleccionadas = Array.from(document.getElementById("filtro-carreras").selectedOptions).map(opt => opt.value);

        const indicesCiclos = etiquetas.map((et, idx) => ciclosSeleccionados.includes(et) ? idx : -1).filter(idx => idx !== -1);

        const nuevosTotales = indicesCiclos.map(i => totales[i]);
        const nuevasEtiquetas = indicesCiclos.map(i => etiquetas[i]);

        charts.linea.data.labels = nuevasEtiquetas;
        charts.linea.data.datasets[0].data = nuevosTotales;
        charts.linea.update();

        charts.gauss.data.labels = nuevasEtiquetas;
        charts.gauss.data.datasets[0].data = calcularGauss(nuevosTotales);
        charts.gauss.update();

        const nuevosProgramas = Object.fromEntries(
            Object.entries(programas)
                .filter(([nombre]) => carrerasSeleccionadas.includes(nombre))
                .map(([nombre, valores]) => [nombre, indicesCiclos.map(i => valores[i])])
        );

        const datasets = Object.entries(nuevosProgramas).map(([nombre, datos]) => ({
            label: nombre,
            data: datos,
            backgroundColor: randomColor(),
            borderColor: randomColor(),
            borderWidth: 1
        }));

        charts.barras.data.labels = nuevasEtiquetas;
        charts.barras.data.datasets = datasets;
        charts.barras.update();

        const primerCiclo = indicesCiclos[0] ?? 0;
        const pastelData = Object.entries(nuevosProgramas).map(([nombre, datos]) => ({
            label: nombre,
            value: datos[0] || 0
        }));

        charts.pastel.data.labels = pastelData.map(d => d.label);
        charts.pastel.data.datasets[0].data = pastelData.map(d => d.value);
        charts.pastel.data.datasets[0].backgroundColor = pastelData.map(() => randomColor());
        charts.pastel.update();
    }

    function crearLinea(labels, data) {
        return new Chart(ctxLinea, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Matrícula Total',
                    data,
                    borderColor: 'blue',
                    backgroundColor: 'rgba(0, 0, 255, 0.2)',
                    tension: 0.3
                }]
            },
            options: { responsive: true }
        });
    }

    function crearBarras(labels, data) {
        const datasets = Object.entries(data).map(([nombre, valores]) => ({
            label: nombre,
            data: valores,
            backgroundColor: randomColor(),
            borderColor: randomColor(),
            borderWidth: 1
        }));

        return new Chart(ctxBarras, {
            type: 'bar',
            data: { labels, datasets },
            options: { responsive: true }
        });
    }

    function crearPastel(labels, data) {
        const primerCiclo = Object.entries(data).map(([nombre, valores]) => ({
            label: nombre,
            value: valores[0] || 0
        }));

        return new Chart(ctxPastel, {
            type: 'pie',
            data: {
                labels: primerCiclo.map(d => d.label),
                datasets: [{
                    data: primerCiclo.map(d => d.value),
                    backgroundColor: primerCiclo.map(() => randomColor())
                }]
            },
            options: { responsive: true }
        });
    }

    function crearGauss(labels, data) {
        return new Chart(ctxGauss, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Campana de Gauss',
                    data: calcularGauss(data),
                    borderColor: 'purple',
                    backgroundColor: 'rgba(123, 0, 255, 0.2)',
                    tension: 0.4
                }]
            },
            options: { responsive: true }
        });
    }

    function calcularGauss(datos) {
        const prom = datos.reduce((a, b) => a + b, 0) / datos.length;
        const sigma = Math.sqrt(datos.reduce((a, b) => a + Math.pow(b - prom, 2), 0) / datos.length);
        return datos.map(x => Math.exp(-Math.pow(x - prom, 2) / (2 * sigma * sigma)));
    }

    function randomColor() {
        const h = Math.floor(Math.random() * 360);
        return `hsl(${h}, 70%, 60%)`;
    }
});


document.addEventListener("DOMContentLoaded", () => {
    const ciclos = document.querySelectorAll(".ciclo-pill");
    const carreras = document.querySelectorAll(".carrera-pill");

    ciclos.forEach(pill => {
        pill.addEventListener("click", () => {
            pill.classList.toggle("selected");
            actualizarGraficas();
        });
    });

    carreras.forEach(pill => {
        pill.addEventListener("click", () => {
            pill.classList.toggle("selected");
            actualizarGraficas();
        });
    });

    function actualizarGraficas() {
        const ciclosSeleccionados = [...document.querySelectorAll(".ciclo-pill.selected")].map(p => p.dataset.id);
        const carrerasSeleccionadas = [...document.querySelectorAll(".carrera-pill.selected")].map(p => p.dataset.nombre);
        
        console.log("🎯 Ciclos seleccionados:", ciclosSeleccionados);
        console.log("🎯 Carreras seleccionadas:", carrerasSeleccionadas);
        
        // TODO: Aquí deberás actualizar las gráficas con esos filtros usando Chart.js
        // Puedes cruzarlo con tus datos para solo mostrar los seleccionados.
    }
});
