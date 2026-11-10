# -*- coding: utf-8 -*-
"""
modelo.py
=========
Definición del modelo de navegación de la página web de la
Iglesia de Santo Domingo (Tunja, Boyacá):  https://museosantodomingo.netlify.app/

Contiene:
  * ESTADOS    -> 43 estados (S0 ... S42) con código, nombre, descripción, tipo y sección real del sitio.
  * RECORRIDOS -> 74 recorridos base de usuarios, distintos entre sí, agrupados por tipo de usuario.

Los estados se construyeron recorriendo el sitio real: menú principal (Inicio, La Iglesia, Historia,
Patrimonio, Capilla del Rosario, Museo Virtual, Galería, Actualidad, Visita, Agenda, Contacto),
buscador, selector de idioma, filtros de Galería y Agenda, formulario de Contacto, botón
"INICIAR RECORRIDO VIRTUAL", textos "Información por confirmar", y el error 404 que aparece al
abrir o recargar una sub-página directamente (por ejemplo /historia).
"""

# ---------------------------------------------------------------------------
# Tipos de estado (los exige la ficha técnica)
# ---------------------------------------------------------------------------
INICIAL = "inicial"
INTERMEDIO = "intermedio"
EXITO = "final exitoso"
NEGATIVO = "final negativo"      # abandono
ERROR = "error"
SEGUIMIENTO = "seguimiento"

# Categoría de resultado final que se usa en los porcentajes
CATEGORIA_POR_TIPO = {
    EXITO: "exito",
    NEGATIVO: "abandono",
    ERROR: "error",
    SEGUIMIENTO: "seguimiento",
}

