# -*- coding: utf-8 -*-
"""
cadena.py
=========
Lógica de la cadena de Márkov:

  1. matriz_conteos()        -> cuenta cuántas veces se pasa del estado i al estado j en los recorridos base.
  2. matriz_probabilidades() -> divide cada fila por su total (matriz de transición P).
                                Los estados finales son ABSORBENTES: P[f][f] = 1.
  3. simular()               -> simula N usuarios (10 a 10 000) con un máximo de pasos por usuario.
  4. analisis_teorico()      -> probabilidades exactas de absorción con la matriz fundamental N = (I - Q)^-1.
  5. aplicar_mejora()        -> modifica la fila de un estado (el crítico) para reducir el abandono/error
                                y permite comparar "antes vs. después".

Solo usa la biblioteca estándar de Python, así el servidor únicamente necesita Flask.
"""
import random
import statistics
from bisect import bisect_left
from collections import Counter

from .modelo import (ESTADOS, RECORRIDOS, CATEGORIA_POR_TIPO, RECOMENDACIONES,
                     RECOMENDACION_GENERAL, EXITO, NEGATIVO, ERROR, SEGUIMIENTO)

N_ESTADOS = len(ESTADOS)
CODIGOS = [e[0] for e in ESTADOS]
NOMBRES = [e[1] for e in ESTADOS]
TIPOS = [e[3] for e in ESTADOS]
FINALES = {i for i, t in enumerate(TIPOS) if t in (EXITO, NEGATIVO, ERROR, SEGUIMIENTO)}
PERDIDA = {i for i, t in enumerate(TIPOS) if t in (NEGATIVO, ERROR)}   # abandono + error
CATEGORIAS = ["exito", "abandono", "error", "seguimiento", "incompleto"]
ETIQUETAS = {"exito": "Éxito", "abandono": "Abandono", "error": "Error",
             "seguimiento": "Seguimiento pendiente", "incompleto": "Sin terminar (límite de pasos)"}


def categoria(estado):
    """Devuelve la categoría del resultado final de un estado (o None si no es final)."""
    return CATEGORIA_POR_TIPO.get(TIPOS[estado])


# ---------------------------------------------------------------------------
# 1 y 2. Matrices
# ---------------------------------------------------------------------------
def matriz_conteos(recorridos=RECORRIDOS):
    """Matriz N x N con el número de transiciones i -> j observadas en los recorridos base."""
    C = [[0] * N_ESTADOS for _ in range(N_ESTADOS)]
    for r in recorridos:
        seq = r["estados"]
        for a, b in zip(seq, seq[1:]):
            C[a][b] += 1
    return C


def matriz_probabilidades(C=None):
    """Matriz de transición: P[i][j] = C[i][j] / suma de la fila i. Estados finales absorbentes."""
    if C is None:
        C = matriz_conteos()
    P = []
    for i, fila in enumerate(C):
        total = sum(fila)
        if i in FINALES or total == 0:
            nueva = [0.0] * N_ESTADOS
            nueva[i] = 1.0                 # absorbente
        else:
            nueva = [c / total for c in fila]
        P.append(nueva)
    return P


def validar_modelo():
    """Comprueba los requisitos mínimos de la ficha técnica y la coherencia de los recorridos."""
    secuencias = [tuple(r["estados"]) for r in RECORRIDOS]
    usados = {s for seq in secuencias for s in seq}
    problemas = []
    for r in RECORRIDOS:
        seq = r["estados"]
        if seq[0] != 0:
            problemas.append(f"Recorrido {r['id']} no empieza en S0")
        if seq[-1] not in FINALES:
            problemas.append(f"Recorrido {r['id']} no termina en un estado final")
        if any(s in FINALES for s in seq[:-1]):
            problemas.append(f"Recorrido {r['id']} pasa por un estado final antes de terminar")
    P = matriz_probabilidades()
    for i in range(N_ESTADOS):
        if abs(sum(P[i]) - 1) > 1e-9:
            problemas.append(f"La fila {CODIGOS[i]} no suma 1")
    return {
        "estados": N_ESTADOS,
        "recorridos": len(RECORRIDOS),
        "recorridos_distintos": len(set(secuencias)),
        "estados_usados": len(usados),
        "tipos_presentes": sorted({TIPOS[i] for i in range(N_ESTADOS)}),
        "cumple_30_estados": N_ESTADOS >= 30,
        "cumple_60_recorridos": len(set(secuencias)) >= 60,
        "problemas": problemas,
    }


# ---------------------------------------------------------------------------
# 3. Simulación
# ---------------------------------------------------------------------------
def _tablas_acumuladas(P):
    """Para cada estado: lista de destinos posibles y sus probabilidades acumuladas (muestreo rápido)."""
    tablas = []
    for fila in P:
        destinos, acum, s = [], [], 0.0
        for j, p in enumerate(fila):
            if p > 0:
                s += p
                destinos.append(j)
                acum.append(s)
        if acum:
            acum[-1] = 1.0
        tablas.append((destinos, acum))
    return tablas


