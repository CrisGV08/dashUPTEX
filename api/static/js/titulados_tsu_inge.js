// static/js/titulados_tsu_inge.js
document.addEventListener("DOMContentLoaded", () => {
  // --- 0) Dependencias ---
  if (typeof window.Chart === "undefined") {
    console.error("[TI] Chart.js no está cargado");
    return;
  }
  if (window.ChartDataLabels) Chart.register(window.ChartDataLabels);

  // --- 1) Carga de datos ---
  let raw = [];
  try {
    const safe = document.getElementById("datosTI");
    if (safe) raw = JSON.parse(safe.textContent || "[]");
  } catch (e) { console.error("[TI] JSON inválido:", e); }

  const base = (raw || [])
    .map(d => ({
      programa: d.programa ?? "SIN PROGRAMA",
      anio: Number(d.anio_ingreso) || 0,
      egreso: Number(d.anio_egreso) || 0,
      th: Number(d.titulados_h) || 0,
      tm: Number(d.titulados_m) || 0,
      dgpH: Number(d.dgp_h) || 0,
      dgpM: Number(d.dgp_m) || 0,
    }))
    .map(d => ({ ...d, totTit: d.th + d.tm, totDgp: d.dgpH + d.dgpM }))
    .filter(d => d.anio > 0)
    .sort((a, b) => a.anio - b.anio || a.programa.localeCompare(b.programa));

  const cont  = document.getElementById("seccionDescargable");
  const cBar  = document.getElementById("chBar");
  const cLine = document.getElementById("chLine");
  const cPie  = document.getElementById("chPie");
  const cGauss= document.getElementById("chGauss");

  if (!base.length) {
    if (cont) {
      const n = document.createElement("div");
      n.className = "empty";
      n.textContent = "No hay datos para graficar.";
      cont.prepend(n);
    }
    return;
  }

  // --- 2) UI (Años / Programas) ---
  const $anio = document.getElementById("fltAnio");
  const $prog = document.getElementById("fltPrograma");

  const anios = [...new Set(base.map(x => x.anio))].sort((a, b) => a - b);
  const progs = [...new Set(base.map(x => x.programa))].sort((a, b) => a.localeCompare(b));

  function fillMulti(sel, arr, selectAll = true) {
    if (!sel) return;
    sel.innerHTML = "";
    arr.forEach(v => sel.add(new Option(String(v), String(v), false, selectAll)));
  }
  fillMulti($anio, anios, true);
  fillMulti($prog, progs, true);

  // Choices.js (si está)
  let chAnio = null, chProg = null;
  if (window.Choices) {
    chAnio = new Choices("#fltAnio", { removeItemButton:true, shouldSort:true, allowSearch:true });
    chProg = new Choices("#fltPrograma",{ removeItemButton:true, shouldSort:true, allowSearch:true });

    chAnio.clearStore();
    chAnio.setChoices(anios.map(a => ({ value:String(a), label:String(a), selected:true })), "value","label", true);
    chProg.clearStore();
    chProg.setChoices(progs.map(p => ({ value:String(p), label:String(p), selected:true })), "value","label", true);
  }
  const getVals = (sel, inst) => inst ? inst.getValue(true) : Array.from(sel.selectedOptions).map(o => o.value);

  // --- 3) Helpers ---
  const fmt = n => new Intl.NumberFormat().format(Number(n) || 0);

  function aggPorAnio(data){
    const m = new Map();
    data.forEach(r => m.set(r.anio, (m.get(r.anio)||0) + r.totTit));
    const labels = Array.from(m.keys()).sort((a,b)=>a-b);
    return { labels, values: labels.map(y => m.get(y)) };
  }

  function calcGauss(values){
    if (!values.length) return { xs:[], ys:[], mean:0, std:0 };
    const mean = values.reduce((a,b)=>a+b,0)/values.length;
    const variance = values.reduce((s,v)=> s + Math.pow(v-mean,2),0)/Math.max(1, values.length-1);
    const std = Math.max(Math.sqrt(variance), 1e-9);
    const min = Math.max(0, mean-3*std), max=mean+3*std, steps=60;
    const xs = Array.from({length:steps},(_,i)=> min + i*(max-min)/(steps-1));
    const ys = xs.map(x => (1/(std*Math.sqrt(2*Math.PI))) * Math.exp(-0.5 * Math.pow((x-mean)/std,2)));
    const mY = Math.max(...ys) || 1;
    return { xs: xs.map(v=>Number(v.toFixed(1))), ys: ys.map(y=> y/mY*100), mean, std };
  }

  const COLORS = {
    bar: "#2e86de",
    barFill: "rgba(46,134,222,.15)",
    line: "#1e6bb8",
    pieA: "#64B5F6",
    pieB: "#FF7043",
    gauss: "#8E24AA",
  };

  const commonXY = (xLabel,yLabel,showValues=true)=>({
    responsive:true,
    maintainAspectRatio:false,
    animation:false,
    plugins:{
      legend:{ position:"bottom" },
      datalabels: showValues ? { anchor:"end", align:"top", formatter:v=>fmt(v), font:{weight:"bold"}, clamp:true } : { display:false },
      tooltip:{ callbacks:{ label: ctx => `${ctx.dataset.label ?? ""} ${fmt(ctx.parsed.y ?? ctx.parsed)}`.trim() } }
    },
    scales:{
      x:{ title:{display:!!xLabel, text:xLabel} },
      y:{ beginAtZero:true, title:{display:!!yLabel, text:yLabel}, ticks:{ callback:v=>fmt(v) } }
    },
    interaction:{ mode:"nearest", intersect:false }
  });

  // --- 4) Filtrado + render ---
  let chB=null, chL=null, chP=null, chG=null;

  function destroyAll(){
    [chB,chL,chP,chG].forEach(c => {
      try{
        if (!c) return;
        const canvas = c.canvas;
        c.destroy();
        canvas.removeAttribute("width");
        canvas.removeAttribute("height");
        canvas.style.removeProperty("width");
        canvas.style.removeProperty("height");
      }catch{}
    });
    chB=chL=chP=chG=null;
  }

  function filtrar(){
    const sa = getVals($anio, chAnio).map(String);
    const sp = getVals($prog, chProg).map(String);
    return base.filter(d =>
      (!sa.length || sa.includes(String(d.anio))) &&
      (!sp.length || sp.includes(String(d.programa)))
    );
  }

  const emptySel = "ti-empty-note";
  const showEmpty = () => {
    if (!cont || document.getElementById(emptySel)) return;
    const n = document.createElement("div");
    n.id = emptySel; n.className = "empty";
    n.textContent = "Sin resultados con los filtros actuales.";
    cont.prepend(n);
  };
  const hideEmpty = () => document.getElementById(emptySel)?.remove();

  function render(){
    destroyAll();
    const data = filtrar();
    if (!data.length){ showEmpty(); return; }
    hideEmpty();

    const {labels, values} = aggPorAnio(data);
    const totalTit = data.reduce((s,r)=>s+r.totTit,0);
    const totalDgp = data.reduce((s,r)=>s+r.totDgp,0);

    if (cBar)  chB = new Chart(cBar.getContext("2d"), {
      type:"bar",
      data:{ labels, datasets:[{ label:"Titulados", data:values, backgroundColor:COLORS.barFill, borderColor:COLORS.bar, borderWidth:2, maxBarThickness:44 }] },
      options: commonXY("Año de ingreso","Personas",true)
    });

    if (cLine) chL = new Chart(cLine.getContext("2d"), {
      type:"line",
      data:{ labels, datasets:[{ label:"Titulados", data:values, borderColor:COLORS.line, borderWidth:2, tension:.25, pointRadius:3 }] },
      options: commonXY("Año de ingreso","Personas",false)
    });

    if (cPie)  chP = new Chart(cPie.getContext("2d"), {
      type:"pie",
      data:{ labels:["Titulados","Registrados DGP"], datasets:[{ data:[totalTit,totalDgp], backgroundColor:[COLORS.pieA, COLORS.pieB] }] },
      options:{
        responsive:true, maintainAspectRatio:false,
        plugins:{
          legend:{ position:"bottom" },
          datalabels:{
            formatter:(v,ctx)=> {
              const sum = ctx.dataset.data.reduce((a,b)=>a+(+b||0),0) || 1;
              return `${fmt(v)} (${(v*100/sum).toFixed(1)}%)`;
            },
            anchor:"center", align:"center", font:{weight:"bold"}
          },
          tooltip:{ callbacks:{ label:tt=>{
            const total = tt.dataset.data.reduce((a,b)=>a+(+b||0),0) || 1;
            const val = +tt.parsed || 0;
            return `${tt.label}: ${fmt(val)} (${(val*100/total).toFixed(1)}%)`;
          }}}
        }
      }
    });

    if (cGauss){
      const g = calcGauss(values);
      chG = new Chart(cGauss.getContext("2d"), {
        type:"line",
        data:{ labels:g.xs, datasets:[{ label:`Campana μ=${g.mean.toFixed(1)} σ=${g.std.toFixed(1)}`, data:g.ys, borderColor:COLORS.gauss, borderWidth:2, tension:.25, pointRadius:0 }] },
        options:{
          responsive:true, maintainAspectRatio:false, animation:false,
          plugins:{ legend:{position:"bottom"}, datalabels:{display:false}, tooltip:{ callbacks:{ label:tt=>`f(x)=${(tt.parsed.y||0).toFixed(2)}` } } },
          scales:{ x:{ title:{display:true, text:"Titulados (x)"} }, y:{ beginAtZero:true, title:{display:true, text:"Densidad (esc.)"} } },
          interaction:{ mode:"nearest", intersect:false }
        }
      });
    }
  }

  // --- 5) Resize robusto ---
  const ro = new ResizeObserver(() => {
    [chB,chL,chP,chG].forEach(ch => ch && ch.resize());
  });
  [cBar,cLine,cPie,cGauss].forEach(cv => cv?.parentElement && ro.observe(cv.parentElement));

  // --- 6) Eventos ---
  const schedule = (() => { let t=null; return () => { clearTimeout(t); t=setTimeout(render, 120); }; })();
  document.getElementById("btnAplicar")?.addEventListener("click", render);
  document.getElementById("btnReset")?.addEventListener("click", () => {
    if (chAnio) {
      chAnio.clearStore();
      chAnio.setChoices(anios.map(a=>({value:String(a),label:String(a),selected:true})), "value","label", true);
    } else fillMulti($anio, anios, true);

    if (chProg) {
      chProg.clearStore();
      chProg.setChoices(progs.map(p=>({value:String(p),label:String(p),selected:true})), "value","label", true);
    } else fillMulti($prog, progs, true);

    render();
  });
  $anio?.addEventListener("change", schedule);
  $prog?.addEventListener("change", schedule);
  window.addEventListener("orientationchange", schedule);

  // --- 7) Primer render ---
  render();

  // --- 8) Exportar PDF (con carga dinámica del CDN) ---
  (function () {
    const BTN_ID   = "btnDescargarPDF";
    const TARGETID = "seccionDescargable";
    const CDN_URL  = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
    const btn = document.getElementById(BTN_ID);
    if (!btn) return;

    function ensureHtml2Pdf() {
      return new Promise((resolve, reject) => {
        if (typeof window.html2pdf !== "undefined") return resolve();
        const s = document.createElement("script");
        s.src = CDN_URL;
        s.async = true;
        s.onload = () => resolve();
        s.onerror = () => reject(new Error("No se pudo cargar html2pdf"));
        document.head.appendChild(s);
      });
    }

    async function exportar() {
      const nodo = document.getElementById(TARGETID);
      if (!nodo) return;

      // Bloquea botón para evitar dobles clics
      const prevText = btn.textContent;
      btn.disabled = true;
      btn.textContent = "Generando PDF...";

      // Asegura layout final de charts
      if (window.Chart) {
        nodo.querySelectorAll("canvas").forEach(cv => {
          const inst = Chart.getChart(cv);
          if (inst) inst.resize();
        });
      }

      const prevBg = nodo.style.backgroundColor;
      nodo.style.backgroundColor = "#ffffff";
      await new Promise(r => requestAnimationFrame(r)); // espera un frame

      const opt = {
        margin: [10, 10, 10, 10],
        filename: `titulados_${(window.__NIVEL_TI__ || 'tsu_ing')}.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
      };

      try {
        await ensureHtml2Pdf();
        await window.html2pdf().set(opt).from(nodo).save();
      } catch (e) {
        console.error("[TI] Error al generar PDF:", e);
        alert("No se pudo generar el PDF. Revisa la consola para más detalles.");
      } finally {
        nodo.style.backgroundColor = prevBg;
        btn.disabled = false;
        btn.textContent = prevText;
      }
    }

    btn.addEventListener("click", exportar);
  })();

});