# ---------------------------------------------------------------------------
# ESTADOS: (código, nombre, descripción, tipo, sección / ruta del sitio)
# ---------------------------------------------------------------------------
ESTADOS = [
    ("S0",  "Ingreso al sitio", "La persona abre el navegador y carga el sitio desde Google, redes sociales o un enlace compartido.", INICIAL, "Navegador"),
    ("S1",  "Página de Inicio", "Ve el banner 'Historia, fe y patrimonio de Tunja' y los accesos a La Iglesia y al Museo Virtual.", INTERMEDIO, "/"),
    ("S2",  "Abrir menú de navegación", "Abre el menú principal (en celular, el menú desplegable) para elegir una sección.", INTERMEDIO, "Menú"),
    ("S3",  "Usar el buscador", "Escribe en la caja 'Buscar en el sitio...' de la barra superior.", INTERMEDIO, "Buscador"),
    ("S4",  "Resultados de búsqueda", "Revisa lo que devolvió la búsqueda y decide a qué sección ir.", INTERMEDIO, "Buscador"),
    ("S5",  "Cambiar idioma", "Abre el selector de idioma 'Español' buscando otra lengua (visitantes extranjeros).", INTERMEDIO, "Selector de idioma"),
    ("S6",  "La Iglesia", "Lee la presentación institucional: vida espiritual, patrimonio cultural y vida comunitaria.", INTERMEDIO, "/la-iglesia"),
    ("S7",  "Historia - línea de tiempo", "Entra a la sección Historia con la cronología de la Iglesia.", INTERMEDIO, "/historia"),
    ("S8",  "Leer cronología", "Recorre los siglos XVI al XX y 'Patrimonio vivo' haciendo scroll en la línea de tiempo.", INTERMEDIO, "/historia"),
    ("S9",  "Patrimonio - categorías", "Explora las categorías Arquitectura, Escultura, Pintura y Retablos.", INTERMEDIO, "/patrimonio"),
    ("S10", "Catálogo de piezas", "Revisa el catálogo: Retablo Mayor, Púlpito, Virgen del Rosario, Serie pictórica, etc.", INTERMEDIO, "/patrimonio"),
    ("S11", "Ver detalle de pieza", "Pulsa 'VER DETALLE →' sobre una pieza patrimonial.", INTERMEDIO, "/patrimonio"),
    ("S12", "Capilla del Rosario", "Lee sobre la arquitectura, el arte y la espiritualidad de la Capilla del Rosario.", INTERMEDIO, "/capilla-del-rosario"),
    ("S13", "Museo Virtual", "Entra a la página del Museo Virtual de la Capilla del Rosario.", INTERMEDIO, "/museo-virtual"),
    ("S14", "Iniciar recorrido virtual", "Pulsa el botón 'INICIAR RECORRIDO VIRTUAL' esperando la experiencia 3D.", INTERMEDIO, "/museo-virtual"),
    ("S15", "Usar controles del recorrido", "Usa las flechas (← ↑ ↓ →) y el zoom (+ –) de la interfaz de referencia.", INTERMEDIO, "/museo-virtual"),
    ("S16", "Puntos de interés", "Revisa los puntos de interés: Retablo Mayor, Púlpito, Virgen del Rosario, Pintura mural.", INTERMEDIO, "/museo-virtual"),
    ("S17", "Galería", "Abre la galería de imágenes de la Iglesia, su arte y arquitectura.", INTERMEDIO, "/galeria"),
    ("S18", "Filtrar galería", "Usa los filtros Todas, Iglesia, Capilla del Rosario, Arquitectura, Arte o Patrimonio.", INTERMEDIO, "/galeria"),
    ("S19", "Abrir imagen ampliada", "Abre una fotografía (p. ej. 'Fachada principal') para verla en grande.", INTERMEDIO, "/galeria"),
    ("S20", "Cerrar imagen ampliada", "Cierra el visor de imagen y vuelve a la cuadrícula de la galería.", INTERMEDIO, "/galeria"),
    ("S21", "Actualidad", "Entra a 'Noticias y eventos' y ve las últimas noticias por categoría.", INTERMEDIO, "/actualidad"),
    ("S22", "Leer noticia", "Pulsa 'LEER MÁS' y abre el detalle de una noticia.", INTERMEDIO, "/actualidad/noticia-ejemplo"),
    ("S23", "Agenda", "Abre el calendario de actividades (celebraciones litúrgicas, eventos culturales, museo).", INTERMEDIO, "/agenda"),
    ("S24", "Filtrar eventos", "Usa los filtros Todos, Litúrgica, Cultural o Museo de la agenda.", INTERMEDIO, "/agenda"),
    ("S25", "Visita - horarios y ubicación", "Consulta ubicación, horarios, accesibilidad y recomendaciones para visitar.", INTERMEDIO, "/visita"),
    ("S26", "Contacto", "Abre la página de contacto con formulario, dirección, teléfono y correo.", INTERMEDIO, "/contacto"),
    ("S27", "Llenar formulario", "Escribe nombre, correo electrónico, asunto y mensaje.", INTERMEDIO, "/contacto"),
    ("S28", "Formulario con errores", "Aparecen errores de validación (campo vacío o correo inválido) y debe corregir.", INTERMEDIO, "/contacto"),
    ("S29", "Enviar mensaje", "Pulsa el botón 'ENVIAR MENSAJE'.", INTERMEDIO, "/contacto"),
    ("S30", "Volver atrás / recargar", "Usa el botón atrás del navegador o recarga la página actual.", INTERMEDIO, "Navegador"),
    ("S31", "Encuentra contenido 'por confirmar'", "Lee textos como 'Información por confirmar' o 'Contenido en construcción' y duda si seguir.", INTERMEDIO, "Varias secciones"),
    ("S32", "Pie de página / enlaces legales", "Baja al pie de página: redes sociales, privacidad, tratamiento de datos, aviso legal.", INTERMEDIO, "Footer"),
    ("S33", "Error 404 - página no encontrada", "Al abrir o recargar una sub-página directamente (p. ej. /historia) Netlify responde 'Page not found'.", ERROR, "Netlify 404"),
    ("S34", "Error - recorrido 3D no disponible", "El botón del recorrido virtual no abre ninguna experiencia ('Experiencia 3D interactiva - Próximamente').", ERROR, "/museo-virtual"),
    ("S35", "Error - el mensaje no se envía", "El formulario es solo visual: el mensaje no llega y el usuario no recibe confirmación.", ERROR, "/contacto"),
    ("S36", "Éxito - planificó su visita", "Obtiene la información necesaria y decide visitar la Iglesia en el centro histórico de Tunja.", EXITO, "Resultado"),
    ("S37", "Éxito - mensaje enviado y confirmado", "El mensaje de contacto se envía y recibe confirmación en pantalla.", EXITO, "Resultado"),
    ("S38", "Éxito - exploró el patrimonio", "Completa la exploración de historia, patrimonio, galería o museo virtual que buscaba.", EXITO, "Resultado"),
    ("S39", "Éxito - se informó de eventos", "Encuentra la celebración o noticia que buscaba en Agenda o Actualidad.", EXITO, "Resultado"),
    ("S40", "Abandono - cierra la pestaña", "Cierra la pestaña o se va a otro sitio sin cumplir su objetivo.", NEGATIVO, "Resultado"),
    ("S41", "Abandono - inactividad", "Deja la página abierta sin interactuar hasta que la sesión se pierde.", NEGATIVO, "Resultado"),
    ("S42", "Seguimiento pendiente", "Queda esperando: respuesta al mensaje, fecha 'por confirmar' o lanzamiento del museo. Volverá luego.", SEGUIMIENTO, "Resultado"),
]