def simular_usuario(tablas, pasos_max, rng):
    """Simula un usuario desde S0 hasta un estado final o hasta agotar pasos_max."""
    estado = 0
    camino = [0]
    pasos = 0
    while estado not in FINALES and pasos < pasos_max:
        destinos, acum = tablas[estado]
        estado = destinos[bisect_left(acum, rng.random())]
        camino.append(estado)
        pasos += 1
    return camino


def simular(n_usuarios=1000, pasos_max=50, semilla=None, P=None, vista_previa=25, guardar_caminos=False):
    """
    Simula n_usuarios personas navegando con la cadena de Márkov P.
    Devuelve porcentajes de éxito/abandono/error/seguimiento, promedio de pasos,
    pérdidas por estado, estado crítico y una vista previa de recorridos.
    """
    if P is None:
        P = matriz_probabilidades()
    if semilla is None:
        semilla = random.randrange(1, 10**6)
    rng = random.Random(semilla)
    tablas = _tablas_acumuladas(P)

    conteo_cat = Counter()
    conteo_final = Counter()
    perdidas_abandono = Counter()   # estado anterior al abandono
    perdidas_error = Counter()      # estado anterior al error
    visitas = Counter()             # usuarios que pasaron al menos una vez por cada estado
    pasos_lista = []
    previa, caminos = [], []

    for u in range(n_usuarios):
        camino = simular_usuario(tablas, pasos_max, rng)
        final = camino[-1]
        cat = categoria(final) if final in FINALES else "incompleto"
        pasos = len(camino) - 1
        conteo_cat[cat] += 1
        pasos_lista.append(pasos)
        for s in set(camino):
            visitas[s] += 1
        if final in FINALES:
            conteo_final[final] += 1
        if cat == "abandono":
            perdidas_abandono[camino[-2]] += 1
        elif cat == "error":
            perdidas_error[camino[-2]] += 1
        if u < vista_previa:
            previa.append({"usuario": u + 1, "camino": camino, "resultado": cat, "pasos": pasos})
        if guardar_caminos:
            caminos.append(camino)

    porcentajes = {c: round(100 * conteo_cat[c] / n_usuarios, 2) for c in CATEGORIAS}

    # Pérdidas por estado (abandono + error) y estado crítico
    perdidas = []
    for s in range(N_ESTADOS):
        a, e = perdidas_abandono[s], perdidas_error[s]
        if a + e:
            perdidas.append({
                "estado": s, "codigo": CODIGOS[s], "nombre": NOMBRES[s],
                "abandono": a, "error": e, "total": a + e,
                "visitas": visitas[s],
                "tasa": round(100 * (a + e) / visitas[s], 2) if visitas[s] else 0.0,
            })
    perdidas.sort(key=lambda x: (-x["total"], x["estado"]))
    critico = perdidas[0] if perdidas else None
    if critico:
        total_perdidos = conteo_cat["abandono"] + conteo_cat["error"]
        critico = dict(critico)
        critico["porcentaje_de_perdidas"] = round(100 * critico["total"] / total_perdidos, 2) if total_perdidos else 0
        critico["recomendacion"] = RECOMENDACIONES.get(critico["estado"], RECOMENDACION_GENERAL)
    mayor_riesgo = max((p for p in perdidas if p["visitas"] >= max(5, n_usuarios * 0.02)),
                       key=lambda x: x["tasa"], default=None)

    # Histograma de pasos
    hist = Counter(pasos_lista)
    histograma = [{"pasos": k, "usuarios": hist[k]} for k in sorted(hist)]

    mas_frecuente = max(["exito", "abandono", "error", "seguimiento"], key=lambda c: conteo_cat[c])

    resultado = {
        "parametros": {"usuarios": n_usuarios, "pasos_max": pasos_max, "semilla": semilla},
        "conteos": {c: conteo_cat[c] for c in CATEGORIAS},
        "porcentajes": porcentajes,
        "resultado_mas_frecuente": mas_frecuente,
        "pasos": {
            "promedio": round(statistics.mean(pasos_lista), 2),
            "mediana": statistics.median(pasos_lista),
            "minimo": min(pasos_lista),
            "maximo": max(pasos_lista),
        },
        "finales": [{"estado": s, "codigo": CODIGOS[s], "nombre": NOMBRES[s], "categoria": categoria(s),
                     "usuarios": conteo_final[s], "porcentaje": round(100 * conteo_final[s] / n_usuarios, 2)}
                    for s in sorted(FINALES)],
        "perdidas": perdidas,
        "estado_critico": critico,
        "estado_mayor_riesgo": mayor_riesgo,
        "visitas": [{"estado": s, "codigo": CODIGOS[s], "usuarios": visitas[s]} for s in range(N_ESTADOS)],
        "histograma_pasos": histograma,
        "vista_previa": previa,
    }
    if guardar_caminos:
        resultado["caminos"] = caminos
    return resultado


