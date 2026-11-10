# -*- coding: utf-8 -*-
"""
app.py — Servidor web del simulador (Flask)
===========================================
Ejecuta:   python app.py
Luego abre en el PC:        http://localhost:5000
y en el celular (misma red Wi-Fi):  http://<IP-de-tu-PC>:5000   (la IP se imprime al iniciar)
"""
import csv
import io
import socket

from flask import Flask, jsonify, render_template, request, Response

from markov.modelo import ESTADOS, RECORRIDOS, RECOMENDACIONES, RECOMENDACION_GENERAL, tipos_de_usuario
from markov.cadena import (matriz_conteos, matriz_probabilidades, simular, analisis_teorico,
                           comparar_mejora, validar_modelo, CODIGOS, NOMBRES, FINALES, ETIQUETAS, categoria)

app = Flask(__name__)
app.json.ensure_ascii = False

MIN_USUARIOS, MAX_USUARIOS = 10, 10000
MIN_PASOS, MAX_PASOS = 3, 200


def _entero(valor, defecto, minimo, maximo, nombre):
    """Convierte y valida un parámetro entero dentro de un rango."""
    try:
        v = int(valor) if valor not in (None, "") else defecto
    except (TypeError, ValueError):
        raise ValueError(f"'{nombre}' debe ser un número entero.")
    if not minimo <= v <= maximo:
        raise ValueError(f"'{nombre}' debe estar entre {minimo} y {maximo}.")
    return v


def _semilla(valor):
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError("La semilla debe ser un número entero.")


@app.errorhandler(ValueError)
def _error_valor(e):
    return jsonify({"error": str(e)}), 400


@app.route("/")
def inicio():
    return render_template("index.html", min_u=MIN_USUARIOS, max_u=MAX_USUARIOS, min_p=MIN_PASOS, max_p=MAX_PASOS)


@app.route("/api/modelo")
def api_modelo():
    """Estados, recorridos base, matriz de conteos y matriz de probabilidades."""
    C = matriz_conteos()
    P = matriz_probabilidades(C)
    return jsonify({
        "sitio": "https://museosantodomingo.netlify.app/",
        "estados": [{"indice": i, "codigo": c, "nombre": n, "descripcion": d, "tipo": t, "seccion": s}
                    for i, (c, n, d, t, s) in enumerate(ESTADOS)],
        "recorridos": RECORRIDOS,
        "tipos_usuario": tipos_de_usuario(),
        "conteos": C,
        "probabilidades": [[round(p, 4) for p in fila] for fila in P],
        "validacion": validar_modelo(),
        "teorico": analisis_teorico(P),
        "etiquetas": ETIQUETAS,
        "recomendaciones": {CODIGOS[k]: v for k, v in RECOMENDACIONES.items()},
        "recomendacion_general": RECOMENDACION_GENERAL,
    })


@app.route("/api/simular", methods=["POST"])
def api_simular():
    d = request.get_json(silent=True) or {}
    n = _entero(d.get("usuarios"), 1000, MIN_USUARIOS, MAX_USUARIOS, "Número de usuarios")
    pasos = _entero(d.get("pasos_max"), 50, MIN_PASOS, MAX_PASOS, "Pasos máximos")
    previa = _entero(d.get("vista_previa"), 30, 0, 200, "Vista previa")
    return jsonify(simular(n, pasos, _semilla(d.get("semilla")), vista_previa=previa))


@app.route("/api/mejora", methods=["POST"])
def api_mejora():
    d = request.get_json(silent=True) or {}
    n = _entero(d.get("usuarios"), 1000, MIN_USUARIOS, MAX_USUARIOS, "Número de usuarios")
    pasos = _entero(d.get("pasos_max"), 50, MIN_PASOS, MAX_PASOS, "Pasos máximos")
    estado = _entero(d.get("estado"), 31, 0, len(ESTADOS) - 1, "Estado")
    if estado in FINALES:
        raise ValueError("Elige un estado no final para aplicar la mejora.")
    reduccion = _entero(d.get("reduccion"), 50, 0, 100, "Reducción") / 100
    modo = d.get("modo") if d.get("modo") in ("exito", "proporcional") else "exito"
    semilla = _semilla(d.get("semilla")) or 2026
    return jsonify(comparar_mejora(estado, reduccion, n, pasos, semilla, modo))


# ------------------------------- Exportar CSV -------------------------------
def _csv(nombre, filas):
    buf = io.StringIO()
    csv.writer(buf, delimiter=";").writerows(filas)
    return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nombre}"})


@app.route("/exportar/<que>.csv")
def exportar(que):
    if que == "estados":
        return _csv("estados.csv", [["Código", "Nombre", "Descripción", "Tipo", "Sección"]] + [list(e) for e in ESTADOS])
    if que == "recorridos":
        return _csv("recorridos.csv", [["#", "Tipo de usuario", "Descripción", "Recorrido", "Resultado"]] +
                    [[r["id"], r["tipo_usuario"], r["descripcion"], " → ".join(CODIGOS[s] for s in r["estados"]),
                      ETIQUETAS[categoria(r["estados"][-1])]] for r in RECORRIDOS])
    if que == "conteos":
        C = matriz_conteos()
        return _csv("matriz_conteos.csv", [[""] + CODIGOS] + [[CODIGOS[i]] + fila for i, fila in enumerate(C)])
    if que == "probabilidades":
        P = matriz_probabilidades()
        return _csv("matriz_probabilidades.csv", [[""] + CODIGOS] +
                    [[CODIGOS[i]] + [f"{p:.4f}".replace(".", ",") for p in fila] for i, fila in enumerate(P)])
    if que == "simulacion":
        n = _entero(request.args.get("usuarios"), 1000, MIN_USUARIOS, MAX_USUARIOS, "Número de usuarios")
        pasos = _entero(request.args.get("pasos"), 50, MIN_PASOS, MAX_PASOS, "Pasos máximos")
        r = simular(n, pasos, _semilla(request.args.get("semilla")), vista_previa=0, guardar_caminos=True)
        filas = [["Usuario", "Pasos", "Estado final", "Resultado", "Recorrido"]]
        for i, cam in enumerate(r["caminos"]):
            fin = cam[-1]
            res = ETIQUETAS[categoria(fin)] if fin in FINALES else ETIQUETAS["incompleto"]
            filas.append([i + 1, len(cam) - 1, f"{CODIGOS[fin]} {NOMBRES[fin]}", res, " → ".join(CODIGOS[s] for s in cam)])
        return _csv(f"simulacion_{n}_usuarios_semilla_{r['parametros']['semilla']}.csv", filas)
    return jsonify({"error": "Exportación no encontrada"}), 404


def ips_locales():
    """IPs del PC en la red local, para abrir el simulador desde el celular."""
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


if __name__ == "__main__":
    PUERTO = 5000
    print("=" * 62)
    print("  Simulador de Márkov – Iglesia de Santo Domingo (Tunja)")
    print("=" * 62)
    print(f"  En este PC:            http://localhost:{PUERTO}")
    for ip in ips_locales():
        print(f"  En celular / otro PC:  http://{ip}:{PUERTO}")
    print("  (El celular debe estar conectado a la MISMA red Wi-Fi)")
    print("  Para detener el servidor: Ctrl + C")
    print("=" * 62)
    app.run(host="0.0.0.0", port=PUERTO, debug=False, threaded=True)
