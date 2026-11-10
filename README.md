# Simulador de Márkov – Navegación en la web de la Iglesia de Santo Domingo (Tunja)

Proyecto Integrador de Simulación. Modela con una **cadena de Márkov** cómo navegan las personas por
https://museosantodomingo.netlify.app/ y simula de **10 a 10 000 usuarios** desde una interfaz web
que funciona en PC y en celular.

## Cómo ejecutarlo

1. Instala **Python 3.10 o superior** desde https://www.python.org/downloads/
   (en Windows marca la casilla **"Add Python to PATH"** durante la instalación).
2. Descomprime el .zip.
3. **Windows:** doble clic en `INICIAR_WINDOWS.bat`.
   **Mac / Linux:** en una terminal, `./iniciar_mac_linux.sh`.
   (Manual: `pip install -r requirements.txt` y luego `python app.py`.)
4. La ventana negra muestra dos direcciones:
   - `http://localhost:5000` → ábrela en tu PC.
   - `http://192.168.x.x:5000` → ábrela en el **celular** o en otro PC conectado a la **misma red Wi-Fi**.
5. Para apagar el servidor: `Ctrl + C` en esa ventana.

### Si el celular no abre la página
- Comprueba que el celular y el PC están en la **misma red Wi-Fi** (no datos móviles).
- La primera vez, Windows pregunta si permite a Python usar la red: elige **Permitir** y marca **Redes privadas**.
  Si ya lo rechazaste: *Panel de control → Firewall de Windows Defender → Permitir una aplicación* → activa *Python* en "Privada".
- En Windows, la red Wi-Fi debe estar como **Red privada** (Configuración → Red e Internet → Wi-Fi → propiedades).
- Algunas redes de universidades bloquean la conexión entre equipos; en ese caso usa la **zona Wi-Fi del celular** y conecta el PC a ella.

## Qué incluye la interfaz
| Requisito de la ficha | Dónde está |
|---|---|
| Elegir número de usuarios (10 a 10 000) | Pestaña *Simulación*: deslizador, casilla y botones rápidos |
| Elegir pasos máximos por usuario | Pestaña *Simulación* (3 a 200) |
| Estados (código, nombre, descripción, tipo) | Pestaña *Estados* (43 estados, con filtros y buscador) |
| Recorridos base | Pestaña *Recorridos* (74 recorridos, 8 tipos de usuario) |
| Matriz de conteos y de probabilidades | Pestaña *Matrices* (mapa de calor, explorador por fila, CSV) |
| Ejecutar la simulación | Botón *Ejecutar simulación* |
| Vista previa de usuarios simulados | Lista con el recorrido de cada usuario y su resultado |
| Resultados (% éxito, abandono, error, seguimiento, promedio de pasos) | Tarjetas de resultados |
| Gráficas | Dona, mosaico animado, pérdidas por estado, estados finales, histograma de pasos |
| Estado crítico | Tarjeta roja "Estado crítico detectado" |
| Interfaz de mejora | Pestaña *Mejora y análisis*: comparación antes/después y respuestas a las 6 preguntas |

## Estructura
```
app.py                  Servidor Flask (API + interfaz). Escucha en 0.0.0.0:5000
markov/modelo.py        43 estados y 74 recorridos base (basados en el sitio real)
markov/cadena.py        Matrices, simulación, estado crítico, matriz fundamental y mejora
simulacion_consola.py   Misma simulación en consola (sirve para Colab)
templates/, static/     Interfaz web (HTML, CSS, JS; sin internet ni librerías externas)
datos/                  Estados, recorridos y matrices en CSV y Excel
documento/              Informe en Word listo para entregar
```

## Modelo
- **Estados:** S0 (ingreso) … S32 intermedios; S33–S35 error; S36–S39 éxito; S40–S41 abandono; S42 seguimiento.
- **Matriz de conteos:** `C[i][j]` = veces que en los recorridos base se pasa de Si a Sj.
- **Matriz de transición:** `P[i][j] = C[i][j] / Σ_j C[i][j]`. Los estados finales son absorbentes (`P[f][f] = 1`).
- **Simulación:** cada usuario empieza en S0 y, en cada paso, elige el siguiente estado al azar según su fila de P,
  hasta llegar a un estado final o agotar los pasos máximos.
- **Comprobación teórica:** con `N = (I − Q)^-1` y `B = N·R` se obtiene la probabilidad exacta de cada resultado.
- **Mejora:** se reduce un % la probabilidad de pasar del estado elegido a abandono/error y se redistribuye hacia el objetivo.

Con la **semilla 2026** se reproducen exactamente los resultados del informe.

## Google Colab
Sube la carpeta `markov/` y `simulacion_consola.py`, y ejecuta en una celda:
```
!python simulacion_consola.py --usuarios 1000 --pasos 50 --semilla 2026
```
