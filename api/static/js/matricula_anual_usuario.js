document.addEventListener("DOMContentLoaded", function () {
  const cont = document.getElementById("contenedorGraficas");
  if (!cont) return;

  // Datos por tipo (claves "ANIO-NOMBRE")
  const dataAnt = JSON.parse(cont.dataset.antiguos || "{}");
  const dataNvo = JSON.parse(cont.dataset.nuevos   || "{}");

  // Catálogos de carreras por tipo (listas de nombres)
  const carrerasAnt = JSON.parse(cont.dataset.carrerasAntiguos || "[]");
  const carrerasNvo = JSON.parse(cont.dataset.carrerasNuevos  || "[]");

  // Controles
  const selAnio = document.getElementById("filtroAnio");
  const selCuat = document.getElementById("filtroCuatrimestre");
  const selTipo = document.getElementById("filtroPrograma");     // "antiguo" | "nuevo"
  const selCarr = document.getElementById("filtroCarreras");     // multiple

  // Inicializa Choices.js (limpiando si ya había instancias)
  try { selAnio.choices?.destroy(); } catch(_){}
  try { selCarr.choices?.destroy(); } catch(_){}

  const chAnio = new Choices(selAnio, {
    removeItemButton: true,
    placeholderValue: 'Selecciona uno o más años',
    searchEnabled: false,
    shouldSort: false
  });
  const chCarr = new Choices(selCarr, {
    removeItemButton: true,
    placeholderValue: 'Selecciona una o más carreras',
    searchPlaceholderValue: 'Buscar...',
    shouldSort: true,
    shouldSortItems: true
  });
  selAnio.choices = chAnio;
  selCarr.choices = chCarr;

  // Helpers para obtener dataset activo y catálogos
  const getActiveData = () => (selTipo.value === 'antiguo') ? dataAnt : dataNvo;
  const getActiveCarr = () => (selTipo.value === 'antiguo') ? carrerasAnt : carrerasNvo;

  function repoblarAnios(keepSelection=false){
    const data = getActiveData();
    const anios = Array.from(new Set(Object.keys(data).map(k => k.split("-")[0])))
                       .sort((a,b)=>(+a)-(+b));
    const prev = keepSelection ? chAnio.getValue(true) : [];
    chAnio.clearStore();
    chAnio.setChoices(
      anios.map(a => ({ value:a, label:a, selected: keepSelection && prev.includes(a) })),
      'value','label', true
    );
  }

  function repoblarCarreras(keepSelection=false){
    const fuente = getActiveCarr().slice()
      .sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'}));
    const prev = keepSelection ? chCarr.getValue(true) : [];
    chCarr.clearStore();
    chCarr.setChoices(
      fuente.map(c => ({ value:c, label:c, selected: keepSelection && prev.includes(c) })),
      'value','label', true
    );
  }

  // Filtrar datos (por Año(s), Cuatrimestre y Carreras)
  function filtrarDatos(){
    const data = getActiveData();
    const aniosSel = Array.from(selAnio.selectedOptions).map(o=>o.value);
    const cuatSel  = selCuat.value; // "Todos" | "Enero - Abril" | ...
    const carrSel  = Array.from(selCarr.selectedOptions).map(o=>o.value);

    const out = [];
    for (const key in data){
      const [anio, ...rest] = key.split("-");
      const nombre = rest.join("-");
      const valores = data[key];

      const okAnio = aniosSel.length===0 || aniosSel.includes(anio);
      const okCarr = carrSel.length===0 || carrSel.includes(nombre);
      if (!okAnio || !okCarr) continue;

      let ea = valores["Enero - Abril"] || 0;
      let ma = valores["Mayo - Agosto"] || 0;
      let sd = valores["Septiembre - Diciembre"] || 0;

      if (cuatSel !== "Todos"){
        ea = (cuatSel==="Enero - Abril") ? ea : 0;
        ma = (cuatSel==="Mayo - Agosto") ? ma : 0;
        sd = (cuatSel==="Septiembre - Diciembre") ? sd : 0;
      }
      out.push({ nombre, anio, ea, ma, sd });
    }
    return out;
  }

  // ========= Gráficas (ahora con fuentes más grandes) =========
  let chartBarras, chartLinea, chartPastel, chartGauss;

  function graficarBarras(labels, ea, ma, sd){
    chartBarras?.destroy();
    chartBarras = new Chart(document.getElementById("graficaBarras"), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label:'Enero - Abril', data: ea, backgroundColor: '#ef9a9a' },
          { label:'Mayo - Agosto', data: ma, backgroundColor: '#80cbc4' },
          { label:'Septiembre - Diciembre', data: sd, backgroundColor: '#90caf9' }
        ]
      },
      options: {
        responsive:true,
        plugins:{
          legend:{ position:'top', labels:{ font:{ size:30 } } },
          tooltip:{ bodyFont:{ size:16 }, titleFont:{ size:30 } }
        },
        scales:{
          x:{ ticks:{ font:{ size:30 } } },
          y:{ ticks:{ font:{ size:30 } } }
        }
      }
    });
  }

  function graficarLinea(labels, total){
    chartLinea?.destroy();
    chartLinea = new Chart(document.getElementById("graficaLinea"), {
      type: 'line',
      data: {
        labels,
        datasets: [{ label:'Total por carrera', data: total, borderColor:'#9575cd', borderWidth:2, fill:false }]
      },
      options: {
        responsive:true,
        plugins:{
          legend:{ labels:{ font:{ size:30 } } },
          tooltip:{ bodyFont:{ size:30 }, titleFont:{ size:30 } }
        },
        scales:{
          x:{ ticks:{ font:{ size:30 } } },
          y:{ ticks:{ font:{ size:30 } } }
        }
      }
    });
  }

  function graficarPastel(labels, total){
    chartPastel?.destroy();
    chartPastel = new Chart(document.getElementById("graficaPastel"), {
      type: 'pie',
      data: {
        labels,
        datasets: [{ data: total, backgroundColor: labels.map(()=>`hsl(${Math.random()*360},60%,70%)`) }]
      },
      options: {
        responsive:true,
        plugins:{
          legend:{ labels:{ font:{ size:30 } } },
          tooltip:{ bodyFont:{ size:30 }, titleFont:{ size:30 } }
        }
      }
    });
  }

  // AHORA: Gauss con nombres reales en el eje X
  function graficarGauss(labels, pcts){
    chartGauss?.destroy();
    chartGauss = new Chart(document.getElementById("graficaGauss"), {
      type: 'bar',
      data: {
        labels, // nombres reales
        datasets: [{ label:'Frecuencia', data: pcts, backgroundColor:'#fdd835' }]
      },
      options: {
        responsive:true,
        plugins:{
          legend:{ labels:{ font:{ size:30 } } },
          tooltip:{ bodyFont:{ size:30 }, titleFont:{ size:30 } }
        },
        scales:{
          x:{ 
            ticks:{ 
              font:{ size:30 },
              autoSkip:false,
              maxRotation:45,
              minRotation:0
            } 
          },
          y:{ ticks:{ font:{ size:16 } } }
        }
      }
    });
  }

  function actualizarGraficas(){
    const arr = filtrarDatos();
    const labels = arr.map(x => `${x.nombre} (${x.anio})`);
    const labelsNombres = arr.map(x => x.nombre); // para Gauss (solo nombre)
    const ea = arr.map(x => x.ea);
    const ma = arr.map(x => x.ma);
    const sd = arr.map(x => x.sd);
    const total = arr.map((_,i) => ea[i]+ma[i]+sd[i]);
    const sum = total.reduce((a,b)=>a+b,0) || 1;
    const pcts = total.map(t => Math.round(t*100/sum));

    graficarBarras(labels, ea, ma, sd);
    graficarLinea(labels, total);
    graficarPastel(labels, total);
    graficarGauss(labelsNombres, pcts); // nombres reales en X
  }

  // ====== Inicialización ======
// Si tu template ya trae opciones preseleccionadas desde el servidor, puedes pasar keepSelection=true
  repoblarAnios(false);
  repoblarCarreras(false);
  actualizarGraficas();

  // ====== Eventos ======
  selTipo.addEventListener('change', () => {
    repoblarAnios(false);
    repoblarCarreras(false);
    actualizarGraficas();
  });
  selAnio.addEventListener('change', actualizarGraficas);
  selCuat.addEventListener('change', actualizarGraficas);
  selCarr.addEventListener('change', actualizarGraficas);
});
