# -*- coding: utf-8 -*-
"""
generar_informe.py
==================
Genera, con los resultados reales del modelo (semilla 2026):
  * datos/  -> estados, recorridos y matrices en CSV y Excel
  * documento/graficas/ -> gráficas PNG
  * documento/Informe_Proyecto_Integrador_Santo_Domingo.docx

Requiere (solo para este script, NO para el servidor):  pip install python-docx matplotlib openpyxl
Uso:  python herramientas/generar_informe.py
"""
import csv
import os
import sys
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from markov.modelo import ESTADOS, RECORRIDOS, RECOMENDACIONES, tipos_de_usuario
from markov.cadena import (matriz_conteos, matriz_probabilidades, simular, analisis_teorico, comparar_mejora,
                           validar_modelo, CODIGOS, NOMBRES, TIPOS, ETIQUETAS, categoria)

SEMILLA, USUARIOS, PASOS, REDUCCION = 2026, 1000, 50, 0.5
DATOS = os.path.join(RAIZ, "datos")
DOC = os.path.join(RAIZ, "documento")
GRAF = os.path.join(DOC, "graficas")
CAPTURAS = os.path.join(DOC, "capturas")
for d in (DATOS, DOC, GRAF):
    os.makedirs(d, exist_ok=True)

COLOR = {"exito": "#2f7d5b", "abandono": "#a3283a", "error": "#d27a1f", "seguimiento": "#3a6ea5", "incompleto": "#8f877b"}
VINO, ORO = "#6b1d2a", "#b8893b"
CATS = ["exito", "abandono", "error", "seguimiento"]

# ----------------------------------------------------------------------------- cálculos
C = matriz_conteos()
P = matriz_probabilidades(C)
VAL = validar_modelo()
SIM = simular(USUARIOS, PASOS, SEMILLA, vista_previa=15)
SIM10K = simular(10000, PASOS, SEMILLA, vista_previa=0)
TEO = analisis_teorico(P)
CRIT = SIM["estado_critico"]
MEJ = comparar_mejora(CRIT["estado"], REDUCCION, USUARIOS, PASOS, SEMILLA)
pct = lambda v: f"{v:.1f} %".replace(".", ",")
num = lambda v, d=2: f"{v:.{d}f}".replace(".", ",")