# ---------------------------------------------------------------------------
# RECORRIDOS BASE: (tipo de usuario, descripción breve, secuencia de estados)
# Cada recorrido empieza en S0 y termina en un estado final (S33 ... S42).
# ---------------------------------------------------------------------------
_R = [
    # ---------------- Turista que planea su visita ----------------
    ("Turista", "Va directo a Visita y aunque ve datos por confirmar decide ir", "0 1 25 31 36"),
    ("Turista", "Usa el menú para ir a Visita y planifica", "0 1 2 25 36"),
    ("Turista", "Horarios 'por confirmar': se va", "0 1 25 31 40"),
    ("Turista", "Explora el museo virtual antes de visitar", "0 1 2 25 13 15 16 36"),
    ("Turista", "Revisa patrimonio para saber qué ver", "0 1 25 9 10 11 31 36"),
    ("Turista", "Busca 'horarios' en el buscador", "0 1 3 4 25 36"),
    ("Turista", "Pregunta horarios por el formulario y queda esperando", "0 1 25 31 26 27 29 42"),
    ("Turista", "Duda, vuelve a inicio y termina cerrando", "0 1 2 25 31 30 1 40"),
    ("Turista", "Extranjero: intenta cambiar idioma y planifica", "0 5 1 2 25 36"),
    ("Turista", "Extranjero: no hay otro idioma y abandona", "0 5 1 25 31 40"),
    ("Turista", "Cruza Visita con Agenda", "0 1 25 23 36"),
    ("Turista", "Lee La Iglesia y luego Visita", "0 1 6 25 36"),
    ("Turista", "Mira fotos antes de decidir", "0 1 2 25 17 19 20 36"),
    # ---------------- Feligrés / comunidad ----------------
    ("Feligrés", "Busca horario de misa: 'por confirmar'", "0 1 23 24 31 42"),
    ("Feligrés", "Filtra eventos litúrgicos y encuentra uno", "0 1 2 23 24 39"),
    ("Feligrés", "Agenda sin fechas: abandona", "0 1 23 31 40"),
    ("Feligrés", "Lee noticia en preparación y queda pendiente", "0 1 21 22 31 42"),
    ("Feligrés", "Lee una noticia de la comunidad", "0 1 21 22 39"),
    ("Feligrés", "Filtra agenda y luego mira cómo llegar", "0 1 2 23 24 25 36"),
    ("Feligrés", "Desde La Iglesia va a la agenda", "0 1 6 23 39"),
    ("Feligrés", "Noticias vacías, vuelve y prueba la agenda", "0 1 21 31 30 23 24 42"),
    ("Feligrés", "Pregunta por un evento, corrige el formulario", "0 1 23 26 27 28 27 29 42"),
    ("Feligrés", "Lee noticia, vuelve, se aburre", "0 1 2 21 22 30 21 40"),
    # ---------------- Estudiante / investigador ----------------
    ("Estudiante", "Historia con fechas por confirmar: se va", "0 1 2 7 8 31 40"),
    ("Estudiante", "Historia y Capilla del Rosario", "0 1 7 8 12 38"),
    ("Estudiante", "Pide fuentes por el formulario: no se envía", "0 1 2 7 8 31 26 27 29 35"),
    ("Estudiante", "Busca 'historia' en el buscador", "0 1 3 4 7 8 38"),
    ("Estudiante", "Revisa varias piezas del catálogo", "0 1 9 10 11 31 30 10 11 38"),
    ("Estudiante", "Va del menú al detalle de una pieza", "0 1 2 9 10 11 38"),
    ("Estudiante", "Lee mucho y se queda inactivo", "0 1 7 8 9 10 11 31 41"),
    ("Estudiante", "Empieza por La Iglesia", "0 1 6 7 8 38"),
    ("Estudiante", "Búsqueda sin resultados útiles", "0 1 3 4 31 40"),
    ("Estudiante", "Capilla, historia y pie de página", "0 1 2 12 7 8 32 40"),
    ("Estudiante", "Recarga /historia y aparece el 404", "0 1 7 31 30 33"),
    ("Estudiante", "Quiere escribir pero el formulario falla", "0 1 9 10 11 31 26 27 28 41"),
    ("Estudiante", "Recorrido completo hasta el museo", "0 1 2 7 8 12 13 15 16 38"),
    # ---------------- Amante del arte / galería ----------------
    ("Arte y fotografía", "Filtra y amplía una foto", "0 1 17 18 19 20 38"),
    ("Arte y fotografía", "Abre y cierra varias fotos", "0 1 2 17 19 20 19 20 38"),
    ("Arte y fotografía", "Abre una foto y se distrae", "0 1 17 19 41"),
    ("Arte y fotografía", "Usa dos filtros distintos", "0 1 17 18 19 20 18 19 20 38"),
    ("Arte y fotografía", "Imágenes de referencia: abandona", "0 1 2 17 18 19 31 40"),
    ("Arte y fotografía", "De patrimonio a la galería", "0 1 9 17 19 20 38"),
    ("Arte y fotografía", "De la galería a la Capilla", "0 1 17 19 20 12 38"),
    ("Arte y fotografía", "Recarga la galería: error 404", "0 1 2 17 18 19 20 30 33"),
    ("Arte y fotografía", "Galería y catálogo patrimonial", "0 1 17 18 19 20 9 10 11 38"),
    ("Arte y fotografía", "Ve una foto y cierra", "0 1 17 19 20 40"),
    # ---------------- Interesado en el Museo Virtual ----------------
    ("Museo virtual", "Pulsa iniciar recorrido: no hay 3D", "0 1 13 14 34"),
    ("Museo virtual", "Desde el menú al recorrido: no hay 3D", "0 1 2 13 14 34"),
    ("Museo virtual", "Usa la interfaz de referencia", "0 1 13 15 16 38"),
    ("Museo virtual", "Desde la Capilla al recorrido", "0 1 12 13 14 34"),
    ("Museo virtual", "Botón sin 3D, pero usa la vista previa", "0 1 13 14 15 16 38"),
    ("Museo virtual", "Puntos 'por confirmar': abandona", "0 1 13 15 16 31 40"),
    ("Museo virtual", "Vuelve atrás y usa los controles", "0 1 2 13 14 30 13 15 16 38"),
    ("Museo virtual", "Lee los avances del proyecto y espera", "0 1 13 14 31 21 22 42"),
    ("Museo virtual", "Capilla, museo y error del recorrido", "0 1 2 12 13 14 34"),
    ("Museo virtual", "Mueve los controles y se queda quieto", "0 1 13 15 41"),
    # ---------------- Persona que quiere contactar ----------------
    ("Contacto", "Envía mensaje y ve confirmación", "0 1 26 27 29 37"),
    ("Contacto", "Corrige el correo y envía", "0 1 2 26 27 28 27 29 37"),
    ("Contacto", "Envía pero no llega", "0 1 26 27 29 35"),
    ("Contacto", "Error de validación y abandona", "0 1 26 27 28 40"),
    ("Contacto", "Envía y queda esperando respuesta", "0 1 2 26 27 29 42"),
    ("Contacto", "Teléfono y correo por confirmar", "0 1 26 31 40"),
    ("Contacto", "Llega desde el pie de página; falla el envío", "0 1 32 26 27 29 35"),
    ("Contacto", "Dos intentos fallidos de validación", "0 1 26 27 28 27 28 40"),
    # ---------------- Visitante de paso / rebote ----------------
    ("Visitante de paso", "Ve el inicio y se va", "0 1 40"),
    ("Visitante de paso", "La página carga y cierra de inmediato", "0 40"),
    ("Visitante de paso", "Abre el menú, lee La Iglesia y se va", "0 1 2 6 40"),
    ("Visitante de paso", "Baja al pie de página y se va", "0 1 32 40"),
    ("Visitante de paso", "Prueba el idioma y se va", "0 1 5 1 40"),
    ("Visitante de paso", "Busca algo, vuelve y se va", "0 1 3 4 30 1 40"),
    ("Visitante de paso", "Deja la pestaña abierta", "0 1 41"),
    # ---------------- Llega por enlace compartido ----------------
    ("Enlace compartido", "Abre un enlace directo a una sub-página: 404", "0 33"),
    ("Enlace compartido", "Lee noticia, recarga y aparece 404", "0 1 21 22 30 33"),
    ("Enlace compartido", "Recarga la Capilla del Rosario: 404", "0 1 12 30 33"),
]