# ---------------------------------------------------------------------------
# 4. Análisis teórico (matriz fundamental)
# ---------------------------------------------------------------------------
def _invertir(M):
    """Inversa de una matriz cuadrada por Gauss-Jordan (sin numpy)."""
    n = len(M)
    A = [list(map(float, fila)) + [1.0 if i == j else 0.0 for j in range(n)] for i, fila in enumerate(M)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(A[r][c]))
        A[c], A[piv] = A[piv], A[c]
        p = A[c][c]
        A[c] = [x / p for x in A[c]]
        for r in range(n):
            if r != c and A[r][c] != 0:
                f = A[r][c]
                A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    return [fila[n:] for fila in A]


def analisis_teorico(P=None):
    """
    Con P = [[Q R],[0 I]]:  N = (I - Q)^-1,  B = N R.
    B[0][f] = probabilidad exacta de que un usuario que entra en S0 termine en el estado final f.
    Suma de la fila 0 de N = número esperado de pasos (sin límite de pasos).
    """
    if P is None:
        P = matriz_probabilidades()
    trans = [i for i in range(N_ESTADOS) if i not in FINALES]
    fins = sorted(FINALES)
    Q = [[P[i][j] for j in trans] for i in trans]
    I_Q = [[(1.0 if a == b else 0.0) - Q[a][b] for b in range(len(trans))] for a in range(len(trans))]
    Nf = _invertir(I_Q)
    R = [[P[i][f] for f in fins] for i in trans]
    fila0 = Nf[trans.index(0)]
    absorcion = {fins[k]: sum(fila0[m] * R[m][k] for m in range(len(trans))) for k in range(len(fins))}
    por_cat = Counter()
    for f, p in absorcion.items():
        por_cat[categoria(f)] += p
    return {
        "pasos_esperados": round(sum(fila0), 3),
        "porcentajes": {c: round(100 * por_cat[c], 2) for c in ["exito", "abandono", "error", "seguimiento"]},
        "por_estado_final": [{"codigo": CODIGOS[f], "nombre": NOMBRES[f], "probabilidad": round(p, 4)}
                             for f, p in absorcion.items()],
    }


# ---------------------------------------------------------------------------
# 5. Escenario de mejora
# ---------------------------------------------------------------------------
EXITOS = {i for i, t in enumerate(TIPOS) if t == EXITO}
NO_AVANZA = {30, 31}   # volver atrás y contenido 'por confirmar' no acercan al objetivo


def aplicar_mejora(estado, reduccion=0.5, P=None, modo="exito"):
    """
    Reduce en `reduccion` (0 a 1) la probabilidad de pasar del `estado` a un abandono o error.
    La probabilidad liberada se reparte:
      * modo "exito": entre los destinos de éxito de esa fila; si no hay, entre los destinos que
                      hacen avanzar al usuario (no 'volver atrás' ni 'por confirmar').
      * modo "proporcional": entre todos los demás destinos según su peso actual.
    Devuelve (nueva_matriz, fila_antes, fila_despues).
    """
    if P is None:
        P = matriz_probabilidades()
    nueva = [fila[:] for fila in P]
    fila = nueva[estado]
    if estado in FINALES:
        return nueva, P[estado], fila
    perdida = sum(fila[j] for j in PERDIDA)
    otros = [j for j in range(N_ESTADOS) if fila[j] > 0 and j not in PERDIDA]
    if modo == "exito":
        preferidos = [j for j in otros if j in EXITOS] or [j for j in otros if j not in NO_AVANZA]
        otros = preferidos or otros
    total_otros = sum(fila[j] for j in otros)
    if perdida == 0 or total_otros == 0:
        return nueva, P[estado], fila
    liberada = perdida * reduccion
    for j in PERDIDA:
        fila[j] *= (1 - reduccion)
    for j in otros:
        fila[j] += liberada * fila[j] / total_otros
    return nueva, P[estado], fila


def comparar_mejora(estado, reduccion, n_usuarios, pasos_max, semilla, modo="exito"):
    """Simula el modelo original y el mejorado con la misma semilla para compararlos."""
    base = simular(n_usuarios, pasos_max, semilla, vista_previa=0)
    P2, antes, despues = aplicar_mejora(estado, reduccion, modo=modo)
    mejorado = simular(n_usuarios, pasos_max, semilla, P=P2, vista_previa=0)
    cambios = [{"destino": CODIGOS[j], "nombre": NOMBRES[j], "antes": round(antes[j], 4), "despues": round(despues[j], 4)}
               for j in range(N_ESTADOS) if antes[j] > 0 or despues[j] > 0]
    return {
        "estado": {"codigo": CODIGOS[estado], "nombre": NOMBRES[estado], "indice": estado},
        "reduccion": reduccion,
        "recomendacion": RECOMENDACIONES.get(estado, RECOMENDACION_GENERAL),
        "base": {k: base[k] for k in ("porcentajes", "pasos", "estado_critico", "conteos")},
        "mejorado": {k: mejorado[k] for k in ("porcentajes", "pasos", "estado_critico", "conteos")},
        "teorico_base": analisis_teorico()["porcentajes"],
        "teorico_mejorado": analisis_teorico(P2)["porcentajes"],
        "fila": cambios,
    }