# ----------------------------------------------------------------------------- datos CSV y Excel
def escribir_csv(nombre, filas):
    with open(os.path.join(DATOS, nombre), "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f, delimiter=";").writerows(filas)

f_estados = [["Código", "Nombre", "Descripción", "Tipo", "Sección del sitio"]] + [list(e) for e in ESTADOS]
f_rec = [["#", "Tipo de usuario", "Descripción", "Recorrido", "Pasos", "Resultado"]] + [
    [r["id"], r["tipo_usuario"], r["descripcion"], " → ".join(CODIGOS[s] for s in r["estados"]), len(r["estados"]) - 1,
     ETIQUETAS[categoria(r["estados"][-1])]] for r in RECORRIDOS]
f_c = [[""] + CODIGOS] + [[CODIGOS[i]] + fila for i, fila in enumerate(C)]
f_p = [[""] + CODIGOS] + [[CODIGOS[i]] + [round(p, 4) for p in fila] for i, fila in enumerate(P)]
escribir_csv("estados.csv", f_estados)
escribir_csv("recorridos.csv", f_rec)
escribir_csv("matriz_conteos.csv", f_c)
escribir_csv("matriz_probabilidades.csv", [f_p[0]] + [[f[0]] + [str(v).replace(".", ",") for v in f[1:]] for f in f_p[1:]])

wb = Workbook()
cab = Font(bold=True, color="FFFFFF"); relleno = PatternFill("solid", fgColor="6B1D2A")
for idx, (titulo, filas) in enumerate([("Estados", f_estados), ("Recorridos", f_rec), ("Matriz de conteos", f_c), ("Matriz de probabilidades", f_p)]):
    ws = wb.active if idx == 0 else wb.create_sheet()
    ws.title = titulo
    for fila in filas:
        ws.append(fila)
    for c in ws[1]:
        c.font, c.fill = cab, relleno
    if titulo.startswith("Matriz"):
        for fila in ws.iter_rows(min_row=2, max_col=1):
            for c in fila:
                c.font, c.fill = cab, relleno
        for col in ws.iter_cols(min_col=2):
            ws.column_dimensions[col[0].column_letter].width = 7
            for c in col[1:]:
                c.alignment = Alignment(horizontal="center")
                if titulo.endswith("probabilidades"):
                    c.number_format = "0.000"
        ws.freeze_panes = "B2"
    else:
        for col, w in zip("ABCDEF", (8, 34, 70, 60, 10, 22) if titulo == "Recorridos" else (8, 36, 90, 16, 26)):
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "A2"
wb.save(os.path.join(DATOS, "modelo_markov_santo_domingo.xlsx"))

# ----------------------------------------------------------------------------- gráficas
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#cfc5b3", "axes.labelcolor": "#4a443c", "xtick.color": "#4a443c", "ytick.color": "#4a443c"})

def guardar(fig, nombre):
    ruta = os.path.join(GRAF, nombre)
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta

# 1. Dona de resultados
fig, ax = plt.subplots(figsize=(6.4, 3.6))
vals = [SIM["conteos"][c] for c in CATS]
w, _ = ax.pie(vals, colors=[COLOR[c] for c in CATS], startangle=90, counterclock=False, wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2))
ax.text(0, 0.05, f"{USUARIOS:,}".replace(",", "."), ha="center", va="center", fontsize=20, fontweight="bold", color="#26211c")
ax.text(0, -0.2, "usuarios", ha="center", va="center", fontsize=9, color="#5f574d")
ax.legend(w, [f"{ETIQUETAS[c]}: {pct(SIM['porcentajes'][c])}" for c in CATS], loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
ax.set_title("Resultado final de los usuarios simulados", fontsize=11, fontweight="bold", color="#26211c")
G_DONA = guardar(fig, "1_resultados.png")

# 2. Pérdidas por estado
top = SIM["perdidas"][:10][::-1]
fig, ax = plt.subplots(figsize=(7, 4))
ax.barh([f"{p['codigo']} {p['nombre'][:32]}" for p in top], [p["abandono"] for p in top], color=COLOR["abandono"], label="Abandono")
ax.barh([f"{p['codigo']} {p['nombre'][:32]}" for p in top], [p["error"] for p in top], left=[p["abandono"] for p in top], color=COLOR["error"], label="Error")
for i, p in enumerate(top):
    ax.text(p["total"] + 1, i, str(p["total"]), va="center", fontsize=9, fontweight="bold")
ax.set_xlabel("Usuarios perdidos justo después de este estado")
ax.set_title("¿Dónde se pierden los usuarios? (top 10)", fontsize=11, fontweight="bold")
ax.legend(frameon=False, loc="lower right")
G_PERD = guardar(fig, "2_perdidas_por_estado.png")

# 3. Estados finales
fin = sorted([f for f in SIM["finales"] if f["usuarios"]], key=lambda f: f["usuarios"])
fig, ax = plt.subplots(figsize=(7, 4))
ax.barh([f"{f['codigo']} {f['nombre'][:34]}" for f in fin], [f["usuarios"] for f in fin], color=[COLOR[f["categoria"]] for f in fin])
for i, f in enumerate(fin):
    ax.text(f["usuarios"] + 2, i, f"{f['usuarios']} ({pct(f['porcentaje'])})", va="center", fontsize=8.5)
ax.set_title("Usuarios por estado final", fontsize=11, fontweight="bold")
ax.set_xlim(0, max(f["usuarios"] for f in fin) * 1.22)
G_FIN = guardar(fig, "3_estados_finales.png")

# 4. Histograma de pasos
fig, ax = plt.subplots(figsize=(7, 3.2))
h = SIM["histograma_pasos"]
ax.bar([x["pasos"] for x in h], [x["usuarios"] for x in h], color=VINO, width=0.75)
ax.axvline(SIM["pasos"]["promedio"], color=ORO, linestyle="--", linewidth=2, label=f"Promedio = {num(SIM['pasos']['promedio'])} pasos")
ax.set_xlabel("Número de pasos hasta terminar"); ax.set_ylabel("Usuarios")
ax.set_title("Distribución de pasos por usuario", fontsize=11, fontweight="bold")
ax.legend(frameon=False)
G_HIST = guardar(fig, "4_histograma_pasos.png")

# 5. Comparación de mejora
fig, ax = plt.subplots(figsize=(7, 3.6))
x = range(len(CATS)); bw = 0.36
antes = [MEJ["base"]["porcentajes"][c] for c in CATS]; desp = [MEJ["mejorado"]["porcentajes"][c] for c in CATS]
b1 = ax.bar([i - bw / 2 for i in x], antes, bw, color=[COLOR[c] for c in CATS], alpha=0.4, label="Antes")
b2 = ax.bar([i + bw / 2 for i in x], desp, bw, color=[COLOR[c] for c in CATS], label="Después de la mejora")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.6, num(b.get_height(), 1), ha="center", fontsize=8.5)
ax.set_xticks(list(x)); ax.set_xticklabels([ETIQUETAS[c].replace(" pendiente", "") for c in CATS])
ax.set_ylabel("% de usuarios")
ax.set_title(f"Antes vs. después de mejorar {MEJ['estado']['codigo']} (reducción {int(REDUCCION*100)} %)", fontsize=11, fontweight="bold")
ax.legend(frameon=False)
G_MEJ = guardar(fig, "5_mejora_antes_despues.png")

