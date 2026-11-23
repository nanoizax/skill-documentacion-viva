"""La página HTML: un solo archivo, sin recursos externos. El diseño vive en plantilla/."""
import html
import json
import os

_AQUI = os.path.dirname(os.path.abspath(__file__))


def _plantilla(nombre):
    with open(os.path.join(_AQUI, "plantilla", nombre), encoding="utf-8") as f:
        return f.read()


def e(x):
    return html.escape(str(x), quote=True)


def _n(cantidad, singular, plural):
    return "%d %s" % (cantidad, singular if cantidad == 1 else plural)


def _corto(txt, n):
    txt = str(txt)
    return txt if len(txt) <= n else txt[: n - 1].rstrip() + "..."


def _lista(valor):
    if not valor:
        return []
    return [valor] if isinstance(valor, str) else list(valor)


def svg_flujo(nombre, pasos):
    partes = []
    for p in pasos:
        for k in ("de", "a"):
            if p[k] not in partes:
                partes.append(p[k])
    ancho_col, margen, tope, fila = 200, 110, 46, 48
    ancho = 2 * margen + ancho_col * max(len(partes) - 1, 0)
    alto = tope + fila * len(pasos) + 24
    x = {n: margen + i * ancho_col for i, n in enumerate(partes)}
    o = ['<svg role="img" aria-label="Flujo: %s" viewBox="0 0 %d %d" style="width:100%%;max-width:%dpx" '
         'xmlns="http://www.w3.org/2000/svg">' % (e(nombre), ancho, alto, ancho),
         '<defs><marker id="p" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="punta"/></marker></defs>']
    for n, px in x.items():
        o.append('<line x1="%d" y1="34" x2="%d" y2="%d" class="vida"/>' % (px, px, alto - 8))
        o.append('<rect x="%d" y="6" width="160" height="28" rx="6" class="caja"/>' % (px - 80))
        o.append('<text x="%d" y="25" text-anchor="middle" class="cajat">%s</text>' % (px, e(_corto(n, 20))))
    for i, p in enumerate(pasos):
        y = tope + 18 + i * fila
        t = "%d. %s" % (i + 1, _corto(p.get("texto", ""), 34))
        if p["de"] == p["a"]:
            px = x[p["de"]]
            o.append('<path d="M%d %d h34 v16 h-34" class="flecha" marker-end="url(#p)"/>' % (px, y + 6))
            o.append('<text x="%d" y="%d" class="flujot">%s</text>' % (px + 40, y + 18, e(t)))
        else:
            x1, x2 = x[p["de"]], x[p["a"]]
            o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="flecha" marker-end="url(#p)"/>'
                     % (x1, y + 20, x2, y + 20))
            o.append('<text x="%d" y="%d" text-anchor="middle" class="flujot">%s</text>'
                     % ((x1 + x2) // 2, y + 12, e(t)))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- ficha de un módulo

def _quienes(autores):
    return ", ".join("%s (%d)" % (a["nombre"], a["commits"]) for a in autores) if autores else "sin datos"


def _seccion(titulo, cuerpo):
    return '<section class="sec"><h4>%s</h4>%s</section>' % (e(titulo), cuerpo) if cuerpo else ""


def _ul(items, ordenada=False):
    items = _lista(items)
    if not items:
        return ""
    etiqueta = "ol" if ordenada else "ul"
    return "<%s>%s</%s>" % (etiqueta, "".join("<li>%s</li>" % e(x) for x in items), etiqueta)


def _archivos_clave(archivos):
    filas = []
    for a in _lista(archivos):
        if isinstance(a, dict):
            filas.append("<li><code>%s</code> %s</li>" % (e(a.get("ruta", "")), e(a.get("para_que", ""))))
        else:
            filas.append("<li><code>%s</code></li>" % e(a))
    return "<ul>%s</ul>" % "".join(filas) if filas else ""


def _cambio(c):
    if not c:
        return ""
    origen = {"commit": "según el mensaje del commit",
              "deducido": "deducido del código; el autor no lo explicó"}.get(c.get("origen"), "")
    filas = ""
    for clave, titulo in (("antes", "Antes"), ("ahora", "Ahora"), ("por_que", "Por qué")):
        if c.get(clave):
            filas += "<tr><th>%s</th><td>%s</td></tr>" % (titulo, e(c[clave]))
    cola = '<p class="mut">El porqué es %s.</p>' % e(origen) if origen else ""
    return '<table class="cambio">%s</table>%s' % (filas, cola) if filas else ""


def _cuerpo_modulo(m, nombres_mod):
    """Todo lo que explica un módulo: sirve igual para la versión actual y las anteriores."""
    dep = ""
    if m.get("depende_de"):
        dep = '<p class="mut">Depende de: %s</p>' % ", ".join(
            '<a href="#m-%s">%s</a>' % (e(x), e(nombres_mod.get(x, x))) for x in m["depende_de"])
    ejemplo = '<pre>%s</pre>' % e(m["ejemplo"]) if m.get("ejemplo") else ""
    return ('<p class="lead">%s</p>' % e(m.get("resumen", "")) +
            _seccion("Por qué existe", "<p>%s</p>" % e(m["por_que"]) if m.get("por_que") else "") +
            _seccion("Cómo funciona", _ul(m.get("como_funciona"), ordenada=True)) +
            _seccion("Datos que maneja", _ul(m.get("datos"))) +
            _seccion("Reglas que cumple", _ul(m.get("reglas"))) +
            _seccion("Por dónde empezar a leer el código", _archivos_clave(m.get("archivos_clave"))) +
            _seccion("Cuidado con", _ul(m.get("cuidados"))) +
            _seccion("Ejemplo", ejemplo) +
            _seccion("Qué cambió y por qué", _cambio(m.get("cambio"))) + dep)


def _quien_modulo(m, a):
    if not a:
        return '<p class="mut">Sin historial de Git en esta ruta.</p>'
    u = a["ultimo"]
    out = '<p>Principal autor del código: <strong>%s</strong>.' % e(a["principal"])
    if a["colaboradores"]:
        out += " También lo tocaron: %s." % e(", ".join(a["colaboradores"]))
    out += '</p><p class="mut">Última modificación: %s, por %s (%s)</p>' % (
        e(u["fecha"]), e(u["autor"]), e(_corto(u["asunto"], 90)))
    doc = m.get("doc")
    if doc and doc.get("fecha"):
        out += '<p class="mut">Documentado el %s (commit %s). Cambios de esta versión: %s</p>' % (
            e(doc["fecha"]), e(doc.get("hasta", "")), e(_quienes(doc.get("autores"))))
    return out


def _versiones(m, nombres_mod):
    vers = m.get("versiones") or []
    if not vers:
        return ""
    items = []
    for v in vers:
        marca = "" if v.get("verificado", True) else ' <span class="chip">sin verificar</span>'
        items.append(
            '<div class="ver"><p><strong>%s</strong> <span class="mut">commit %s · cambios de: %s</span>%s</p>%s</div>'
            % (e(v.get("fecha", "sin fecha")), e(v.get("hasta", "")), e(_quienes(v.get("autores"))), marca,
               _cuerpo_modulo(v, nombres_mod)))
    return ('<details class="vers"><summary>Versiones anteriores (%d)</summary>%s</details>'
            % (len(vers), "".join(items)))


# ---------------------------------------------------------------- búsqueda

def _texto_modulo(m):
    partes = [m.get("nombre", ""), m.get("ruta", ""), m.get("resumen", ""), m.get("por_que", "")]
    for campo in ("como_funciona", "datos", "reglas", "cuidados"):
        partes += [str(x) for x in _lista(m.get(campo))]
    for a in _lista(m.get("archivos_clave")):
        partes += [a.get("ruta", ""), a.get("para_que", "")] if isinstance(a, dict) else [str(a)]
    partes.append(m.get("ejemplo", ""))
    c = m.get("cambio") or {}
    partes += [c.get("antes", ""), c.get("ahora", ""), c.get("por_que", "")]
    return " ".join(str(p) for p in partes if p)


def _indice(data, aut, nombres_mod, personas):
    reg = []
    for m in data.get("modulos", []):
        a = aut["modulos"].get(m["id"]) or {}
        gente = [a.get("principal", "")] + a.get("colaboradores", []) + [x["nombre"] for x in (m.get("doc") or {}).get("autores", [])]
        antiguo = " ".join(_texto_modulo(v) + " " + " ".join(x["nombre"] for x in v.get("autores", []))
                           for v in m.get("versiones", []))
        deps = " ".join(nombres_mod.get(x, x) for x in m.get("depende_de", []))
        reg.append({"id": "m-" + m["id"], "tipo": "Módulo", "titulo": m["nombre"],
                    "texto": _texto_modulo(m) + " " + " ".join(g for g in gente if g) + " " + deps,
                    "antiguo": antiguo})
    for i, (nombre, d) in enumerate(personas):
        reg.append({"id": "p-%d" % i, "tipo": "Persona", "titulo": nombre,
                    "texto": " ".join(r["asunto"] for r in d["recientes"]) + " " + " ".join(
                        nombres_mod.get(k, k) for k in d["modulos"])})
    for i, f in enumerate(data.get("flujos", [])):
        reg.append({"id": "f-%d" % i, "tipo": "Flujo", "titulo": f["nombre"],
                    "texto": " ".join("%s %s %s" % (p["de"], p["a"], p.get("texto", "")) for p in f["pasos"])})
    for i, a in enumerate(data.get("historial", [])):
        reg.append({"id": "h-%d" % i, "tipo": "Actividad", "titulo": "%s del %s" % (a["titulo"], a["fecha"]),
                    "texto": a.get("resumen", "") + " " + " ".join(x["nombre"] for x in a.get("autores", []))})
    return reg


def indice_busqueda(data):
    """Registros de búsqueda de toda la documentación (los usa la página y el comando indice)."""
    aut = data.get("autoria", {"modulos": {}, "personas": {}, "posibles_alias": []})
    nombres_mod = {m["id"]: m["nombre"] for m in data.get("modulos", [])}
    personas = sorted(aut["personas"].items(), key=lambda kv: (-kv[1]["lineas"], kv[0]))
    return _indice(data, aut, nombres_mod, personas)


def _json_seguro(obj):
    """JSON que se puede incrustar en un <script> sin romper la página."""
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


# ---------------------------------------------------------------- la página

def render(data):
    p = data["proyecto"]
    aut = data.get("autoria", {"modulos": {}, "personas": {}, "posibles_alias": []})
    gen = data.get("generado", {})
    nombres_mod = {m["id"]: m["nombre"] for m in data.get("modulos", [])}
    personas = sorted(aut["personas"].items(), key=lambda kv: (-kv[1]["lineas"], kv[0]))
    h = ['<!doctype html><html lang="es"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>Documentación de %s</title><style>%s</style></head><body>" % (e(p["nombre"]), _plantilla("estilos.css")),
         '<nav class="principal"><div class="barra"><div class="enlaces"><a href="#resumen">Resumen</a><a href="#equipo">Equipo</a>'
         '<a href="#modulos">Módulos</a><a href="#flujos">Flujos</a><a href="#historial">Historial</a>'
         '<a href="#pendiente">Sin verificar</a></div>'
         '<div class="busca"><label class="oculto" for="buscar">Buscar en la documentación</label>'
         '<input id="buscar" type="search" autocomplete="off" '
         'placeholder="Busca un módulo, una persona o una palabra (atajo: /)">'
         '<div id="resultados" hidden role="region" aria-live="polite"></div></div></div></nav>']
    ultima = data.get("historial", [{}])[0] if data.get("historial") else {}
    h.append('<header id="resumen"><h1>%s</h1><p class="res">%s</p>' % (e(p["nombre"]), e(p.get("resumen", ""))))
    if p.get("stack"):
        h.append('<div class="chips">%s</div>' % "".join('<span class="chip">%s</span>' % e(s) for s in p["stack"]))
    h.append('<div class="estado"><strong>Al día hasta el commit <code>%s</code></strong> (%s, rama <code>%s</code>).<br>'
             'Última actualización cubre los cambios de: %s.</div></header><main>'
             % (e(gen.get("commit", "")[:7]), e(gen.get("fecha", "")), e(gen.get("ref", "")),
                e(_quienes(ultima.get("autores")))))

    h.append('<h2 id="equipo">Equipo</h2>')
    if aut["posibles_alias"]:
        pares = "; ".join("%s y %s" % (e(a), e(b)) for a, b in aut["posibles_alias"])
        h.append('<div class="aviso">Puede que estas personas aparezcan duplicadas con otro nombre en Git: %s. '
                 'Se arregla con un archivo <code>.mailmap</code> en la raíz del proyecto.</div>' % pares)
    if aut.get("prs_sin_confirmar"):
        por_quien = {}
        for x in aut["prs_sin_confirmar"]:
            por_quien.setdefault(x["integrado_por"], []).append("PR %d" % x["pr"])
        detalle = "; ".join("%s (integrados por %s)" % (", ".join(v), e(k)) for k, v in por_quien.items())
        h.append('<div class="aviso">Hay cambios que entraron como un solo commit de tipo Merged PR. Git los atribuye '
                 'a quien completó el PR, que puede no ser quien lo escribió: %s. Si sabes quién los escribió, '
                 'indícalo y quedará guardado en <code>autores.json</code>, dentro de esta carpeta.</div>' % detalle)
    h.append('<div class="grid">')
    principales = {}
    for mid, d in aut["modulos"].items():
        principales.setdefault(d["principal"], []).append(mid)
    for i, (nombre, d) in enumerate(personas):
        mods = ", ".join(e(nombres_mod.get(m, m)) for m in sorted(principales.get(nombre, []))) or "ninguno"
        rec = "".join("<li><span class='mut'>%s</span> %s</li>" % (e(r["fecha"]), e(_corto(r["asunto"], 80)))
                      for r in d["recientes"])
        h.append('<div class="card" id="p-%d"><h3>%s</h3><p class="mut">%s · %s a %s</p>'
                 '<p>Principal autor del código en: %s</p><p class="mut">Actividad reciente</p><ul>%s</ul>'
                 '<button type="button" class="enlace" data-buscar-persona="%s">Ver todo lo que tocó</button></div>'
                 % (i, e(nombre), _n(d["commits"], "commit", "commits"), e(d["primera"]), e(d["ultima"]), mods, rec,
                    e(nombre)))
    h.append("</div>")

    h.append('<h2 id="modulos">Módulos</h2>')
    if data.get("modulos"):
        orden = sorted(data["modulos"], key=lambda m: m["nombre"].lower())
        h.append('<nav class="indice" aria-label="Índice de módulos">%s</nav>' % "".join(
            '<a href="#m-%s">%s</a>' % (e(m["id"]), e(m["nombre"])) for m in orden))
    for m in data.get("modulos", []):
        marca = '' if m.get("verificado", True) else ' <span class="chip">sin verificar</span>'
        h.append('<article class="modulo" id="m-%s"><h3>%s%s</h3><p class="ruta"><code>%s</code></p>%s'
                 '<div class="quien"><h4>Quién lo hizo</h4>%s</div>%s</article>'
                 % (e(m["id"]), e(m["nombre"]), marca, e(m["ruta"]), _cuerpo_modulo(m, nombres_mod),
                    _quien_modulo(m, aut["modulos"].get(m["id"])), _versiones(m, nombres_mod)))

    h.append('<h2 id="flujos">Flujos</h2>')
    if not data.get("flujos"):
        h.append('<p class="mut">Todavía no hay flujos documentados.</p>')
    for i, f in enumerate(data.get("flujos", [])):
        h.append('<div class="flujo" id="f-%d"><h3>%s</h3>%s</div>' % (i, e(f["nombre"]), svg_flujo(f["nombre"], f["pasos"])))

    h.append('<h2 id="historial">Historial de la documentación</h2>')
    for i, a in enumerate(data.get("historial", [])):
        rango = ("%s a %s" % (a["desde"], a["hasta"])) if a.get("desde") else ("hasta %s" % a["hasta"])
        mods = ", ".join(e(nombres_mod.get(x, x)) for x in a.get("modulos_tocados", []))
        h.append('<div class="hist" id="h-%d"><strong>%s</strong> <span class="mut">%s · commits %s · %s</span>'
                 '<p>%s</p><p class="mut">Hechos por: %s%s</p></div>'
                 % (i, e(a["titulo"]), e(a["fecha"]), e(rango), _n(a["commits"], "cambio", "cambios"),
                    e(a.get("resumen", "")), e(_quienes(a.get("autores"))),
                    ("<br>Módulos tocados: %s" % mods) if mods else ""))

    h.append('<h2 id="pendiente">Sin verificar</h2>')
    if data.get("sin_verificar"):
        h.append("<ul>%s</ul>" % "".join("<li>%s</li>" % e(x) for x in data["sin_verificar"]))
    else:
        h.append('<p class="mut">No se marcó nada como pendiente de comprobar.</p>')
    h.append("</main><footer>Esta página se genera desde el historial de Git. Los nombres, las fechas y las cifras "
             "salen de ahí, no de una opinión. No incluye correos. Ábrela con doble clic, no necesita internet. "
             "Para leerla con una herramienta de desarrollo, usa INDICE.md, en esta misma carpeta."
             "</footer>")
    h.append('<script type="application/json" id="indice">%s</script>' % _json_seguro(_indice(data, aut, nombres_mod, personas)))
    h.append("<script>%s</script></body></html>" % _plantilla("buscador.js"))
    return "".join(h)
