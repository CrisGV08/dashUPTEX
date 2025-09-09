// static/js/tasa_de_titulacion_usuario.js
document.addEventListener("DOMContentLoaded", () => {
  const avisos = document.getElementById("avisos");
  const cards = document.getElementById("cardsProgramas");

  const notice = (msg) => {
    if (!avisos) return;
    avisos.style.display = "block";
    avisos.innerHTML = `<div class="mensaje">${msg}</div>`;
  };

  // Paleta (azules / cian / violeta)
  const COLORS = {
    mat:  { border:'rgb(33,150,243)',  fill:'rgba(33,150,243,.15)' }, // blue 500
    egr:  { border:'rgb(2,136,209)',   fill:'rgba(2,136,209,.15)'  }, // light blue 700
    tit:  { border:'rgb(25,118,210)',  fill:'rgba(25,118,210,.15)' }, // blue 700
    ef:   { border:'rgb(124,77,255)',  fill:'rgba(124,77,255,.15)' }, // deep purple A400
    tasa: { border:'rgb(0,172,193)',   fill:'rgba(0,172,193,.15)'  }, // cyan 600
  };

  // 1) Datos del template
  let raw = [];
  try {
    raw = JSON.parse(document.getElementById("jsonDatos")?.textContent || "[]");
  } catch (e) {
    console.error("[TT-U] JSON inválido", e);
    notice("Los datos no tienen el formato esperado (JSON).");
  }

  if (typeof Chart === "undefined") {
    notice("No se pudo cargar Chart.js (revisa el CDN o la red).");
  }

  // 2) UI
  const filtroAnio = document.getElementById("filtro_anio");
  const filtroPrograma = document.getElementById("filtro_programa");
  const filtroTipo = document.getElementById("filtro_tipo");
  const filtroVista = document.getElementById("filtro_vista");
  const btnAplicar = document.getElementById("aplicarFiltros");
  const btnReset = document.getElementById("resetFiltros");
  const btnPDF = document.getElementById("btnDescargarPDF");
  const panelFiltros = document.querySelector(".filtros");
  const badgeProm = document.getElementById("promedioGlobal");
  const exportable = document.getElementById("seccionDescargable");

  // 3) Choices
  let chAnio, chPrograma, chTipo, chVista;
  const common = { removeItemButton: true, searchPlaceholderValue: "Buscar…" };
  function initChoices() {
    if (typeof Choices === "undefined") return;
    chAnio = new Choices(filtroAnio, { ...common, shouldSort:true });
    chPrograma = new Choices(filtroPrograma, { ...common, shouldSort:true });
    chTipo = new Choices(filtroTipo, { ...common, shouldSort:false });
    chVista = new Choices(filtroVista, { ...common, shouldSort:false });
  }

  // Helpers
  const fmtPct = (v) => `${(Number(v) || 0).toFixed(0)}%`;
  const fmtNum = (v) => new Intl.NumberFormat().format(Number(v)||0);

  const buildData = (filtered) => {
    const DATA = {};
    filtered.forEach(r => {
      const key = r.programa;
      if (!DATA[key]) DATA[key] = { programa: key, tipo: r.tipo, id: r.programa_id, datos: {} };
      DATA[key].datos[r.anio_ingreso] = {
        anio: r.anio_ingreso,
        matricula: +r.matricula || 0,
        egresados: +r.egresados || 0,
        titulados: +r.titulados || 0,
        ef: +r.eficiencia_terminal || 0,
        tasa: +r.tasa_titulacion || 0,
      };
    });
    return DATA;
  };

  function createSizedCanvas(container, h = 160) {
    const c = document.createElement("canvas");
    c.height = h;
    container.appendChild(c);
    const w = Math.max(300, container.clientWidth - 16);
    c.style.width = `${w}px`;
    c.width = w;
    return c;
  }

  function guardChart(createFn, container) {
    try { return createFn(); }
    catch (e) {
      console.error("[TT-U] Error Chart:", e);
      const err = document.createElement("div");
      err.className = "mensaje";
      err.textContent = "No se pudo renderizar la gráfica.";
      container.appendChild(err);
      return null;
    }
  }

  let charts = [];
  const destroyCharts = () => { charts.forEach(c => c && typeof c.destroy==="function" && c.destroy()); charts = []; };

  function render() {
    destroyCharts();
    cards.innerHTML = "";

    if (!raw.length) {
      notice("No hay registros para mostrar.");
      return;
    }

    const selAnios = chAnio ? chAnio.getValue(true).map(Number)
                            : Array.from(filtroAnio.selectedOptions).map(o=>+o.value);
    const selProgs = chPrograma ? chPrograma.getValue(true)
                                : Array.from(filtroPrograma.selectedOptions).map(o=>o.value);
    const selTipos = chTipo ? chTipo.getValue(true)
                            : Array.from(filtroTipo.selectedOptions).map(o=>o.value);
    const vistas = chVista ? chVista.getValue(true)
                           : Array.from(filtroVista.selectedOptions).map(o=>o.value);

    const filtered = raw.filter(r =>
      selAnios.includes(r.anio_ingreso) &&
      selProgs.includes(r.programa) &&
      selTipos.includes(r.tipo)
    );

    if (!filtered.length) {
      notice("No hay coincidencias con los filtros seleccionados.");
      return;
    } else {
      avisos.style.display = "none";
      avisos.innerHTML = "";
    }

    // Promedio global visible en el título
    const tasasGlobal = filtered.map(r => +r.tasa_titulacion || 0);
    const promGlobal = tasasGlobal.length ? Math.round(tasasGlobal.reduce((a,b)=>a+b,0)/tasasGlobal.length) : 0;
    if (badgeProm) badgeProm.textContent = promGlobal ? `${promGlobal}%` : "";

    const DATA = buildData(filtered);

    Object.keys(DATA).sort((a,b)=>a.localeCompare(b)).forEach(programa => {
      const info = DATA[programa];
      const years = Object.keys(info.datos).map(Number).sort((a,b)=>a-b);
      if (!years.length) return;

      const matricula = years.map(y => info.datos[y].matricula);
      const egresados = years.map(y => info.datos[y].egresados);
      const titulados = years.map(y => info.datos[y].titulados);
      const ef = years.map(y => info.datos[y].ef);
      const tasa = years.map(y => info.datos[y].tasa);

      const prom = (() => {
        const vals = tasa.filter(v => v>0);
        return vals.length ? Math.round(vals.reduce((a,b)=>a+b,0)/vals.length) : 0;
      })();

      const card = document.createElement("section");
      card.className = "program-card";
      card.innerHTML = `
        <div class="pc-head">
          <h3>${programa} <span class="pc-badge">(${prom}%)</span></h3>
        </div>
        <div class="pc-body"></div>
      `;
      const body = card.querySelector(".pc-body");

      // Línea combinada
      if (vistas.includes("linea") && typeof Chart !== "undefined") {
        const c = createSizedCanvas(body, 170);
        const ctx = c.getContext("2d");
        const ch = guardChart(() => new Chart(ctx, {
          type: "line",
          data: {
            labels: years,
            datasets: [
              { label: "Matrícula", data: matricula, yAxisID: "y", fill: true, borderWidth: 2, tension:.25,
                borderColor: COLORS.mat.border, backgroundColor: COLORS.mat.fill, pointRadius: 2 },
              { label: "Egresados", data: egresados, yAxisID: "y", fill: true, borderWidth: 2, tension:.25,
                borderColor: COLORS.egr.border, backgroundColor: COLORS.egr.fill, pointRadius: 2 },
              { label: "Titulados", data: titulados, yAxisID: "y", fill: true, borderWidth: 2, tension:.25,
                borderColor: COLORS.tit.border, backgroundColor: COLORS.tit.fill, pointRadius: 2 },
              { label: "EF. Terminal %", data: ef, yAxisID: "y1", fill: false, borderWidth: 2, tension:.25,
                borderColor: COLORS.ef.border, pointRadius: 2, borderDash:[5,4] },
              { label: "Tasa Titulación %", data: tasa, yAxisID: "y1", fill: false, borderWidth: 3, tension:.25,
                borderColor: COLORS.tasa.border, pointRadius: 2 }
            ]
          },
          options: {
            responsive:false,
            maintainAspectRatio:false,
            plugins:{ legend:{display:true, position:"top"} },
            scales:{
              y:{beginAtZero:true, title:{display:true, text:"Cantidad"}, ticks:{precision:0}},
              y1:{beginAtZero:true, max:100, position:"right", grid:{drawOnChartArea:false},
                  title:{display:true, text:"%"}, ticks:{callback:v=>`${v}%`}}
            }
          }
        }), body);
        charts.push(ch);
      }

      // Tabla mini
      if (vistas.includes("tabla")) {
        const t = document.createElement("div");
        t.className = "mini-table";
        const head = `<thead><tr><th></th>${years.map(y=>`<th>${y}</th>`).join("")}</tr></thead>`;
        const rows = [
          ["MATRICULA DE INGRESO", matricula],
          ["EGRESADOS", egresados],
          ["EF.TERMINAL %", ef.map(v=>fmtPct(v))],
          ["TITULADOS", titulados],
          ["TASA DE TITULACIÓN", tasa.map(v=>fmtPct(v))]
        ].map(([n, vals]) => `<tr><th>${n}</th>${vals.map(v=>`<td>${fmtNum(v)}</td>`).join("")}</tr>`).join("");
        t.innerHTML = `<table>${head}<tbody>${rows}</tbody></table>`;
        body.appendChild(t);
      }

      // Barras
      if (vistas.includes("barras") && typeof Chart !== "undefined") {
        const c2 = createSizedCanvas(body, 150);
        const ctx2 = c2.getContext("2d");
        const ch2 = guardChart(() => new Chart(ctx2, {
          type: "bar",
          data: {
            labels: years,
            datasets: [
              { label: "Matrícula", data: matricula,
                backgroundColor: COLORS.mat.fill, borderColor: COLORS.mat.border, borderWidth:1 },
              { label: "Egresados", data: egresados,
                backgroundColor: COLORS.egr.fill, borderColor: COLORS.egr.border, borderWidth:1 },
              { label: "Titulados", data: titulados,
                backgroundColor: COLORS.tit.fill, borderColor: COLORS.tit.border, borderWidth:1 }
            ]
          },
          options:{
            responsive:false,
            maintainAspectRatio:false,
            plugins:{ legend:{position:"top"} },
            scales:{ y:{beginAtZero:true, ticks:{precision:0}} }
          }
        }), body);
        charts.push(ch2);
      }

      cards.appendChild(card);
    });
  }

  // PDF
  const pdfOpts = {
    margin:[10,10,10,10],
    filename:"tasa_titulacion.pdf",
    image:{type:"jpeg", quality:0.98},
    html2canvas:{scale:2, useCORS:true},
    jsPDF:{unit:"mm", format:"a4", orientation:"portrait"}
  };
  async function descargarPDF() {
    if (typeof html2pdf === "undefined") return;
    const prev = panelFiltros.style.display;
    panelFiltros.style.display = "none";
    await new Promise(r=>setTimeout(r,40));
    await html2pdf().set(pdfOpts).from(exportable).save();
    panelFiltros.style.display = prev || "";
  }

  // Eventos
  btnAplicar?.addEventListener("click", render);
  btnReset?.addEventListener("click", () => {
    const allAnios = [...new Set(raw.map(d => String(d.anio_ingreso)))];
    const allProgs = [...new Set(raw.map(d => d.programa))];
    if (chAnio) chAnio.setChoiceByValue(allAnios); else [...filtroAnio.options].forEach(o=>o.selected=true);
    if (chPrograma) chPrograma.setChoiceByValue(allProgs); else [...filtroPrograma.options].forEach(o=>o.selected=true);
    if (chTipo) chTipo.setChoiceByValue(["ANTIGUO","NUEVO"]); else [...filtroTipo.options].forEach(o=>o.selected=true);
    if (chVista) chVista.setChoiceByValue(["linea","tabla","barras"]); else [...filtroVista.options].forEach(o=>o.selected=true);
    render();
  });
  btnPDF?.addEventListener("click", descargarPDF);

  // Init
  initChoices();
  render();
  console.log("[TT-U] registros:", raw.length);
});
