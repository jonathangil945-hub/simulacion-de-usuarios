/* =========================================================================
   graficas.js — Gráficas en SVG sin librerías externas (funcionan sin internet).
   ========================================================================= */
const Graficas = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const tip = () => document.getElementById("tooltip");
  const renders = new Map();   // contenedor -> función de redibujo (para cambiar de tamaño)

  function el(tag, attrs = {}, padre) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (padre) padre.appendChild(n);
    return n;
  }
  const fmt = (v, dec = 0) => Number(v).toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });

  function mostrarTip(html, ev) {
    const t = tip(); t.innerHTML = html; t.classList.add("visible");
    const x = (ev.touches ? ev.touches[0].clientX : ev.clientX), y = (ev.touches ? ev.touches[0].clientY : ev.clientY);
    const w = t.offsetWidth, h = t.offsetHeight;
    t.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, x - w / 2)) + "px";
    t.style.top = Math.max(8, y - h - 14) + "px";
  }
  const ocultarTip = () => tip().classList.remove("visible");
  function conTip(nodo, html) {
    nodo.addEventListener("mousemove", e => mostrarTip(html, e));
    nodo.addEventListener("mouseleave", ocultarTip);
    nodo.addEventListener("touchstart", e => { mostrarTip(html, e); setTimeout(ocultarTip, 1800); }, { passive: true });
  }

  function registrar(cont, fn) { renders.set(cont, fn); fn(); }
  let tmr; window.addEventListener("resize", () => { clearTimeout(tmr); tmr = setTimeout(() => renders.forEach((fn, c) => c.isConnected && c.offsetParent && fn()), 150); });
  function redibujarVisibles() { renders.forEach((fn, c) => c.isConnected && c.offsetParent && fn()); }

  /* ----------------------------- Dona ----------------------------- */
  function dona(cont, datos, centro) {
    registrar(cont, () => {
      cont.innerHTML = "";
      const total = datos.reduce((s, d) => s + d.value, 0) || 1;
      const S = 220, R = 100, r = 64, c = S / 2;
      const svg = el("svg", { viewBox: `0 0 ${S} ${S}`, role: "img" }, cont);
      let a0 = -Math.PI / 2;
      datos.filter(d => d.value > 0).forEach((d, i) => {
        const frac = d.value / total;
        const a1 = a0 + frac * Math.PI * 2 - (frac < 1 ? 0.012 : 0);
        const g = a1 - a0 > Math.PI ? 1 : 0;
        const p = frac >= 0.9999
          ? `M ${c} ${c - R} A ${R} ${R} 0 1 1 ${c - 0.01} ${c - R} L ${c - 0.01} ${c - r} A ${r} ${r} 0 1 0 ${c} ${c - r} Z`
          : `M ${c + R * Math.cos(a0)} ${c + R * Math.sin(a0)} A ${R} ${R} 0 ${g} 1 ${c + R * Math.cos(a1)} ${c + R * Math.sin(a1)}
             L ${c + r * Math.cos(a1)} ${c + r * Math.sin(a1)} A ${r} ${r} 0 ${g} 0 ${c + r * Math.cos(a0)} ${c + r * Math.sin(a0)} Z`;
        const path = el("path", { d: p, fill: d.color, class: "barra", style: `opacity:0;transition:opacity .4s ${i * 0.08}s` }, svg);
        requestAnimationFrame(() => path.style.opacity = 1);
        conTip(path, `<b>${d.label}</b><br>${fmt(d.value)} usuarios · ${fmt(100 * d.value / total, 1)} %`);
        a0 += frac * Math.PI * 2;
      });
      if (centro) {
        el("text", { x: c, y: c - 4, "text-anchor": "middle", style: "font-family:var(--serif);font-size:30px;font-weight:600;fill:var(--tinta)" }, svg).textContent = centro.valor;
        el("text", { x: c, y: c + 18, "text-anchor": "middle", style: "font-size:11px;letter-spacing:.08em;text-transform:uppercase" }, svg).textContent = centro.texto;
      }
      const ley = document.createElement("div");
      ley.className = "leyenda leyenda--vertical";
      ley.innerHTML = datos.map(d => `<span><span><i style="background:${d.color}"></i>${d.label}</span><b>${fmt(100 * d.value / total, 1)} %</b></span>`).join("");
      cont.appendChild(ley);
    });
  }

  /* ----------------------- Barras horizontales ----------------------- */
  function barrasH(cont, datos, { formato = v => fmt(v), maxEtiqueta = 30 } = {}) {
    registrar(cont, () => {
      cont.innerHTML = "";
      if (!datos.length) { cont.innerHTML = '<p class="ayuda">Sin datos.</p>'; return; }
      const W = Math.max(300, cont.clientWidth), fila = 30, izq = Math.min(210, W * 0.42), der = 64;
      const H = datos.length * fila + 6;
      const max = Math.max(...datos.map(d => d.value)) || 1;
      const svg = el("svg", { viewBox: `0 0 ${W} ${H}` }, cont);
      datos.forEach((d, i) => {
        const y = i * fila + 4, w = (W - izq - der) * d.value / max;
        let txt = d.label; if (txt.length > maxEtiqueta * (W / 520)) txt = txt.slice(0, Math.max(10, Math.floor(maxEtiqueta * W / 520))) + "…";
        el("text", { x: izq - 8, y: y + 16, "text-anchor": "end" }, svg).textContent = txt;
        el("rect", { x: izq, y: y + 3, width: W - izq - der, height: fila - 10, rx: 5, fill: "#f3ede1" }, svg);
        const r = el("rect", { x: izq, y: y + 3, width: 0, height: fila - 10, rx: 5, fill: d.color || "var(--vino)", class: "barra", style: "transition:width .7s cubic-bezier(.2,.8,.2,1)" }, svg);
        requestAnimationFrame(() => r.setAttribute("width", Math.max(2, w)));
        el("text", { x: izq + Math.max(2, w) + 6, y: y + 16, style: "font-weight:600;fill:var(--tinta)" }, svg).textContent = formato(d.value);
        conTip(r, d.tooltip || `<b>${d.label}</b><br>${formato(d.value)}`);
      });
    });
  }

  /* ----------------------------- Histograma ----------------------------- */
  function histograma(cont, datos, color = "var(--vino)") {
    registrar(cont, () => {
      cont.innerHTML = "";
      const W = Math.max(300, cont.clientWidth), H = 220, m = { t: 12, r: 10, b: 34, l: 44 };
      const svg = el("svg", { viewBox: `0 0 ${W} ${H}` }, cont);
      const maxP = Math.max(...datos.map(d => d.pasos)), minP = 0;
      const n = maxP - minP + 1;
      const mapa = new Map(datos.map(d => [d.pasos, d.usuarios]));
      const maxU = Math.max(...datos.map(d => d.usuarios)) || 1;
      const bw = (W - m.l - m.r) / n;
      const ticksY = 4;
      for (let k = 0; k <= ticksY; k++) {
        const v = maxU * k / ticksY, y = H - m.b - (H - m.t - m.b) * k / ticksY;
        el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, class: k ? "rejilla-l" : "eje" }, svg);
        el("text", { x: m.l - 6, y: y + 4, "text-anchor": "end" }, svg).textContent = fmt(Math.round(v));
      }
      const salto = Math.ceil(n / Math.floor((W - m.l) / 34));
      for (let p = minP; p <= maxP; p++) {
        const u = mapa.get(p) || 0, h = (H - m.t - m.b) * u / maxU, x = m.l + (p - minP) * bw;
        if (u) {
          const r = el("rect", { x: x + bw * 0.12, y: H - m.b, width: bw * 0.76, height: 0, rx: Math.min(3, bw / 4), fill: color, class: "barra", style: "transition:all .6s cubic-bezier(.2,.8,.2,1)" }, svg);
          requestAnimationFrame(() => { r.setAttribute("y", H - m.b - h); r.setAttribute("height", h); });
          conTip(r, `<b>${p} pasos</b><br>${fmt(u)} usuarios`);
        }
        if ((p - minP) % salto === 0) el("text", { x: x + bw / 2, y: H - m.b + 16, "text-anchor": "middle" }, svg).textContent = p;
      }
      el("text", { x: (W + m.l) / 2, y: H - 2, "text-anchor": "middle", style: "font-size:11px" }, svg).textContent = "Número de pasos hasta terminar";
    });
  }

  /* ----------------------- Barras agrupadas (antes/después) ----------------------- */
  function agrupadas(cont, categorias, series) {
    registrar(cont, () => {
      cont.innerHTML = "";
      const W = Math.max(300, cont.clientWidth), H = 260, m = { t: 22, r: 8, b: 40, l: 38 };
      const svg = el("svg", { viewBox: `0 0 ${W} ${H}` }, cont);
      const max = Math.max(5, ...series.flatMap(s => s.values)) * 1.12;
      for (let k = 0; k <= 4; k++) {
        const v = max * k / 4, y = H - m.b - (H - m.t - m.b) * k / 4;
        el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, class: k ? "rejilla-l" : "eje" }, svg);
        el("text", { x: m.l - 6, y: y + 4, "text-anchor": "end" }, svg).textContent = Math.round(v) + "%";
      }
      const gw = (W - m.l - m.r) / categorias.length, bw = Math.min(46, gw * 0.7 / series.length);
      categorias.forEach((c, i) => {
        const x0 = m.l + i * gw + (gw - bw * series.length) / 2;
        series.forEach((s, k) => {
          const v = s.values[i], h = (H - m.t - m.b) * v / max, x = x0 + k * bw;
          const r = el("rect", { x: x + 2, y: H - m.b, width: bw - 4, height: 0, rx: 4, fill: s.colores ? s.colores[i] : s.color, opacity: s.opacidad || 1, class: "barra", style: "transition:all .7s cubic-bezier(.2,.8,.2,1)" }, svg);
          requestAnimationFrame(() => { r.setAttribute("y", H - m.b - h); r.setAttribute("height", h); });
          conTip(r, `<b>${c.label} · ${s.name}</b><br>${fmt(v, 1)} %`);
          el("text", { x: x + bw / 2, y: H - m.b - h - 5, "text-anchor": "middle", style: "font-size:10.5px;font-weight:600;fill:var(--tinta)" }, svg).textContent = fmt(v, 1);
        });
        el("text", { x: m.l + i * gw + gw / 2, y: H - m.b + 17, "text-anchor": "middle", style: "font-weight:600" }, svg).textContent = c.label;
      });
      const ley = document.createElement("div"); ley.className = "leyenda";
      ley.innerHTML = series.map(s => `<span><i style="background:${s.leyenda || s.color};opacity:${s.opacidad || 1}"></i>${s.name}</span>`).join("");
      cont.appendChild(ley);
    });
  }

  return { dona, barrasH, histograma, agrupadas, conTip, fmt, redibujarVisibles, ocultarTip };
})();
