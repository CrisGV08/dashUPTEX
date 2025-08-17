// static/js/titulados_historicos.js (solo filtros: Años + Programas)
document.addEventListener("DOMContentLoaded", () => {
  // --- 0) Chequeo básico de Chart.js --- 
  if (typeof window.Chart === "undefined") {
    console.error("[TH] Chart.js no está cargado. Revisa el <script src='https://cdn.jsdelivr.net/npm/chart.js'> en la plantilla.");
    return;
  }
  if (window.ChartDataLabels) Chart.register(window.ChartDataLabels);

  // --- 1) Obtener datos de json_script o fallback ---
  let raw = [];
  try {
    const safe = document.getElementById("datosTH");
    if (safe) raw = JSON.parse(safe.textContent || "[]");
    if (!raw.length) {
      const compat = document.getElementById("jsonDatos");
      if (compat) raw = JSON.parse(compat.textContent || "[]");
    }
  } catch (e) {
    console.error("[TH] Error parseando JSON:", e);
    raw = [];
  }
  console.log("[TH] Registros crudos:", raw.length);

  // --- 2) Normalizar estructura a un arreglo base uniforme ---
  const base = (raw || [])
    .map(d => ({
      programa: d.programa ?? d.nombre_programa ?? "SIN PROGRAMA",
      anio:     Number(d.anio_ingreso ?? d.anio) || 0,
      egreso:   Number(d.anio_egreso   ?? d.egreso) || 0,
      th:       Number(d.titulados_h   ?? d.titulados_hombres) || 0,
      tm:       Number(d.titulados_m   ?? d.titulados_mujeres) || 0,
      dgpH:     Number(d.dgp_h         ?? d.registrados_dgp_h) || 0,
      dgpM:     Number(d.dgp_m         ?? d.registrados_dgp_m) || 0
    }))
    .map(d => ({ ...d, totTit: d.th + d.tm, totDgp: d.dgpH + d.dgpM }))
    .sort((a,b) => a.anio - b.anio || a.programa.localeCompare(b.programa));

  // Contenedor y canvases
  const contGraficas = document.getElementById("seccionDescargable");
  const cLinea  = document.getElementById("gLinea");
  const cBarras = document.getElementById("gBarras");
  const cPastel = document.getElementById("gPastel");
  const cGauss  = document.getElementById("gGauss");

  // Alturas explícitas para evitar que Chart.js tome 0
  [cLinea, cBarras, cPastel, cGauss].forEach(cv => {
    if (cv) {
      cv.style.minHeight = "360px";
      cv.height = 360; // tamaño explícito
    }
  });

  // Si no hay datos, muestra aviso y termina
  if (!base.length) {
    if (contGraficas) {
      const msg = document.createElement("div");
      msg.className = "empty";
      msg.textContent = "No hay datos para graficar. Carga un Excel o ajusta los filtros.";
      contGraficas.prepend(msg);
    }
    return;
  }

  // --- 3) Filtros (solo Años y Programas) ---
  const $anio = document.getElementById("fltAnio");
  const $prog = document.getElementById("fltPrograma");

  const anios = [...new Set(base.map(d => d.anio))].sort((a,b)=>a-b);
  const progs = [...new Set(base.map(d => d.programa))].sort((a,b)=>a.localeCompare(b));

  function fillMulti(sel, arr){
    if (!sel) return;
    sel.innerHTML = "";
    arr.forEach(v => sel.add(new Option(String(v), String(v), false, true))); // selecciona todo por defecto
  }
  fillMulti($anio, anios);
  fillMulti($prog, progs);

  const selected = sel => sel ? Array.from(sel.selectedOptions).map(o => o.value) : [];

  function filtrar() {
    const sAnios = selected($anio);
    const sProgs = selected($prog);

    const out = base.filter(d => {
      const aOK = !sAnios.length || sAnios.includes(String(d.anio));
      const pOK = !sProgs.length || sProgs.includes(d.programa);
      return aOK && pOK;
    }).sort((a,b) => a.anio - b.anio || a.programa.localeCompare(b.programa));
    return out;
  }

  // --- 4) Utilidades de gráficas ---
  let chL=null, chB=null, chP=null, chG=null;
  const fmt = n => new Intl.NumberFormat().format(Number(n)||0);

  function destroyAll(){
    [chL,chB,chP,chG].forEach(ch => ch && ch.destroy());
    chL=chB=chP=chG=null;
  }

  function pastelColors(n){
    const out=[], m=Math.max(1,n);
    for(let i=0;i<m;i++) out.push(`hsl(${(i*360/m)%360},70%,62%)`);
    return out;
  }

  function topNConOtros(labels, values, topN=10){
    const arr = labels.map((l,i)=>({l, v:Number(values[i])||0})).sort((a,b)=>b.v-a.v);
    const top = arr.slice(0, topN);
    const otros = arr.slice(topN).reduce((s,x)=>s+x.v,0);
    if (otros>0) top.push({l:"Otros", v:otros});
    return { labels: top.map(x=>x.l), values: top.map(x=>x.v) };
  }

  function curvaGauss(vals){
    const xs = vals.map(v=>Number(v)||0);
    const n=xs.length; if(!n) return {x:[],y:[]};
    const mean = xs.reduce((a,b)=>a+b,0)/n;
    const variance = xs.reduce((a,b)=>a+(b-mean)**2,0)/Math.max(1,n-1);
    const std = Math.max(Math.sqrt(variance), 1e-9);
    const min = Math.max(0, mean-3*std), max=mean+3*std, steps=60;
    const X = Array.from({length:steps},(_,i)=> min + i*(max-min)/(steps-1));
    const Y = X.map(x => (1/(std*Math.sqrt(2*Math.PI)))*Math.exp(-0.5*((x-mean)/std)**2));
    const mY = Math.max(...Y)||1; // normaliza a 0–100
    return { x:X.map(v=>v.toFixed(1)), y:Y.map(y=> y/mY*100) };
  }

  const common = {
    responsive:true,
    maintainAspectRatio:false,
    animation:false,
    interaction:{ mode:"nearest", intersect:false },
    scales:{ y:{ beginAtZero:true, ticks:{ callback:v => fmt(v) } } },
    plugins:{
      legend:{ display:true },
      tooltip:{ enabled:true }
    }
  };

  // --- 5) Render principal ---
  const emptyNoteId = "th-empty-note";
  function showEmptyNote(){
    if (!contGraficas) return;
    if (!document.getElementById(emptyNoteId)) {
      const msg = document.createElement("div");
      msg.id = emptyNoteId;
      msg.className = "empty";
      msg.style.marginTop = "8px";
      msg.textContent = "Sin resultados con los filtros actuales.";
      contGraficas.prepend(msg);
    }
  }
  function hideEmptyNote(){
    const n = document.getElementById(emptyNoteId);
    if (n) n.remove();
  }

  function render(){
    destroyAll();
    const arr = filtrar();
    if (!arr.length) {
      showEmptyNote();
      return;
    }
    hideEmptyNote();

    const labels = arr.map(d => `${d.programa} (${d.anio}-${d.egreso})`);
    const titH   = arr.map(d => d.th);
    const titM   = arr.map(d => d.tm);
    const totTit = arr.map(d => d.totTit);
    const totDgp = arr.map(d => d.totDgp);

    // Línea (titulados totales)
    if (cLinea) {
      chL = new Chart(cLinea.getContext("2d"), {
        type:"line",
        data:{
          labels,
          datasets:[{
            label:"Titulados totales",
            data:totTit,
            borderWidth:2,
            borderColor:"#1976D2",
            backgroundColor:"rgba(25,118,210,.15)",
            tension:.3,
            fill:true
          }]
        },
        options: common
      });
    }

    // Barras apiladas H/M + línea DGP
    if (cBarras) {
      chB = new Chart(cBarras.getContext("2d"), {
        type:"bar",
        data:{
          labels,
          datasets:[
            { label:"Titulados H", data:titH, stack:"tit", backgroundColor:"#64B5F6" },
            { label:"Titulados M", data:titM, stack:"tit", backgroundColor:"#81C784" },
            { label:"DGP total",   data:totDgp, type:"line", yAxisID:"y1",
              borderColor:"#FF7043", backgroundColor:"rgba(255,112,67,.15)", borderWidth:2, tension:.25, fill:false }
          ]
        },
        options:{
          ...common,
          scales:{
            y:{ beginAtZero:true, stacked:true, ticks:{ callback:v=>fmt(v) } },
            y1:{ beginAtZero:true, position:"right", grid:{ drawOnChartArea:false }, ticks:{ callback:v=>fmt(v) } }
          }
        }
      });
    }

    // Pastel (Top 10 + Otros)
    if (cPastel) {
      const top = topNConOtros(labels, totTit, 10);
      chP = new Chart(cPastel.getContext("2d"), {
        type:"pie",
        data:{ labels: top.labels, datasets:[{ data: top.values, backgroundColor: pastelColors(top.labels.length) }] },
        options:{
          responsive:true, maintainAspectRatio:false,
          plugins:{
            legend:{ position:"right" },
            tooltip:{ callbacks:{
              label:(ctx)=>{
                const total = ctx.dataset.data.reduce((a,b)=>a+(+b||0),0)||1;
                const val = +ctx.parsed || 0;
                return `${ctx.label}: ${fmt(val)} (${(val/total*100).toFixed(1)}%)`;
              }
            }}
          }
        }
      });
    }

    // Gauss (densidad normalizada de titulados)
    if (cGauss) {
      const {x,y} = curvaGauss(totTit);
      chG = new Chart(cGauss.getContext("2d"), {
        type:"line",
        data:{ labels:x, datasets:[{ label:"Campana (titulados)", data:y, borderColor:"#8E24AA", borderWidth:2, tension:.25, fill:false }] },
        options:{ ...common, scales:{ x:{ title:{display:true,text:"Titulados"} }, y:{ title:{display:true,text:"Densidad (esc.)"}, beginAtZero:true } } }
      });
    }
  }

  // --- 6) Eventos ---
  document.getElementById("filtrosTH")?.addEventListener("change", render);
  document.getElementById("btnAplicar")?.addEventListener("click", render);
  document.getElementById("btnReset")?.addEventListener("click", () => {
    // restaurar selects (seleccionar todo)
    fillMulti($anio, anios);
    fillMulti($prog, progs);
    render();
  });

  window.addEventListener("resize", () => {
    // throttling simple
    clearTimeout(window.__thR__);
    window.__thR__ = setTimeout(render, 120);
  });

  // --- 7) Primer render ---
  render();
});

// Exportación PDF manual (opcional)
function exportarPDF(){
  const cont = document.getElementById("seccionDescargable");
  if (!cont || typeof html2pdf === "undefined") return;
  html2pdf().set({
    margin: 0.5,
    filename: "titulados_historicos.pdf",
    image: { type: "jpeg", quality: 1 },
    html2canvas: { scale: 3, useCORS: true, allowTaint: true },
    jsPDF: { unit: "in", format: "letter", orientation: "portrait" }
  }).from(cont).save();
}
