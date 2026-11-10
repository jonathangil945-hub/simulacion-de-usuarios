# -*- coding: utf-8 -*-
"""
simulacion_consola.py
=====================
Versión en consola (sin interfaz web) del modelo. Sirve como "archivo de trabajo en Python"
y también se puede copiar a Google Colab junto con la carpeta markov/.

Uso:
    python simulacion_consola.py                       # 1000 usuarios, 50 pasos, semilla 2026
    python simulacion_consola.py --usuarios 5000 --pasos 80 --semilla 7
"""
import argparse

from markov.modelo import ESTADOS, RECORRIDOS
from markov.cadena import (matriz_conteos, matriz_probabilidades, simular, analisis_teorico,
                           comparar_mejora, validar_modelo, CODIGOS, ETIQUETAS, categoria)


def linea(t=""):
    print("\n" + "=" * 78 + ("\n  " + t + "\n" + "=" * 78 if t else ""))


def main():
    ap = argparse.ArgumentParser(description="Simulación de navegación con cadenas de Márkov")
    ap.add_argument("--usuarios", type=int, default=1000, help="10 a 10000")
    ap.add_argument("--pasos", type=int, default=50, help="pasos máximos por usuario")
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--reduccion", type=int, default=50, help="%% de reducción en el estado crítico")
    a = ap.parse_args()
    if not 10 <= a.usuarios <= 10000:
        ap.error("--usuarios debe estar entre 10 y 10000")

    linea("1. ESTADOS DEL MODELO")
    for c, n, d, t, s in ESTADOS:
        print(f"{c:>4}  {n:<40} [{t}]")

    linea("2. RECORRIDOS BASE")
    for r in RECORRIDOS:
        print(f"#{r['id']:>2} {r['tipo_usuario']:<18} " + " → ".join(CODIGOS[s] for s in r["estados"]))
    print("\nValidación:", validar_modelo())

    C = matriz_conteos()
    P = matriz_probabilidades(C)
    linea("3. MATRIZ DE CONTEOS (solo transiciones distintas de cero)")
    for i, fila in enumerate(C):
        nz = [f"{CODIGOS[j]}:{v}" for j, v in enumerate(fila) if v]
        if nz:
            print(f"{CODIGOS[i]:>4} → " + ", ".join(nz))
    linea("4. MATRIZ DE PROBABILIDADES (solo distintas de cero)")
    for i, fila in enumerate(P):
        print(f"{CODIGOS[i]:>4} → " + ", ".join(f"{CODIGOS[j]}:{p:.3f}" for j, p in enumerate(fila) if p))

    linea(f"5. SIMULACIÓN: {a.usuarios} usuarios, máx. {a.pasos} pasos, semilla {a.semilla}")
    r = simular(a.usuarios, a.pasos, a.semilla, vista_previa=10)
    for u in r["vista_previa"]:
        print(f"Usuario {u['usuario']:>2}: " + " → ".join(CODIGOS[s] for s in u["camino"]) + f"  [{ETIQUETAS[u['resultado']]}]")
    print()
    for c, v in r["porcentajes"].items():
        print(f"  {ETIQUETAS[c]:<32} {v:6.2f} %   ({r['conteos'][c]} usuarios)")
    print(f"  Promedio de pasos: {r['pasos']['promedio']}   (mediana {r['pasos']['mediana']}, máx. {r['pasos']['maximo']})")
    c = r["estado_critico"]
    print(f"\n  ESTADO CRÍTICO: {c['codigo']} {c['nombre']} -> {c['total']} usuarios perdidos "
          f"({c['porcentaje_de_perdidas']} % de las pérdidas, tasa {c['tasa']} %)")
    print("  Recomendación:", c["recomendacion"])

    t = analisis_teorico(P)
    print("\n  Teórico (matriz fundamental):", t["porcentajes"], "pasos esperados:", t["pasos_esperados"])

    linea(f"6. MEJORA: reducir {a.reduccion} % el abandono/error en {c['codigo']}")
    m = comparar_mejora(c["estado"], a.reduccion / 100, a.usuarios, a.pasos, a.semilla)
    for k in ("exito", "abandono", "error", "seguimiento"):
        print(f"  {ETIQUETAS[k]:<24} {m['base']['porcentajes'][k]:6.2f} % → {m['mejorado']['porcentajes'][k]:6.2f} %"
              f"   (teórico {m['teorico_base'][k]:.2f} → {m['teorico_mejorado'][k]:.2f})")


if __name__ == "__main__":
    main()