# 6 y 7. Mapas de calor de las matrices
cmap = LinearSegmentedColormap.from_list("vino", ["#ffffff", "#f1dcc4", "#c7795f", VINO])
for nombre, M, titulo in (("6_matriz_conteos.png", C, "Matriz de conteos"), ("7_matriz_probabilidades.png", P, "Matriz de probabilidades (transición)")):
    fig, ax = plt.subplots(figsize=(10, 9.4))
    im = ax.imshow(M, cmap=cmap, aspect="equal")
    ax.set_xticks(range(len(CODIGOS))); ax.set_xticklabels(CODIGOS, rotation=90, fontsize=6.5)
    ax.set_yticks(range(len(CODIGOS))); ax.set_yticklabels(CODIGOS, fontsize=6.5)
    ax.set_xlabel("Estado destino (j)"); ax.set_ylabel("Estado origen (i)")
    for i in range(len(M)):
        for j in range(len(M)):
            v = M[i][j]
            if v:
                t = str(v) if isinstance(v, int) else f"{v:.2f}"[1:] if v < 1 else "1"
                ax.text(j, i, t, ha="center", va="center", fontsize=4.6, color="white" if (v / (max(map(max, M)))) > 0.45 else "#26211c")
    ax.set_title(titulo, fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    if nombre.startswith("6"):
        G_MC = guardar(fig, nombre)
    else:
        G_MP = guardar(fig, nombre)

# ----------------------------------------------------------------------------- documento Word
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
for m in ("left_margin", "right_margin"):
    setattr(sec, m, Cm(2.3))
sec.top_margin = sec.bottom_margin = Cm(2.2)

estilos = doc.styles
estilos["Normal"].font.name = "Calibri"; estilos["Normal"].font.size = Pt(11)
estilos["Normal"].element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
estilos["Normal"].paragraph_format.space_after = Pt(6)
for nivel, tam, color in ((1, 16, VINO), (2, 13, "#26211c"), (3, 11.5, VINO)):
    st = estilos[f"Heading {nivel}"]
    st.font.name = "Cambria"; st.font.size = Pt(tam); st.font.bold = True
    st.font.color.rgb = RGBColor.from_string(color[1:])
    st.element.rPr.rFonts.set(qn("w:asciiTheme"), "") if False else None
    rf = st.element.rPr.rFonts; rf.set(qn("w:ascii"), "Cambria"); rf.set(qn("w:hAnsi"), "Cambria")
    for a in list(rf.attrib):
        if "Theme" in a:
            del rf.attrib[a]
    st.paragraph_format.space_before = Pt(14 if nivel == 1 else 10)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.keep_with_next = True


def sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), color)
    tcPr.append(sh)


def repetir_encabezado(fila):
    trPr = fila._tr.get_or_add_trPr()
    e = OxmlElement("w:tblHeader"); e.set(qn("w:val"), "true"); trPr.append(e)


def tabla(encabezados, filas, anchos, tam=9, colores_fila=None):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    for i, h in enumerate(encabezados):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(tam); r.font.color.rgb = RGBColor(255, 255, 255)
        sombrear(c, "6B1D2A")
    repetir_encabezado(t.rows[0])
    for k, fila in enumerate(filas):
        celdas = t.add_row().cells
        for i, v in enumerate(fila):
            celdas[i].text = ""
            p = celdas[i].paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(v)); r.font.size = Pt(tam)
            if i == 0:
                r.bold = True
            if colores_fila and colores_fila[k]:
                sombrear(celdas[i], colores_fila[k])
            elif k % 2:
                sombrear(celdas[i], "F7F1E6")
    for i, w in enumerate(anchos):
        t.columns[i].width = Cm(w)
    for fila in t.rows:
        for i, w in enumerate(anchos):
            fila.cells[i].width = Cm(w)
    # ancho total fijo y diseño "fixed" para que Word, LibreOffice y Google Docs respeten las columnas
    tblPr = t._tbl.tblPr
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(int(sum(anchos) * 567))); tw.set(qn("w:type"), "dxa")
    for viejo in tblPr.findall(qn("w:tblW")):
        tblPr.remove(viejo)
    tblPr.append(tw)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def parrafo(texto, negrita_inicio=None, tam=None, alin=None, cursiva=False):
    p = doc.add_paragraph()
    if negrita_inicio:
        p.add_run(negrita_inicio).bold = True
    r = p.add_run(texto); r.italic = cursiva
    if tam:
        for run in p.runs:
            run.font.size = Pt(tam)
    if alin:
        p.alignment = alin
    return p


