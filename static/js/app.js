/* =========================================================================
   app.js — Lógica de la interfaz del simulador
   ========================================================================= */
(() => {
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const { fmt } = Graficas;

  const COLOR = { exito: "#2f7d5b", abandono: "#a3283a", error: "#d27a1f", seguimiento: "#3a6ea5", incompleto: "#8f877b" };
  const COLOR_TIPO = { "inicial": "#6a4c93", "intermedio": "#7a7064", "final exitoso": COLOR.exito, "final negativo": COLOR.abandono, "error": COLOR.error, "seguimiento": COLOR.seguimiento };
  const CAT_TIPO = { "final exitoso": "exito", "final negativo": "abandono", "error": "error", "seguimiento": "seguimiento" };
  const CATS = ["exito", "abandono", "error", "seguimiento"];

  let M = null;          // modelo
  let SIM = null;        // última simulación
  let MEJ = null;        // última mejora
  let matrizActual = "conteos";

  // ------------------------------------------------------------------ utilidades
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const est = i => M.estados[i];
  const catDe = i => CAT_TIPO[est(i).tipo] || null;
  const nombreCat = c => M.etiquetas[c];

  async function api(url, datos) {
    const r = await fetch(url, datos ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos) } : {});
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "Error del servidor");
    return j;
  }

  function chipsCamino(camino, resultado) {
    return camino.map((s, k) => {
      const e = est(s);
      let cls = "paso";
      if (e.tipo === "inicial") cls += " paso--inicial";
      const c = catDe(s);
      if (c) cls += " paso--" + c;
      if (k === camino.length - 1 && resultado === "incompleto") cls += " paso--incompleto";
      return (k ? '<span class="flecha">›</span>' : "") + `<span class="${cls}" data-tip="${esc(e.codigo + " · " + e.nombre)}">${e.codigo}</span>`;
    }).join("");
  }
  // tooltips para chips de estados (delegado)
  document.addEventListener("mouseover", e => {
    const t = e.target.closest("[data-tip]"); if (!t) return;
    const tip = $("#tooltip"); tip.textContent = t.dataset.tip; tip.classList.add("visible");
    const r = t.getBoundingClientRect();
    tip.style.left = Math.min(innerWidth - tip.offsetWidth - 8, Math.max(8, r.left + r.width / 2 - tip.offsetWidth / 2)) + "px";
    tip.style.top = Math.max(8, r.top - tip.offsetHeight - 8) + "px";
  });
  document.addEventListener("mouseout", e => { if (e.target.closest("[data-tip]")) Graficas.ocultarTip(); });

  function filtros(cont, opciones, alCambiar, inicial = "todos") {
    cont.innerHTML = opciones.map(o => `<button type="button" data-v="${o.v}" class="${o.v === inicial ? "activo" : ""}">${o.color ? `<span class="punto" style="background:${o.color}"></span>` : ""}${o.t}</button>`).join("");
    cont.onclick = e => {
      const b = e.target.closest("button"); if (!b) return;
      cont.querySelectorAll("button").forEach(x => x.classList.toggle("activo", x === b));
      alCambiar(b.dataset.v);
    };
  }

  // ------------------------------------------------------------------ pestañas
  $$(".pestana").forEach(b => b.addEventListener("click", () => {
    $$(".pestana").forEach(x => x.classList.toggle("activa", x === b));
    $$(".vista").forEach(v => v.classList.toggle("activa", v.id === "vista-" + b.dataset.vista));
    b.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
    requestAnimationFrame(Graficas.redibujarVisibles);
  }));
  const irA = v => $(`.pestana[data-vista="${v}"]`).click();

  // ------------------------------------------------------------------ controles
  const rgU = $("#rgUsuarios"), inU = $("#inUsuarios"), rgP = $("#rgPasos"), inP = $("#inPasos");
  const MINU = +inU.min, MAXU = +inU.max;
  const posAU = p => Math.round(MINU * Math.pow(MAXU / MINU, p / 1000));
  const uAPos = u => Math.round(1000 * Math.log(u / MINU) / Math.log(MAXU / MINU));
  const relleno = r => r.style.setProperty("--p", (100 * (r.value - r.min) / (r.max - r.min)) + "%");
  function redondeoBonito(v) { const m = Math.pow(10, Math.max(0, Math.floor(Math.log10(v)) - 1)); return Math.round(v / m) * m; }
  function syncU(v, desde) {
    v = Math.min(MAXU, Math.max(MINU, v || MINU));
    if (desde !== "input") inU.value = v;
    if (desde !== "rango") rgU.value = uAPos(v);
    relleno(rgU);
    $$("#chipsUsuarios button").forEach(b => b.classList.toggle("activo", +b.dataset.v === v));
  }
  rgU.addEventListener("input", () => syncU(redondeoBonito(posAU(+rgU.value)), "rango"));
  inU.addEventListener("input", () => { const v = +inU.value; if (v >= MINU && v <= MAXU) syncU(v, "input"); });
  inU.addEventListener("change", () => syncU(+inU.value));
  $("#chipsUsuarios").addEventListener("click", e => { const b = e.target.closest("button"); if (b) syncU(+b.dataset.v); });
  rgP.addEventListener("input", () => { inP.value = rgP.value; relleno(rgP); });
  inP.addEventListener("input", () => { if (+inP.value >= +rgP.min && +inP.value <= +rgP.max) { rgP.value = inP.value; relleno(rgP); } });
  $("#btnSemilla").addEventListener("click", () => $("#inSemilla").value = 2026);
  syncU(1000); relleno(rgP);

  const rgR = $("#rgReduccion");
  rgR.addEventListener("input", () => { $("#lblReduccion").textContent = rgR.value + " %"; relleno(rgR); });
  relleno(rgR);

  // ------------------------------------------------------------------ carga del modelo
  async function cargarModelo() {
    M = await api("/api/modelo");
    $("#rEstados").textContent = M.estados.length;
    $("#rRecorridos").textContent = M.recorridos.length;
    $("#rTipos").textContent = M.tipos_usuario.length;
    pintarEstados(); pintarRecorridos(); pintarMatriz(); pintarSelects(); pintarTeorico();
  }

  // ------------------------------------------------------------------ ESTADOS
  let filtroTipo = "todos";
  function pintarEstados() {
    const tipos = ["inicial", "intermedio", "final exitoso", "final negativo", "error", "seguimiento"];
    filtros($("#filtroTipo"), [{ v: "todos", t: "Todos" }, ...tipos.map(t => ({ v: t, t: t[0].toUpperCase() + t.slice(1), color: COLOR_TIPO[t] }))], v => { filtroTipo = v; tablaEstados(); });
    $("#buscaEstado").addEventListener("input", tablaEstados);
    tablaEstados();
  }
  function tablaEstados() {
    const q = $("#buscaEstado").value.trim().toLowerCase();
    $("#tbEstados").innerHTML = M.estados
      .filter(e => (filtroTipo === "todos" || e.tipo === filtroTipo) && (!q || (e.codigo + e.nombre + e.descripcion + e.seccion).toLowerCase().includes(q)))
      .map(e => `<tr><td class="codigo">${e.codigo}</td><td><strong>${esc(e.nombre)}</strong></td><td>${esc(e.descripcion)}</td>
        <td><span class="etiqueta" style="background:${COLOR_TIPO[e.tipo]}">${e.tipo}</span></td><td>${esc(e.seccion)}</td></tr>`).join("")
      || `<tr><td colspan="5" class="ayuda">Sin coincidencias.</td></tr>`;
  }

  // ------------------------------------------------------------------ RECORRIDOS
  let fTU = "todos", fRes = "todos";
  function pintarRecorridos() {
    const v = M.validacion;
    $("#txtRecorridos").textContent = `${v.recorridos_distintos} recorridos distintos de ${M.tipos_usuario.length} tipos de usuario. Todos empiezan en S0 y terminan en un estado final.`;
    const sel = $("#selTipoUsuario");
    sel.innerHTML = `<option value="todos">Todos los tipos de usuario</option>` + M.tipos_usuario.map(t => `<option>${esc(t)}</option>`).join("");
    sel.onchange = () => { fTU = sel.value; gridRec(); };
    filtros($("#filtroResRec"), [{ v: "todos", t: "Todos" }, ...CATS.map(c => ({ v: c, t: nombreCat(c), color: COLOR[c] }))], v => { fRes = v; gridRec(); });
    gridRec();
  }
  function gridRec() {
    const lista = M.recorridos.filter(r => (fTU === "todos" || r.tipo_usuario === fTU) && (fRes === "todos" || catDe(r.estados.at(-1)) === fRes));
    $("#gridRecorridos").innerHTML = lista.map(r => {
      const c = catDe(r.estados.at(-1));
      return `<article class="tarjeta-rec"><header><span class="num">#${r.id}</span><span class="tu">${esc(r.tipo_usuario)}</span></header>
        <p>${esc(r.descripcion)}</p><div class="camino">${chipsCamino(r.estados)}</div>
        <small style="color:${COLOR[c]};font-weight:700">${nombreCat(c)} · ${r.estados.length - 1} pasos</small></article>`;
    }).join("") || '<p class="ayuda">No hay recorridos con ese filtro.</p>';
  }

  // ------------------------------------------------------------------ MATRICES
  function pintarMatriz() {
    const datos = M[matrizActual], cods = M.estados.map(e => e.codigo);
    const esP = matrizActual === "probabilidades";
    const max = Math.max(...datos.flat().filter((_, k) => true)) || 1;
    const maxC = esP ? 1 : Math.max(...datos.flat());
    let h = `<thead><tr><th title="Fila = estado de origen, columna = estado de destino">De → A</th>${cods.map((c, j) => `<th data-j="${j}">${c}</th>`).join("")}${esP ? "" : "<th>Total</th>"}</tr></thead><tbody>`;
    datos.forEach((fila, i) => {
      const tot = fila.reduce((a, b) => a + b, 0);
      h += `<tr data-i="${i}"><th>${cods[i]}</th>`;
      fila.forEach((v, j) => {
        const a = v ? Math.max(0.08, esP ? Math.sqrt(v) : Math.sqrt(v / maxC)) : 0;
        const estilo = v ? `background:rgba(107,29,42,${a.toFixed(3)});${a > 0.5 ? "color:#fff;" : ""}` : "";
        const txt = esP ? (v ? v.toFixed(2).replace(".", ",") : "0") : v;
        h += `<td data-i="${i}" data-j="${j}" class="${v ? "" : "cero"}${esP && i === j && v === 1 ? " abs" : ""}" style="${estilo}">${txt}</td>`;
      });
      if (!esP) h += `<th style="position:static">${tot}</th>`;
      h += "</tr>";
    });
    $("#tablaMatriz").innerHTML = h + "</tbody>";
    const total = M.conteos.flat().reduce((a, b) => a + b, 0);
    $("#txtMatriz").textContent = esP
      ? "P[i][j] = conteo(i→j) / total de la fila i. Cada fila suma 1. Los estados finales son absorbentes (1 en la diagonal)."
      : `${fmt(total)} transiciones contadas en los ${M.recorridos.length} recorridos base (${M.estados.length} × ${M.estados.length}).`;
  }
  $$(".segmentado button").forEach(b => b.addEventListener("click", () => {
    $$(".segmentado button").forEach(x => x.classList.toggle("activo", x === b));
    matrizActual = b.dataset.m; pintarMatriz();
  }));
  $("#chkCeros").addEventListener("change", e => $("#tablaMatriz").classList.toggle("sin-ceros", e.target.checked));
  function focoCelda(td) {
    $$(".matriz .foco, .matriz .fila-foco, .matriz .col-foco").forEach(x => x.classList.remove("foco", "fila-foco", "col-foco"));
    if (!td || td.dataset.j === undefined || td.tagName !== "TD") return;
    const i = +td.dataset.i, j = +td.dataset.j;
    td.classList.add("foco"); td.parentElement.classList.add("fila-foco");
    $(`.matriz thead th[data-j="${j}"]`)?.classList.add("col-foco");
    const c = M.conteos[i][j], p = M.probabilidades[i][j], tot = M.conteos[i].reduce((a, b) => a + b, 0);
    $("#infoCelda").innerHTML = `<b>${est(i).codigo}</b> ${esc(est(i).nombre)} → <b>${est(j).codigo}</b> ${esc(est(j).nombre)}<br>
      Conteo: <b>${c}</b> de ${tot} salidas · Probabilidad: <b>${fmt(p, 4)}</b>${i === j && p === 1 ? " (estado absorbente)" : ""}`;
  }
  $("#tablaMatriz").addEventListener("mouseover", e => focoCelda(e.target.closest("td")));
  $("#tablaMatriz").addEventListener("click", e => focoCelda(e.target.closest("td")));

  function pintarSelects() {
    const opts = M.estados.map(e => `<option value="${e.indice}">${e.codigo} · ${esc(e.nombre)}</option>`).join("");
    $("#selFila").innerHTML = opts;
    $("#selFila").value = 1;
    $("#selFila").onchange = pintarFila;
    pintarFila();
    $("#selMejora").innerHTML = M.estados.filter(e => !CAT_TIPO[e.tipo]).map(e => `<option value="${e.indice}">${e.codigo} · ${esc(e.nombre)}</option>`).join("");
    $("#selMejora").value = 31;
    $("#selMejora").onchange = pintarReco;
    pintarReco();
  }
  function pintarFila() {
    const i = +$("#selFila").value, fila = M.probabilidades[i];
    const datos = fila.map((p, j) => ({ j, p })).filter(x => x.p > 0).sort((a, b) => b.p - a.p)
      .map(x => ({ label: `${est(x.j).codigo} ${est(x.j).nombre}`, value: x.p, color: catDe(x.j) ? COLOR[catDe(x.j)] : "#7a6f62",
        tooltip: `<b>${est(i).codigo} → ${est(x.j).codigo}</b><br>${esc(est(x.j).nombre)}<br>p = ${fmt(x.p, 4)} · conteo ${M.conteos[i][x.j]}` }));
    Graficas.barrasH($("#gFila"), datos, { formato: v => fmt(v * 100, 1) + " %", maxEtiqueta: 34 });
  }
  function pintarTeorico() {
    const t = M.teorico;
    $("#kpisTeorico").innerHTML = CATS.map(c => kpi(nombreCat(c), fmt(t.porcentajes[c], 2) + " %", "Probabilidad exacta", COLOR[c], t.porcentajes[c])).join("")
      + kpi("Pasos esperados", fmt(t.pasos_esperados, 2), "Sin límite de pasos", "#6b1d2a");
    animarBarras($("#kpisTeorico"));
  }
  function pintarReco() {
    const cod = est(+$("#selMejora").value).codigo;
    $("#recoMejora").innerHTML = `<p><strong>Mejora propuesta para ${cod} · ${esc(est(+$("#selMejora").value).nombre)}:</strong> ${esc(M.recomendaciones[cod] || M.recomendacion_general)}</p>`;
  }

  // ------------------------------------------------------------------ SIMULACIÓN
  function kpi(etq, val, det, color, pct) {
    return `<div class="kpi" style="--c:${color}"><div class="kpi__etq">${etq}</div><div class="kpi__val">${val}</div>
      <div class="kpi__det">${det}</div>${pct !== undefined ? `<div class="kpi__barra"><i data-w="${pct}"></i></div>` : ""}</div>`;
  }
  const animarBarras = cont => requestAnimationFrame(() => cont.querySelectorAll(".kpi__barra i").forEach(i => i.style.width = i.dataset.w + "%"));

  function params() {
    return { usuarios: +inU.value, pasos_max: +inP.value, semilla: $("#inSemilla").value === "" ? null : +$("#inSemilla").value };
  }
  function validar(p) {
    if (!Number.isInteger(p.usuarios) || p.usuarios < MINU || p.usuarios > MAXU) return `El número de usuarios debe estar entre ${MINU} y ${fmt(MAXU)}.`;
    if (!Number.isInteger(p.pasos_max) || p.pasos_max < +inP.min || p.pasos_max > +inP.max) return `Los pasos máximos deben estar entre ${inP.min} y ${inP.max}.`;
    return "";
  }
  const cargando = on => $("#cargando").classList.toggle("oculto", !on);

  $("#formSim").addEventListener("submit", async e => {
    e.preventDefault();
    const p = params(), err = validar(p);
    $("#errSim").textContent = err; if (err) return;
    $("#btnSimular").disabled = true; cargando(true);
    try {
      const [r] = await Promise.all([api("/api/simular", { ...p, vista_previa: 40 }), new Promise(ok => setTimeout(ok, 350))]);
      SIM = r; pintarSimulacion();
      // mejora automática sobre el estado crítico (para las respuestas)
      if (r.estado_critico) { $("#selMejora").value = r.estado_critico.estado; pintarReco(); await ejecutarMejora(true); }
      $("#resultados").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (ex) { $("#errSim").textContent = ex.message; }
    finally { $("#btnSimular").disabled = false; cargando(false); }
  });

  function pintarSimulacion() {
    const r = SIM, n = r.parametros.usuarios;
    $("#vacio").classList.add("oculto"); $("#resultados").classList.remove("oculto");
    const k = $("#kpis");
    k.innerHTML = CATS.map(c => kpi(nombreCat(c), fmt(r.porcentajes[c], 1) + " %", `${fmt(r.conteos[c])} de ${fmt(n)} usuarios`, COLOR[c], r.porcentajes[c])).join("")
      + kpi("Promedio de pasos", fmt(r.pasos.promedio, 2), `Mediana ${fmt(r.pasos.mediana)} · máx. ${r.pasos.maximo}`, "#6b1d2a")
      + (r.conteos.incompleto
        ? kpi("Sin terminar", fmt(r.porcentajes.incompleto, 1) + " %", `Llegaron al límite de ${r.parametros.pasos_max} pasos`, COLOR.incompleto, r.porcentajes.incompleto)
        : kpi("Usuarios simulados", fmt(n), `Semilla ${r.parametros.semilla} · máx. ${r.parametros.pasos_max} pasos`, "#b8893b"));
    animarBarras(k);

    const cats = [...CATS, ...(r.conteos.incompleto ? ["incompleto"] : [])];
    Graficas.dona($("#gDona"), cats.map(c => ({ label: nombreCat(c), value: r.conteos[c], color: COLOR[c] })), { valor: fmt(n), texto: "usuarios" });
    $("#txtMasFrecuente").innerHTML = `Resultado más frecuente: <strong style="color:${COLOR[r.resultado_mas_frecuente]}">${nombreCat(r.resultado_mas_frecuente)}</strong> (${fmt(r.porcentajes[r.resultado_mas_frecuente], 1)} %).`;

    mosaico(r);
    pintarCritico(r);

    Graficas.barrasH($("#gPerdidas"), r.perdidas.slice(0, 10).map(p => ({
      label: `${p.codigo} ${p.nombre}`, value: p.total, color: p.error > p.abandono ? COLOR.error : COLOR.abandono,
      tooltip: `<b>${p.codigo} · ${esc(p.nombre)}</b><br>Abandonos: ${fmt(p.abandono)} · Errores: ${fmt(p.error)}<br>Pasaron por aquí: ${fmt(p.visitas)} (tasa de pérdida ${fmt(p.tasa, 1)} %)`
    })));
    Graficas.barrasH($("#gFinales"), r.finales.filter(f => f.usuarios).sort((a, b) => b.usuarios - a.usuarios).map(f => ({
      label: `${f.codigo} ${f.nombre}`, value: f.usuarios, color: COLOR[f.categoria],
      tooltip: `<b>${f.codigo} · ${esc(f.nombre)}</b><br>${fmt(f.usuarios)} usuarios (${fmt(f.porcentaje, 1)} %)`
    })));
    Graficas.histograma($("#gHist"), r.histograma_pasos);
    $("#txtPasos").textContent = `Promedio ${fmt(r.pasos.promedio, 2)} pasos · mediana ${fmt(r.pasos.mediana)} · mínimo ${r.pasos.minimo} · máximo ${r.pasos.maximo}.`;

    filtros($("#filtroPrevia"), [{ v: "todos", t: "Todos" }, ...CATS.map(c => ({ v: c, t: nombreCat(c), color: COLOR[c] })),
      ...(r.vista_previa.some(u => u.resultado === "incompleto") ? [{ v: "incompleto", t: "Sin terminar", color: COLOR.incompleto }] : [])], listaPrevia);
    listaPrevia("todos");
    $("#lnkCsvSim").href = `/exportar/simulacion.csv?usuarios=${n}&pasos=${r.parametros.pasos_max}&semilla=${r.parametros.semilla}`;
  }

  function listaPrevia(f) {
    const lista = SIM.vista_previa.filter(u => f === "todos" || u.resultado === f);
    $("#listaPrevia").innerHTML = lista.map(u => `<li><span class="u">Usuario ${u.usuario}</span><div class="camino">${chipsCamino(u.camino, u.resultado)}</div>
      <span class="r" style="color:${COLOR[u.resultado]}">${nombreCat(u.resultado).replace(" (límite de pasos)", "")}<br><small style="color:var(--tinta-2);font-weight:400">${u.pasos} pasos</small></span></li>`).join("")
      || '<li class="ayuda">Ningún usuario de la vista previa tuvo ese resultado.</li>';
  }

  function pintarCritico(r) {
    const c = r.estado_critico, p = $("#panelCritico");
    if (!c) { p.innerHTML = '<p class="ayuda">No hubo pérdidas en esta simulación.</p>'; return; }
    const riesgo = r.estado_mayor_riesgo;
    p.innerHTML = `<div class="critico">
      <div class="critico__ins">${c.codigo}</div>
      <div><div class="critico__tit">⚠ Estado crítico detectado</div><h3>${esc(c.nombre)}</h3>
        <p>Desde aquí se perdieron <strong>${fmt(c.total)}</strong> usuarios (${fmt(c.abandono)} abandonos, ${fmt(c.error)} errores): el
        <strong>${fmt(c.porcentaje_de_perdidas, 1)} %</strong> de todas las pérdidas. De cada 100 personas que pasan por este estado, ${fmt(c.tasa, 0)} se pierden.
        ${riesgo && riesgo.codigo !== c.codigo ? `<br>Mayor tasa de riesgo: <strong>${riesgo.codigo} ${esc(riesgo.nombre)}</strong> (${fmt(riesgo.tasa, 1)} % de quienes pasan por allí).` : ""}</p></div>
      <div class="critico__num"><b>${fmt(c.total)}</b><small>usuarios perdidos</small></div>
      <div class="critico__reco"><p><strong>Recomendación:</strong> ${esc(c.recomendacion)}</p>
        <button class="btn btn--primario" id="btnIrMejora">✦ Probar esta mejora</button></div></div>`;
    $("#btnIrMejora").onclick = () => { $("#selMejora").value = c.estado; pintarReco(); irA("mejora"); };
  }

  // Mosaico animado: un cuadro por usuario (o una muestra proporcional si son muchos)
  let animMosaico;
  function mosaico(r) {
    const cv = $("#mosaico"), n = r.parametros.usuarios;
    const celdas = Math.min(n, 1000), porCelda = n / celdas;
    const cats = ["exito", "abandono", "error", "seguimiento", "incompleto"];
    // reparto proporcional de categorías en las celdas
    let lista = []; let acum = 0, asignadas = 0;
    cats.forEach(c => { acum += r.conteos[c]; const hasta = Math.round(acum / n * celdas); for (; asignadas < hasta; asignadas++) lista.push(c); });
    // orden pseudoaleatorio estable
    let s = r.parametros.semilla || 1; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
    for (let i = lista.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [lista[i], lista[j]] = [lista[j], lista[i]]; }
    $("#leyendaMosaico").innerHTML = cats.filter(c => r.conteos[c]).map(c => `<span><i style="background:${COLOR[c]}"></i>${nombreCat(c)}</span>`).join("")
      + `<span style="margin-left:auto;color:var(--tinta-2)">${porCelda > 1 ? `1 cuadro ≈ ${fmt(porCelda, 0)} usuarios` : "1 cuadro = 1 usuario"}</span>`;
    cancelAnimationFrame(animMosaico);
    const dibujar = progreso => {
      const dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
      cv.width = W * dpr; cv.height = H * dpr;
      const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr);
      const lado = Math.floor(Math.sqrt(W * H / celdas)), cols = Math.max(1, Math.floor(W / lado)), filas = Math.ceil(celdas / cols);
      const t = Math.min(lado, Math.floor(H / filas)), ox = (W - cols * t) / 2, oy = (H - filas * t) / 2;
      const hasta = Math.floor(celdas * progreso);
      for (let i = 0; i < celdas; i++) {
        const x = ox + (i % cols) * t, y = oy + Math.floor(i / cols) * t;
        ctx.fillStyle = i < hasta ? COLOR[lista[i]] : "#e6dece";
        const g = t > 6 ? 1.2 : 0.5;
        ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x + g, y + g, t - 2 * g, t - 2 * g, t > 8 ? 2 : 0) : ctx.rect(x + g, y + g, t - 2 * g, t - 2 * g); ctx.fill();
      }
    };
    const t0 = performance.now(), dur = 1400;
    const paso = now => { const p = Math.min(1, (now - t0) / dur); dibujar(1 - Math.pow(1 - p, 3)); if (p < 1) animMosaico = requestAnimationFrame(paso); };
    animMosaico = requestAnimationFrame(paso);
    window.addEventListener("resize", () => SIM && dibujar(1), { once: true });
  }

  // ------------------------------------------------------------------ MEJORA
  $("#formMejora").addEventListener("submit", async e => { e.preventDefault(); cargando(true); try { await ejecutarMejora(false); } finally { cargando(false); } });

  async function ejecutarMejora(silencioso) {
    const p = params(), err = validar(p);
    $("#errMejora").textContent = err; if (err) return;
    try {
      MEJ = await api("/api/mejora", { ...p, semilla: SIM ? SIM.parametros.semilla : (p.semilla ?? 2026), estado: +$("#selMejora").value, reduccion: +rgR.value, modo: $("#selModo").value });
      pintarMejora();
      if (!silencioso) $("#resMejora").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (ex) { $("#errMejora").textContent = ex.message; }
  }

  function pintarMejora() {
    const m = MEJ;
    $("#resMejora").classList.remove("oculto");
    $("#txtMejoraParams").textContent = `${m.estado.codigo} ${m.estado.nombre} · reducción ${Math.round(m.reduccion * 100)} % · ${fmt(params().usuarios)} usuarios, misma semilla.`;
    const cats = CATS.map(c => ({ label: nombreCat(c).replace(" pendiente", "") }));
    Graficas.agrupadas($("#gComparar"), cats, [
      { name: "Antes", values: CATS.map(c => m.base.porcentajes[c]), colores: CATS.map(c => COLOR[c]), opacidad: 0.38, leyenda: "#6b1d2a" },
      { name: "Después de la mejora", values: CATS.map(c => m.mejorado.porcentajes[c]), colores: CATS.map(c => COLOR[c]), leyenda: "#6b1d2a" },
    ]);
    $("#deltas").innerHTML = CATS.map(c => {
      const d = m.mejorado.porcentajes[c] - m.base.porcentajes[c], dt = m.teorico_mejorado[c] - m.teorico_base[c];
      const bueno = c === "exito" ? d > 0.05 : d < -0.05, malo = c === "exito" ? d < -0.05 : d > 0.05;
      return `<div class="delta"><span class="nom"><i style="background:${COLOR[c]}"></i>${nombreCat(c)}</span>
        <span>${fmt(m.base.porcentajes[c], 1)} % → <strong>${fmt(m.mejorado.porcentajes[c], 1)} %</strong><small>Teórico: ${fmt(m.teorico_base[c], 1)} → ${fmt(m.teorico_mejorado[c], 1)} %</small></span>
        <span class="cambio ${bueno ? "bueno" : malo ? "malo" : "neutro"}" title="Cambio simulado">Sim. ${d >= 0 ? "+" : ""}${fmt(d, 1)} pp</span>
        <span class="cambio ${dt > 0.05 === (c === "exito") && Math.abs(dt) > 0.05 ? "bueno" : Math.abs(dt) > 0.05 ? "malo" : "neutro"}" title="Cambio teórico">Teó. ${dt >= 0 ? "+" : ""}${fmt(dt, 1)} pp</span></div>`;
    }).join("") + `<p class="ayuda">pp = puntos porcentuales. Primera columna de cambio: simulación; segunda: cálculo teórico exacto.</p>`;
    $("#txtFila").textContent = `Probabilidades de salida de ${m.estado.codigo} antes y después de aplicar la mejora.`;
    $("#tbFila").innerHTML = m.fila.map(f => {
      const d = f.despues - f.antes;
      return `<tr><td><span class="codigo">${f.destino}</span> ${esc(f.nombre)}</td><td>${fmt(f.antes, 4)}</td><td><strong>${fmt(f.despues, 4)}</strong></td>
        <td style="color:${d > 1e-6 ? COLOR.exito : d < -1e-6 ? COLOR.abandono : "inherit"};font-weight:600">${d > 1e-6 ? "+" : ""}${fmt(d, 4)}</td></tr>`;
    }).join("");
    pintarRespuestas();
  }

  // ------------------------------------------------------------------ RESPUESTAS A LAS 6 PREGUNTAS
  function pintarRespuestas() {
    if (!SIM || !MEJ) return;
    const r = SIM, c = r.estado_critico, m = MEJ, n = r.parametros.usuarios;
    const mf = r.resultado_mas_frecuente;
    const orden = CATS.slice().sort((a, b) => r.porcentajes[b] - r.porcentajes[a]);
    const d = cat => m.mejorado.porcentajes[cat] - m.base.porcentajes[cat];
    const sig = v => (v >= 0 ? "+" : "") + fmt(v, 1);
    const segundo = r.perdidas[1];
    const resp = [
      ["1. ¿Cuál fue el resultado final más frecuente?",
        `Con ${fmt(n)} usuarios y un máximo de ${r.parametros.pasos_max} pasos, el resultado más frecuente fue <strong>${nombreCat(mf).toLowerCase()}</strong> con ${fmt(r.porcentajes[mf], 1)} %. Le siguen ${orden.slice(1).map(x => `${nombreCat(x).toLowerCase()} (${fmt(r.porcentajes[x], 1)} %)`).join(", ")}. Sumando abandono y error, ${fmt(r.porcentajes.abandono + r.porcentajes.error, 1)} % de las personas no logra su objetivo.`],
      ["2. ¿En qué estado se pierden más usuarios?",
        `En <strong>${c.codigo} – ${esc(c.nombre)}</strong>: ${fmt(c.total)} usuarios (${fmt(c.porcentaje_de_perdidas, 1)} % de todas las pérdidas) abandonaron o tuvieron error justo después de este estado.${segundo ? ` El segundo es ${segundo.codigo} – ${esc(segundo.nombre)} con ${fmt(segundo.total)} usuarios.` : ""}`],
      ["3. ¿Qué estado es más crítico para la experiencia? ¿Por qué?",
        `${c.codigo} – ${esc(c.nombre)}, porque concentra la mayor cantidad de pérdidas y ${fmt(c.tasa, 0)} de cada 100 personas que llegan allí se van sin cumplir su objetivo. En el sitio real esto ocurre porque muchas secciones (Visita, Agenda, Historia, Contacto, Patrimonio) muestran “Información por confirmar” o “Contenido en construcción”.${r.estado_mayor_riesgo && r.estado_mayor_riesgo.codigo !== c.codigo ? ` También es riesgoso ${r.estado_mayor_riesgo.codigo} – ${esc(r.estado_mayor_riesgo.nombre)}, con la tasa de pérdida más alta (${fmt(r.estado_mayor_riesgo.tasa, 1)} %).` : ""}`],
      ["4. ¿Qué cambio harían primero para aumentar la probabilidad de éxito?",
        esc(M.recomendaciones[c.codigo] || M.recomendacion_general)],
      ["5. ¿Qué pasaría si mejoran el estado donde más usuarios abandonan?",
        `Al reducir en ${Math.round(m.reduccion * 100)} % las salidas a abandono/error de ${m.estado.codigo}, los usuarios recuperados continúan hacia su objetivo. El éxito pasa de ${fmt(m.base.porcentajes.exito, 1)} % a ${fmt(m.mejorado.porcentajes.exito, 1)} % (${sig(d("exito"))} pp) y el abandono de ${fmt(m.base.porcentajes.abandono, 1)} % a ${fmt(m.mejorado.porcentajes.abandono, 1)} % (${sig(d("abandono"))} pp). El nuevo estado crítico sería ${m.mejorado.estado_critico ? m.mejorado.estado_critico.codigo + " – " + esc(m.mejorado.estado_critico.nombre) : "ninguno"}.`],
      ["6. ¿Cómo cambiarían los porcentajes de éxito, abandono y error?",
        `Simulación (misma semilla): éxito ${fmt(m.base.porcentajes.exito, 1)} → ${fmt(m.mejorado.porcentajes.exito, 1)} %, abandono ${fmt(m.base.porcentajes.abandono, 1)} → ${fmt(m.mejorado.porcentajes.abandono, 1)} %, error ${fmt(m.base.porcentajes.error, 1)} → ${fmt(m.mejorado.porcentajes.error, 1)} %, seguimiento ${fmt(m.base.porcentajes.seguimiento, 1)} → ${fmt(m.mejorado.porcentajes.seguimiento, 1)} %. Cálculo teórico exacto: éxito ${fmt(m.teorico_base.exito, 1)} → ${fmt(m.teorico_mejorado.exito, 1)} %, abandono ${fmt(m.teorico_base.abandono, 1)} → ${fmt(m.teorico_mejorado.abandono, 1)} %, error ${fmt(m.teorico_base.error, 1)} → ${fmt(m.teorico_mejorado.error, 1)} %.`],
    ];
    $("#respuestas").innerHTML = resp.map(([q, a]) => `<div class="respuesta"><h4>${q}</h4><p>${a}</p></div>`).join("");
  }

  cargarModelo().catch(e => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<div class="panel"><p class="error">No se pudo cargar el modelo: ${esc(e.message)}</p></div>`); });
})();
