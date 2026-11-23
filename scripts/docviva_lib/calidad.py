"""Avisos de calidad sobre el análisis. No bloquean: le dicen a quien analiza qué reforzar."""

PALABRAS_MINIMAS_RESUMEN = 25


def _palabras(texto):
    return len((texto or "").split())


def _lista(valor):
    if not valor:
        return []
    return [valor] if isinstance(valor, str) else list(valor)


def avisos_calidad(modulos_entrada, ids_conocidos, ids_previos):
    """Devuelve [{modulo, aviso}] para los módulos que se acaban de documentar.

    ids_previos: módulos que ya estaban documentados; solo a esos se les pide explicar qué cambió.
    """
    avisos = []

    def avisar(m, texto):
        avisos.append({"modulo": m["id"], "aviso": texto})

    for m in modulos_entrada:
        resumen = (m.get("resumen") or "").strip()
        n = _palabras(resumen)
        if n < PALABRAS_MINIMAS_RESUMEN:
            avisar(m, "El resumen tiene %d palabras. Explica qué es, para quién es y por qué existe, "
                      "de forma que lo entienda un junior (mínimo %d)." % (n, PALABRAS_MINIMAS_RESUMEN))
        if resumen.lower().rstrip(".") in (m.get("nombre", "").lower(), "módulo de " + m.get("nombre", "").lower()):
            avisar(m, "El resumen solo repite el nombre del módulo.")
        if not m.get("por_que"):
            avisar(m, "Falta por_que: por qué existe este módulo y qué problema resuelve.")
        if not _lista(m.get("como_funciona")):
            avisar(m, "Falta como_funciona: el recorrido paso a paso, en lenguaje claro.")
        if not _lista(m.get("archivos_clave")):
            avisar(m, "Faltan archivos_clave: qué archivos abrir primero y para qué sirve cada uno.")
        if m["id"] in ids_previos:
            cambio = m.get("cambio") or {}
            if not (cambio.get("antes") and cambio.get("ahora") and cambio.get("por_que")):
                avisar(m, "Falta cambio con antes, ahora y por_que: qué hacía antes, qué hace ahora y por qué cambió.")
            elif cambio.get("origen") not in ("commit", "deducido"):
                avisar(m, "En cambio.origen indica si el porqué viene del mensaje del commit ('commit') "
                          "o lo dedujiste del código ('deducido').")
        for dep in _lista(m.get("depende_de")):
            if dep not in ids_conocidos:
                avisar(m, "depende_de menciona '%s', que no es un módulo documentado." % dep)
    return avisos