RECORRIDOS = [
    {"id": i + 1, "tipo_usuario": t, "descripcion": d, "estados": [int(x) for x in s.split()]}
    for i, (t, d, s) in enumerate(_R)
]

# ---------------------------------------------------------------------------
# Recomendaciones de mejora por estado (se usan en la sección "Mejora")
# ---------------------------------------------------------------------------
RECOMENDACIONES = {
    0:  "Optimizar la carga inicial (imágenes livianas, vista previa para redes) para que la persona no cierre antes de ver el contenido.",
    1:  "Agregar en el Inicio accesos directos claros a 'Horarios de visita', 'Agenda de misas' y 'Museo Virtual' con información real.",
    5:  "Habilitar al menos la versión en inglés del sitio; hoy el selector solo ofrece Español.",
    14: "Mientras llega el 3D, hacer que el botón abra un recorrido 360° con fotografías o un video, en lugar de no hacer nada.",
    17: "Reemplazar las imágenes de referencia por fotografías reales con descripción de cada pieza.",
    19: "Agregar en el visor la ficha de la obra y navegación a la siguiente imagen para mantener el interés.",
    23: "Publicar el calendario con fechas reales de celebraciones y eventos, y permitir agregarlos al calendario del celular.",
    25: "Publicar dirección exacta, mapa, horarios de apertura y de visitas guiadas (hoy están 'por confirmar').",
    26: "Publicar teléfono, correo y redes reales; hoy todos los datos de contacto dicen 'por confirmar'.",
    27: "Simplificar el formulario y mostrar ejemplos de formato en cada campo.",
    28: "Mostrar mensajes de validación claros junto a cada campo y conservar lo escrito al corregir.",
    29: "Conectar el formulario a un servicio real (p. ej. Netlify Forms) y mostrar confirmación de envío.",
    30: "Configurar el archivo _redirects de Netlify ('/*  /index.html  200') para que recargar o volver atrás no produzca 404.",
    31: "Reemplazar los textos 'Información por confirmar' y 'Contenido en construcción' por contenido real: horarios, historia, fichas de piezas y contactos. Es el punto donde más personas abandonan.",
    32: "Activar los enlaces del pie de página (redes, privacidad, aviso legal), que hoy apuntan a '#!'.",
}
RECOMENDACION_GENERAL = ("Revisar el contenido y la claridad de este paso, y ofrecer un enlace directo a la acción "
                         "que la persona busca (visitar, ver la agenda, contactar o explorar el museo).")


def tipos_de_usuario():
    """Lista ordenada y sin repetir de los tipos de usuario usados en los recorridos."""
    vistos = []
    for r in RECORRIDOS:
        if r["tipo_usuario"] not in vistos:
            vistos.append(r["tipo_usuario"])
    return vistos