def vinetas(items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True; p.add_run(it[1])
        else:
            p.add_run(it)


def imagen(ruta, ancho_cm, pie):
    doc.add_picture(ruta, width=Cm(ancho_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(pie); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x5F, 0x57, 0x4D)


COLOR_FILA = {"final exitoso": "E3F2EA", "final negativo": "F8E3E6", "error": "FBEBD8", "seguimiento": "E2ECF7", "inicial": "ECE6F5"}

# --- Portada
for _ in range(4):
    doc.add_paragraph()
p = parrafo("PROYECTO INTEGRADOR · SIMULACIÓN", alin=WD_ALIGN_PARAGRAPH.CENTER)
p.runs[0].font.color.rgb = RGBColor.from_string("B8893B"); p.runs[0].bold = True; p.runs[0].font.size = Pt(11)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Simulación con cadenas de Márkov aplicada a la página web de la Iglesia de Santo Domingo")
r.font.name = "Cambria"; r.font.size = Pt(24); r.bold = True; r.font.color.rgb = RGBColor.from_string("6B1D2A")
p = parrafo("Modelo de navegación de usuarios en museosantodomingo.netlify.app — Tunja, Boyacá", alin=WD_ALIGN_PARAGRAPH.CENTER, tam=12.5, cursiva=True)
for _ in range(3):
    doc.add_paragraph()
datos_portada = [("Integrantes:", "______________________________"), ("", "______________________________"), ("", "______________________________"),
                 ("Grupo / curso:", "______________________________"), ("Docente:", "______________________________"),
                 ("Fecha:", "Noviembre de 2026")]
for a, b in datos_portada:
    p = parrafo(b, negrita_inicio=(a + " ") if a else None, alin=WD_ALIGN_PARAGRAPH.CENTER, tam=12)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# --- 1. Caso elegido
doc.add_heading("1. Caso elegido", 1)
parrafo("Flujo modelado: ", negrita_inicio=None)
doc.paragraphs[-1].runs[0].bold = True
doc.paragraphs[-1].add_run("Navegación de un visitante por el sitio web de la Iglesia de Santo Domingo y del Museo Virtual de la Capilla del Rosario "
                           "(https://museosantodomingo.netlify.app/), desde que abre el sitio hasta que cumple su objetivo, abandona, encuentra un error "
                           "o queda con un seguimiento pendiente.")
parrafo("El modelo se construyó recorriendo el sitio real. Su menú tiene las secciones Inicio, La Iglesia, Historia, Patrimonio, Capilla del Rosario, "
        "Museo Virtual, Galería, Actualidad, Visita, Agenda y Contacto, además de un buscador, un selector de idioma, filtros en Galería y Agenda, "
        "un formulario de contacto y el botón «Iniciar recorrido virtual». Durante la revisión se observaron tres hechos que el modelo incorpora "
        "porque afectan directamente el comportamiento de las personas:")
vinetas([
    ("Contenido «por confirmar». ", "Horarios, dirección, teléfono, fechas de la agenda, fichas de piezas y la línea de tiempo de Historia muestran "
     "«Información por confirmar» o «Contenido en construcción» (estado S31)."),
    ("Recorrido 3D no disponible. ", "El botón del Museo Virtual no abre ninguna experiencia: «Experiencia 3D interactiva – Próximamente» (estado S34)."),
    ("Error 404 al abrir o recargar sub-páginas. ", "Al abrir directamente https://museosantodomingo.netlify.app/historia (el enlace de la ficha técnica) "
     "Netlify responde «Page not found». Lo mismo ocurre al recargar cualquier sección (estado S33)."),
])
parrafo("Se definieron 8 tipos de usuario: " + ", ".join(tipos_de_usuario()) + ". Cada uno tiene objetivos y comportamientos distintos "
        "(explorar, dudar, volver atrás, corregir formularios, abandonar o completar el proceso).")

# --- 2. Estados
doc.add_heading("2. Estados del modelo", 1)
cont_tipo = Counter(TIPOS)
parrafo(f"Se definieron {len(ESTADOS)} estados (S0 a S{len(ESTADOS)-1}): " +
        ", ".join(f"{v} {k}" for k, v in cont_tipo.items()) + ". Los estados finales son absorbentes: una vez alcanzados, el usuario termina.")
tabla(["Código", "Nombre", "Descripción", "Tipo"],
      [[c, n, d, t] for c, n, d, t, s in ESTADOS], [1.5, 4.2, 8.4, 2.6], tam=8.5,
      colores_fila=[COLOR_FILA.get(e[3]) for e in ESTADOS])

# --- 3. Recorridos
doc.add_heading("3. Recorridos de usuarios", 1)
res_rec = Counter(categoria(r["estados"][-1]) for r in RECORRIDOS)
parrafo(f"Se construyeron {len(RECORRIDOS)} recorridos distintos (mínimo exigido: 60). Todos inician en S0 y terminan en un estado final. "
        f"Incluyen idas y vueltas, dudas, correcciones de formulario y repeticiones (por ejemplo, abrir y cerrar varias fotos). Por resultado: " +
        ", ".join(f"{res_rec[c]} de {ETIQUETAS[c].lower()}" for c in CATS) + ".")
por_tipo = defaultdict(Counter)
for r in RECORRIDOS:
    por_tipo[r["tipo_usuario"]][categoria(r["estados"][-1])] += 1
tabla(["Tipo de usuario", "Recorridos", "Éxito", "Abandono", "Error", "Seguimiento"],
      [[t, sum(por_tipo[t].values())] + [por_tipo[t][c] for c in CATS] for t in tipos_de_usuario()] +
      [["Total", len(RECORRIDOS)] + [res_rec[c] for c in CATS]], [4.6, 2.4, 2.2, 2.4, 2.2, 2.9], tam=9)
doc.add_heading("Listado completo de recorridos", 3)
tabla(["#", "Tipo de usuario", "Descripción", "Recorrido", "Resultado"],
      [[r["id"], r["tipo_usuario"], r["descripcion"], " → ".join(CODIGOS[s] for s in r["estados"]), ETIQUETAS[categoria(r["estados"][-1])]]
       for r in RECORRIDOS], [0.9, 2.5, 4.6, 6.4, 2.3], tam=7.5,
      colores_fila=[COLOR_FILA.get(TIPOS[r["estados"][-1]]) for r in RECORRIDOS])

# --- 4. Matrices
doc.add_heading("4. Matriz de conteos y matriz de probabilidades", 1)
total_tr = sum(map(sum, C))
parrafo(f"La matriz de conteos C (43 × 43) registra cuántas veces, en los recorridos base, un usuario pasa del estado i al estado j. "
        f"En total se contaron {total_tr} transiciones. La matriz de transición se obtiene dividiendo cada fila por su total:")
p = parrafo("P[i][j] = C[i][j] / Σⱼ C[i][j]", alin=WD_ALIGN_PARAGRAPH.CENTER); p.runs[0].bold = True; p.runs[0].font.size = Pt(12)
parrafo("Cada fila de P suma 1. Para los estados finales (S33 a S42) se define P[f][f] = 1, es decir, son estados absorbentes. "
        "Ambas matrices completas se calculan en Python (markov/cadena.py), se muestran en la pestaña «Matrices» de la aplicación y se entregan "
        "en la carpeta datos/ en formato CSV y Excel. A continuación se presentan como mapas de calor y como lista de transiciones distintas de cero.")
imagen(G_MC, 15.5, "Figura 1. Matriz de conteos (filas: origen, columnas: destino).")
imagen(G_MP, 15.5, "Figura 2. Matriz de probabilidades de transición.")
doc.add_heading("Transiciones distintas de cero", 3)
filas_t = []
for i in range(len(C)):
    tot = sum(C[i])
    for j in range(len(C)):
        if C[i][j]:
            filas_t.append([CODIGOS[i], NOMBRES[i], CODIGOS[j], NOMBRES[j], C[i][j], f"{C[i][j]}/{tot}", num(P[i][j], 4)])
tabla(["Origen", "Nombre origen", "Destino", "Nombre destino", "Conteo", "Fracción", "Probabilidad"], filas_t,
      [1.3, 4.1, 1.4, 4.4, 1.4, 1.6, 2.0], tam=7.5)

# --- 5. Simulación
doc.add_heading("5. Simulación", 1)
parrafo(f"Se simularon {USUARIOS:,} usuarios".replace(",", ".") + f" con un máximo de {PASOS} pasos por usuario y semilla aleatoria {SEMILLA} "
        "(la misma semilla reproduce exactamente estos resultados en la aplicación). Cada usuario inicia en S0 y en cada paso elige el siguiente "
        "estado al azar según las probabilidades de su fila en P, hasta llegar a un estado final o agotar los pasos.")
doc.add_heading("Vista previa de usuarios simulados", 3)
tabla(["Usuario", "Recorrido simulado", "Pasos", "Resultado"],
      [[u["usuario"], " → ".join(CODIGOS[s] for s in u["camino"]), u["pasos"], ETIQUETAS[u["resultado"]]] for u in SIM["vista_previa"]],
      [1.6, 10.6, 1.4, 3.1], tam=8.5)

# --- 6. Resultados
doc.add_heading("6. Resultados", 1)
filas_r = [[ETIQUETAS[c], SIM["conteos"][c], pct(SIM["porcentajes"][c]), pct(SIM10K["porcentajes"][c]), pct(TEO["porcentajes"][c])] for c in CATS]
filas_r.append(["Sin terminar (límite de pasos)", SIM["conteos"]["incompleto"], pct(SIM["porcentajes"]["incompleto"]), pct(SIM10K["porcentajes"]["incompleto"]), "—"])
filas_r.append(["Promedio de pasos", "—", num(SIM["pasos"]["promedio"]), num(SIM10K["pasos"]["promedio"]), num(TEO["pasos_esperados"])])
tabla(["Indicador", "Usuarios (1.000)", "% con 1.000", "% con 10.000", "Teórico exacto"], filas_r, [5.4, 2.8, 2.6, 2.8, 3.0], tam=9.5)
parrafo("La columna «Teórico exacto» se calcula con la matriz fundamental N = (I − Q)⁻¹ y B = N·R, donde Q contiene las transiciones entre estados "
        "no finales y R las transiciones hacia los estados finales. Los resultados simulados se acercan al valor teórico a medida que aumenta el "
        "número de usuarios, lo que valida la simulación.", tam=10)
imagen(G_DONA, 13.5, "Figura 3. Porcentaje de éxito, abandono, error y seguimiento pendiente (1.000 usuarios).")
imagen(G_FIN, 14.5, "Figura 4. Usuarios por estado final.")
imagen(G_HIST, 14.5, f"Figura 5. Distribución de pasos (promedio {num(SIM['pasos']['promedio'])}, mediana {num(SIM['pasos']['mediana'], 0)}, máximo {SIM['pasos']['maximo']}).")
doc.add_heading("Estado más crítico", 2)
parrafo(f"{CRIT['codigo']} – {CRIT['nombre']}. ", negrita_inicio=None)
doc.paragraphs[-1].runs[0].bold = True
doc.paragraphs[-1].add_run(f"Es el estado desde el cual se pierden más usuarios: {CRIT['total']} personas ({CRIT['abandono']} abandonos y {CRIT['error']} errores), "
                           f"el {pct(CRIT['porcentaje_de_perdidas'])} de todas las pérdidas. De quienes pasan por este estado, el {pct(CRIT['tasa'])} se pierde.")
imagen(G_PERD, 14.5, "Figura 6. Estados desde los que se producen los abandonos y errores.")
tabla(["Estado", "Nombre", "Abandonos", "Errores", "Total", "Pasaron por aquí", "Tasa de pérdida"],
      [[p["codigo"], p["nombre"], p["abandono"], p["error"], p["total"], p["visitas"], pct(p["tasa"])] for p in SIM["perdidas"][:10]],
      [1.4, 5.6, 1.8, 1.6, 1.4, 2.4, 2.4], tam=8.5)

# --- 7. Mejora
doc.add_heading("7. Propuesta de mejora", 1)
parrafo(RECOMENDACIONES.get(CRIT["estado"], ""), negrita_inicio="Mejora propuesta: ")
parrafo(f"Para medir su efecto se modificó la fila de {CRIT['codigo']} en la matriz de transición: la probabilidad de pasar a abandono o error se redujo "
        f"en {int(REDUCCION*100)} % y esa probabilidad se trasladó hacia el objetivo del usuario (estado de éxito de esa fila). Luego se volvió a simular "
        f"con los mismos {USUARIOS:,} usuarios y la misma semilla.".replace(",", "."))
tabla(["Destino desde " + MEJ["estado"]["codigo"], "Antes", "Después"],
      [[f"{f['destino']} {f['nombre']}", num(f["antes"], 4), num(f["despues"], 4)] for f in MEJ["fila"]], [9.5, 3.5, 3.5], tam=9)
tabla(["Resultado", "Antes (sim.)", "Después (sim.)", "Cambio", "Antes (teórico)", "Después (teórico)"],
      [[ETIQUETAS[c], pct(MEJ["base"]["porcentajes"][c]), pct(MEJ["mejorado"]["porcentajes"][c]),
        f"{MEJ['mejorado']['porcentajes'][c]-MEJ['base']['porcentajes'][c]:+.1f} pp".replace(".", ","),
        pct(MEJ["teorico_base"][c]), pct(MEJ["teorico_mejorado"][c])] for c in CATS], [3.8, 2.4, 2.6, 2.2, 2.7, 2.9], tam=9)
imagen(G_MEJ, 14.5, "Figura 7. Comparación de resultados antes y después de la mejora.")

# --- 8. Preguntas
doc.add_heading("8. Preguntas de análisis", 1)
orden = sorted(CATS, key=lambda c: -SIM["porcentajes"][c])
seg = SIM["perdidas"][1]
riesgo = SIM["estado_mayor_riesgo"]
d = lambda c: MEJ["mejorado"]["porcentajes"][c] - MEJ["base"]["porcentajes"][c]
nuevo_crit = MEJ["mejorado"]["estado_critico"]
preguntas = [
    ("1. ¿Cuál fue el resultado final más frecuente en su simulación: éxito, abandono o error?",
     f"El resultado más frecuente fue el {ETIQUETAS[orden[0]].lower()}, con {pct(SIM['porcentajes'][orden[0]])} de los {USUARIOS:,} usuarios. ".replace(",", ".") +
     f"Le siguen {ETIQUETAS[orden[1]].lower()} ({pct(SIM['porcentajes'][orden[1]])}), {ETIQUETAS[orden[2]].lower()} ({pct(SIM['porcentajes'][orden[2]])}) y "
     f"{ETIQUETAS[orden[3]].lower()} ({pct(SIM['porcentajes'][orden[3]])}). Aunque el éxito es el resultado individual más frecuente, no alcanza la mitad: "
     f"sumando abandono y error, {pct(SIM['porcentajes']['abandono'] + SIM['porcentajes']['error'])} de las personas no logra su objetivo. "
     f"Con 10.000 usuarios el orden se mantiene (éxito {pct(SIM10K['porcentajes']['exito'])}, abandono {pct(SIM10K['porcentajes']['abandono'])}), y el valor "
     f"teórico exacto es {pct(TEO['porcentajes']['exito'])} de éxito."),
    ("2. ¿En qué estado o paso del recorrido se están perdiendo más usuarios?",
     f"En {CRIT['codigo']} – {CRIT['nombre']}. Desde ese estado se perdieron {CRIT['total']} usuarios, el {pct(CRIT['porcentaje_de_perdidas'])} de todas las pérdidas. "
     f"Le siguen {seg['codigo']} – {seg['nombre']} ({seg['total']} usuarios, sobre todo personas que ven el inicio y se van) y los puntos de error: "
     f"S14 (el recorrido 3D no abre), S29 (el formulario no envía el mensaje) y S30 (recargar produce error 404)."),
    ("3. ¿Qué estado consideran más crítico para mejorar la experiencia del usuario? ¿Por qué?",
     f"{CRIT['codigo']} – {CRIT['nombre']}. Es el más crítico por tres razones: (a) concentra la mayor cantidad de pérdidas; (b) tiene una tasa de pérdida alta: "
     f"{pct(CRIT['tasa'])} de quienes llegan allí abandonan; y (c) es transversal: aparece en Visita, Agenda, Historia, Patrimonio, Contacto y Museo Virtual, "
     f"así que afecta a casi todos los tipos de usuario. Una persona que busca el horario de misa o la dirección para visitar y encuentra «por confirmar» "
     f"no tiene motivo para seguir navegando." + (f" Por tasa, el estado más riesgoso es {riesgo['codigo']} – {riesgo['nombre']} ({pct(riesgo['tasa'])}), "
     f"pero por él pasan pocos usuarios, por lo que su impacto total es menor." if riesgo and riesgo["codigo"] != CRIT["codigo"] else "")),
    ("4. ¿Qué cambio harían primero en el flujo de la aplicación para aumentar la probabilidad de éxito?",
     RECOMENDACIONES.get(CRIT["estado"], "") + " En concreto: publicar la dirección exacta con mapa, los horarios de apertura, de misas y de visitas guiadas, "
     "las fechas reales de la agenda, el teléfono y el correo. Como segundo y tercer cambio, de bajo costo: configurar en Netlify el archivo "
     "_redirects («/*  /index.html  200») para eliminar el error 404, y conectar el formulario de contacto a un servicio real (por ejemplo Netlify Forms)."),
    ("5. ¿Qué pasaría con los resultados si mejoran el estado donde más usuarios abandonan?",
     f"Al reducir en {int(REDUCCION*100)} % las salidas a abandono desde {CRIT['codigo']}, los usuarios que antes se iban encuentran la información y terminan "
     f"su objetivo. En la simulación el éxito sube de {pct(MEJ['base']['porcentajes']['exito'])} a {pct(MEJ['mejorado']['porcentajes']['exito'])} "
     f"({d('exito'):+.1f} puntos porcentuales) y el abandono baja de {pct(MEJ['base']['porcentajes']['abandono'])} a {pct(MEJ['mejorado']['porcentajes']['abandono'])}. ".replace("+", "+") +
     f"El error no cambia porque los errores provienen de otros estados (S14, S29, S30). Después de la mejora, el estado crítico pasa a ser "
     f"{nuevo_crit['codigo']} – {nuevo_crit['nombre']}, lo que indica el siguiente punto a trabajar."),
    ("6. ¿Cómo cambiarían los porcentajes de éxito, abandono y error después de aplicar la mejora propuesta?",
     f"Simulación con la misma semilla: éxito {pct(MEJ['base']['porcentajes']['exito'])} → {pct(MEJ['mejorado']['porcentajes']['exito'])}, "
     f"abandono {pct(MEJ['base']['porcentajes']['abandono'])} → {pct(MEJ['mejorado']['porcentajes']['abandono'])}, "
     f"error {pct(MEJ['base']['porcentajes']['error'])} → {pct(MEJ['mejorado']['porcentajes']['error'])} y seguimiento "
     f"{pct(MEJ['base']['porcentajes']['seguimiento'])} → {pct(MEJ['mejorado']['porcentajes']['seguimiento'])}. Con el cálculo teórico exacto: éxito "
     f"{pct(MEJ['teorico_base']['exito'])} → {pct(MEJ['teorico_mejorado']['exito'])}, abandono {pct(MEJ['teorico_base']['abandono'])} → "
     f"{pct(MEJ['teorico_mejorado']['abandono'])} y error {pct(MEJ['teorico_base']['error'])} → {pct(MEJ['teorico_mejorado']['error'])}. "
     "Si además se eliminan el error 404 y el fallo del formulario, el porcentaje de error también bajaría; la aplicación permite probar cada mejora "
     "por separado en la pestaña «Mejora y análisis»."),
]
for q, a in preguntas:
    doc.add_heading(q, 3)
    doc.add_paragraph(a.replace("+-", "-"))

# --- 9. Implementación
doc.add_heading("9. Implementación en Python y aplicación web", 1)
parrafo("El modelo está implementado en Python y se presenta en una aplicación web hecha con Flask. El PC funciona como servidor y cualquier "
        "celular o computador conectado a la misma red Wi-Fi puede abrirla con la dirección que se muestra al iniciar (http://IP-del-PC:5000).")
vinetas([
    ("markov/modelo.py: ", "43 estados y 74 recorridos base."),
    ("markov/cadena.py: ", "matriz de conteos, matriz de probabilidades, simulación, estado crítico, matriz fundamental y escenario de mejora."),
    ("app.py: ", "servidor Flask; permite elegir de 10 a 10.000 usuarios y de 3 a 200 pasos máximos, y exporta resultados en CSV."),
    ("templates/ y static/: ", "interfaz adaptable a celular con pestañas de Simulación, Estados, Recorridos, Matrices y Mejora; gráficas propias en SVG que funcionan sin internet."),
    ("simulacion_consola.py: ", "la misma simulación en consola, útil para Google Colab."),
])
for ruta, ancho, pie in ((os.path.join(CAPTURAS, "pc_simulacion.png"), 15.5, "Figura 8. Pestaña de simulación en el computador."),
                         (os.path.join(CAPTURAS, "pc_matrices.png"), 15.5, "Figura 9. Pestaña de matrices."),
                         (os.path.join(CAPTURAS, "pc_mejora.png"), 15.5, "Figura 10. Interfaz de mejora."),
                         (os.path.join(CAPTURAS, "celular_simulacion.png"), 6.5, "Figura 11. La aplicación vista desde un celular.")):
    if os.path.exists(ruta):
        imagen(ruta, ancho, pie)

# --- 10. Conclusiones
doc.add_heading("10. Conclusiones", 1)
vinetas([
    f"El sitio cumple el objetivo de {pct(TEO['porcentajes']['exito'])} de los visitantes (valor teórico), pero cerca de la mitad termina en abandono o error.",
    f"El principal problema no es técnico sino de contenido: el estado {CRIT['codigo']} (información «por confirmar») es el punto donde más usuarios se pierden.",
    "Los errores provienen de tres fallas concretas del sitio: el recorrido 3D aún no existe, el formulario de contacto no envía mensajes y las sub-páginas dan error 404 al recargarse.",
    "Las cadenas de Márkov permiten cuantificar el efecto de cada mejora antes de implementarla: reducir a la mitad el abandono en el estado crítico aumenta el éxito "
    f"en {MEJ['teorico_mejorado']['exito'] - MEJ['teorico_base']['exito']:.1f} puntos porcentuales según el cálculo teórico.".replace(".", ",", 1) if False else
    f"Las cadenas de Márkov permiten cuantificar el efecto de cada mejora antes de implementarla: reducir a la mitad el abandono en el estado crítico aumenta el éxito "
    f"en {num(MEJ['teorico_mejorado']['exito'] - MEJ['teorico_base']['exito'], 1)} puntos porcentuales según el cálculo teórico.",
    "La simulación converge al valor teórico al aumentar el número de usuarios, lo que confirma que el modelo está bien implementado.",
])

# Pie de página con número
for s in doc.sections:
    p = s.footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Proyecto Integrador · Cadenas de Márkov · Iglesia de Santo Domingo — pág. "); r.font.size = Pt(8)
    for tipo, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        run = p.add_run(); run.font.size = Pt(8)
        if tipo:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tipo); run._r.append(fc)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; run._r.append(it)

salida = os.path.join(DOC, "Informe_Proyecto_Integrador_Santo_Domingo.docx")
doc.save(salida)
print("Validación:", VAL)
print("Informe:", salida)
print("Resultados 1000:", SIM["porcentajes"], "crítico", CRIT["codigo"])
