"""Índice de la documentación en texto, pensado para que una herramienta lo lea en segundos.

Genera, junto a la página HTML:
  INDICE.md          el mapa completo del proyecto en una sola página
  modulos/<id>.md    la ficha completa de cada módulo, para abrir solo la que hace falta
  indice.json        lo mismo en formato máquina

Leerlo cuesta mucho menos que recorrer el código fuente, porque ya viene resumido, ordenado y
con la autoría. No incluye correos.
"""
import json
import os
import re
import unicodedata

from .constantes import CARPETA
from .rama import _leer_json_de_rama, _rama_con_docs, sincronizar_docs


# ---------------------------------------------------------------- piezas pequeñas

def archivo_id(mid):
    """Nombre de archivo seguro para un id de módulo (nunca sale de la carpeta)."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(mid)).strip(".-") or "modulo"


def _lista(valor):
    if not valor:
        return []
    return [valor] if isinstance(valor, str) else list(valor)


def primera_frase(texto, maximo=200):
    texto = " ".join(str(texto or "").split())
    corte = texto.find(". ")
    frase = texto[: corte + 1] if 0 < corte < maximo else texto
    return frase if len(frase) <= maximo else frase[: maximo - 3].rstrip() + "..."


def _celda(texto):
    return str(texto or "").replace("|", "/").replace("\n", " ").strip()


def _quienes(autores):
    return ", ".join("%s (%d)" % (a["nombre"], a["commits"]) for a in autores) if autores else "sin datos"


def _md_lista(items, ordenada=False):
    items = _lista(items)
    if ordenada:
        return "\n".join("%d. %s" % (i + 1, x) for i, x in enumerate(items))
    return "\n".join("- %s" % x for x in items)


def _archivo_clave(a):
    if isinstance(a, dict):
        return "`%s`: %s" % (a.get("ruta", ""), a.get("para_que", ""))
    return "`%s`" % a


def _seccion(titulo, cuerpo):
    return "\n## %s\n\n%s\n" % (titulo, cuerpo) if cuerpo else ""


def _nombres_archivos(modulos):
    usados, res = set(), {}
    for m in modulos:
        base = archivo_id(m["id"])
        nombre, n = base, 2
        while nombre in usados:
            nombre, n = "%s-%d" % (base, n), n + 1
        usados.add(nombre)
        res[m["id"]] = "modulos/%s.md" % nombre
    return res


# ---------------------------------------------------------------- ficha de un módulo

def ficha_md(m, a, nombres):
    dep = ", ".join("%s (`%s`)" % (nombres.get(x, x), x) for x in _lista(m.get("depende_de"))) or "ninguno"
    out = ["# %s (`%s`)" % (m["nombre"], m["id"]), "",
           "- Ruta: `%s`" % m["ruta"],
           "- Verificado: %s" % ("sí" if m.get("verificado", True) else "no, tratar como hipótesis"),
           "- Depende de: %s" % dep]
    if a:
        out.append("- Principal autor del código: %s" % a["principal"])
        if a["colaboradores"]:
            out.append("- También lo tocaron: %s" % ", ".join(a["colaboradores"]))
        u = a["ultimo"]
        out.append("- Última modificación: %s, por %s (%s)" % (u["fecha"], u["autor"], u["asunto"]))
    doc = m.get("doc")
    if doc and doc.get("fecha"):
        out.append("- Documentado el %s (commit %s). Cambios de esta versión: %s"
                   % (doc["fecha"], doc.get("hasta", ""), _quienes(doc.get("autores"))))
    out += _cuerpo(m)
    vers = m.get("versiones") or []
    if vers:
        out += ["", "## Versiones anteriores (%d)" % len(vers), "",
                "Texto que tuvo este módulo antes. La versión vigente es la de arriba."]
        for v in vers:
            out += ["", "### Versión del %s (commit %s)" % (v.get("fecha", "sin fecha"), v.get("hasta", "")), "",
                    "Cambios de: %s" % _quienes(v.get("autores")), "", v.get("resumen", "")]
            cambio = _cambio_md(v.get("cambio"))
            if cambio:
                out += ["", cambio]
    return "\n".join(out).rstrip() + "\n"


def _cuerpo(m):
    texto = _seccion("En pocas palabras", m.get("resumen", ""))
    texto += _seccion("Por qué existe", m.get("por_que", ""))
    texto += _seccion("Cómo funciona", _md_lista(m.get("como_funciona"), ordenada=True))
    texto += _seccion("Datos que maneja", _md_lista(m.get("datos")))
    texto += _seccion("Reglas que cumple", _md_lista(m.get("reglas")))
    texto += _seccion("Por dónde empezar a leer el código",
                      _md_lista([_archivo_clave(x) for x in _lista(m.get("archivos_clave"))]))
    texto += _seccion("Cuidado con", _md_lista(m.get("cuidados")))
    texto += _seccion("Ejemplo", "```\n%s\n```" % m["ejemplo"] if m.get("ejemplo") else "")
    texto += _seccion("Qué cambió y por qué", _cambio_md(m.get("cambio")))
    return texto.rstrip("\n").split("\n")


def _cambio_md(c):
    if not c:
        return ""
    origen = {"commit": "según el mensaje del commit", "deducido": "deducido del código; el autor no lo explicó"}
    filas = ["- %s: %s" % (t, c[k]) for k, t in (("antes", "Antes"), ("ahora", "Ahora"), ("por_que", "Por qué")) if c.get(k)]
    if c.get("origen") in origen and filas:
        filas.append("- El porqué es %s." % origen[c["origen"]])
    return "\n".join(filas)


# ---------------------------------------------------------------- el índice

def generar(data):
    """Devuelve {ruta relativa: contenido} con INDICE.md, indice.json y las fichas."""
    p = data["proyecto"]
    gen = data.get("generado", {})
    aut = data.get("autoria", {"modulos": {}, "personas": {}, "posibles_alias": [], "prs_sin_confirmar": []})
    modulos = data.get("modulos", [])
    nombres = {m["id"]: m["nombre"] for m in modulos}
    ficha = _nombres_archivos(modulos)
    archivos = {ficha[m["id"]]: ficha_md(m, aut["modulos"].get(m["id"]), nombres) for m in modulos}

    md = ["# Índice de la documentación: %s" % p["nombre"], "", p.get("resumen", ""), ""]
    if p.get("stack"):
        md.append("- Tecnologías: %s" % ", ".join(p["stack"]))
    md.append("- Al día hasta el commit `%s` (%s, rama `%s`)."
              % (gen.get("commit", "")[:7], gen.get("fecha", ""), gen.get("ref", "")))
    md += ["", "## Cómo leer esto", "",
           "Está hecho para que una persona o una herramienta entienda el proyecto sin recorrer todo el código.", "",
           "1. Lee esta página primero: da el mapa completo.",
           "2. Para entender un módulo, abre su ficha (columna Ficha): explica qué es, por qué existe y cómo funciona.",
           "3. Para saber a qué módulo pertenece un archivo, usa el mapa de rutas.",
           "4. Abre el código fuente solo de los archivos clave del módulo que necesitas.",
           "5. Lo marcado como no verificado no se comprobó: trátalo como una hipótesis.",
           "", "## Módulos", "",
           "| Módulo | Ruta | Qué es | Depende de | Principal autor | Última modificación | Verificado | Ficha |",
           "|---|---|---|---|---|---|---|---|"]
    for m in modulos:
        a = aut["modulos"].get(m["id"])
        md.append("| %s (`%s`) | `%s` | %s | %s | %s | %s | %s | `%s` |" % (
            _celda(m["nombre"]), _celda(m["id"]), _celda(m["ruta"]), _celda(primera_frase(m.get("resumen"))),
            _celda(", ".join(_lista(m.get("depende_de"))) or "ninguno"),
            _celda(a["principal"] if a else "sin datos"), _celda(a["ultimo"]["fecha"] if a else "sin datos"),
            "sí" if m.get("verificado", True) else "no", ficha[m["id"]]))
    md += ["", "## Mapa de rutas", "", "Qué módulo es dueño de cada carpeta:", ""]
    md += ["- `%s` -> %s (`%s`)" % (m["ruta"].rstrip("/") + "/", m["nombre"], m["id"]) for m in modulos]
    deps = [(m["id"], d) for m in modulos for d in _lista(m.get("depende_de"))]
    md += ["", "## Dependencias", ""] + (["- %s -> %s" % (a, b) for a, b in deps] or ["Ninguna documentada."])
    md += ["", "## Flujos"]
    for f in data.get("flujos", []):
        md += ["", "### %s" % f["nombre"], ""]
        md += ["%d. %s -> %s: %s" % (i + 1, s["de"], s["a"], s.get("texto", "")) for i, s in enumerate(f["pasos"])]
    if not data.get("flujos"):
        md += ["", "Todavía no hay flujos documentados."]
    md += ["", "## Archivos clave", "", "Por dónde entrar al código:", ""]
    clave = [("%s (%s)" % (_archivo_clave(x), m["nombre"])) for m in modulos for x in _lista(m.get("archivos_clave"))]
    md += ["- %s" % c for c in clave] or ["No se documentaron."]
    md += ["", "## Equipo", ""]
    principales = {}
    for mid, d in aut["modulos"].items():
        principales.setdefault(d["principal"], []).append(nombres.get(mid, mid))
    for nombre, d in sorted(aut["personas"].items(), key=lambda kv: (-kv[1]["lineas"], kv[0])):
        mods = ", ".join(sorted(principales.get(nombre, []))) or "ninguno"
        md.append("- %s: principal en %s. %d %s, última actividad %s." % (
            nombre, mods, d["commits"], "commit" if d["commits"] == 1 else "commits", d["ultima"]))
    if aut.get("posibles_alias"):
        md += ["", "Posibles duplicados (la misma persona con otro nombre en Git): %s."
               % "; ".join("%s y %s" % (a, b) for a, b in aut["posibles_alias"])]
    md += ["", "## Últimos cambios", ""]
    for h in data.get("historial", [])[:5]:
        tocados = ", ".join(nombres.get(x, x) for x in h.get("modulos_tocados", [])) or "sin módulos indicados"
        md.append("- %s, %s (commits hasta %s). %s Módulos: %s. Hechos por: %s." % (
            h["fecha"], h["titulo"], h["hasta"], h.get("resumen", ""), tocados, _quienes(h.get("autores"))))
    if aut.get("prs_sin_confirmar"):
        md += ["", "## Autoría sin confirmar", "",
               "Estos PR entraron como un solo commit y Git los atribuye a quien los completó: %s."
               % ", ".join("PR %d (integrado por %s)" % (x["pr"], x["integrado_por"]) for x in aut["prs_sin_confirmar"])]
    md += ["", "## Pendiente de comprobar", ""]
    md += ["- %s" % x for x in data.get("sin_verificar", [])] or ["Nada marcado como pendiente."]
    archivos["INDICE.md"] = "\n".join(md).rstrip() + "\n"

    personas = [{"nombre": n, "commits": d["commits"], "ultima_actividad": d["ultima"],
                 "principal_en": sorted(principales.get(n, []))} for n, d in aut["personas"].items()]
    js = {"proyecto": {"nombre": p["nombre"], "resumen": p.get("resumen", ""), "stack": p.get("stack", [])},
          "generado": gen,
          "modulos": [{"id": m["id"], "nombre": m["nombre"], "ruta": m["ruta"], "que_es": primera_frase(m.get("resumen")),
                       "depende_de": _lista(m.get("depende_de")), "verificado": m.get("verificado", True),
                       "principal": (aut["modulos"].get(m["id"]) or {}).get("principal"),
                       "colaboradores": (aut["modulos"].get(m["id"]) or {}).get("colaboradores", []),
                       "ultima_modificacion": (aut["modulos"].get(m["id"]) or {}).get("ultimo"),
                       "archivos_clave": [{"ruta": x.get("ruta", ""), "para_que": x.get("para_que", "")} if isinstance(x, dict)
                                          else {"ruta": str(x), "para_que": ""} for x in _lista(m.get("archivos_clave"))],
                       "versiones_anteriores": len(m.get("versiones") or []), "ficha": ficha[m["id"]]}
                      for m in modulos],
          "flujos": [f["nombre"] for f in data.get("flujos", [])], "personas": personas,
          "sin_verificar": data.get("sin_verificar", [])}
    archivos["indice.json"] = json.dumps(js, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return archivos


def escribir(carpeta, data):
    """Escribe el índice y las fichas. Las fichas viejas se borran para no dejar módulos que ya no existen."""
    archivos = generar(data)
    modulos_dir = os.path.join(carpeta, "modulos")
    os.makedirs(modulos_dir, exist_ok=True)
    for viejo in os.listdir(modulos_dir):
        if viejo.endswith(".md"):
            os.remove(os.path.join(modulos_dir, viejo))
    for ruta, contenido in archivos.items():
        with open(os.path.join(carpeta, *ruta.split("/")), "w", encoding="utf-8", newline="\n") as f:
            f.write(contenido)
    return sorted(archivos)


# ---------------------------------------------------------------- lectura (para el comando indice)

def _normalizar(texto):
    sin = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in sin if not unicodedata.combining(c)).lower()


def _raiz(t):
    return re.sub(r"(es|s)$", "", t) if len(t) > 4 else t


def buscar(registros, consulta):
    """Misma lógica que el buscador de la página: todos los términos, sin tildes, con plurales."""
    terminos = [_raiz(t) for t in _normalizar(consulta).split()]
    if not terminos:
        return []
    res = []
    for r in registros:
        titulo, texto, antiguo = (_normalizar(r.get(k)) for k in ("titulo", "texto", "antiguo"))
        puntos, solo_antiguo, ok = 0, False, True
        for t in terminos:
            en_t, en_x, en_a = t in titulo, t in texto, t in antiguo
            if not (en_t or en_x or en_a):
                ok = False
                break
            puntos += (10 if en_t else 0) + (2 if en_x else 0) + (1 if en_a else 0)
            if not en_t and not en_x and en_a:
                solo_antiguo = True
        if ok:
            res.append({"id": r["id"], "tipo": r["tipo"], "titulo": r["titulo"], "puntos": puntos,
                        "solo_en_version_anterior": solo_antiguo})
    return sorted(res, key=lambda x: -x["puntos"])


def leer(repo, modulo=None, consulta=None):
    """Lee el índice directamente de la rama de documentación, sin tocar nada.

    Sin argumentos: INDICE.md. Con modulo: la ficha de ese módulo. Con consulta: resultados de búsqueda.
    """
    from .pagina import indice_busqueda
    from .gitutil import git
    sincronizar_docs(repo)  # si otra persona ya subió la documentación, se lee desde ahí
    rama = _rama_con_docs(repo)
    if not rama:
        raise SystemExit("Todavía no hay documentación en este proyecto. Documéntalo primero.")
    if consulta:
        data = _leer_json_de_rama(repo, rama, "data.json") or {}
        ficha = _nombres_archivos(data.get("modulos", []))
        res = buscar(indice_busqueda(data), consulta)
        for r in res:
            if r["id"].startswith("m-") and r["id"][2:] in ficha:
                r["ficha"] = ficha[r["id"][2:]]
        return res
    if modulo:
        data = _leer_json_de_rama(repo, rama, "data.json") or {}
        ficha = _nombres_archivos(data.get("modulos", []))
        if modulo not in ficha:
            raise SystemExit("No existe el módulo '%s'. Módulos: %s" % (modulo, ", ".join(sorted(ficha)) or "ninguno"))
        ruta = ficha[modulo]
    else:
        ruta = "INDICE.md"
    texto = git(repo, "show", "%s:%s/%s" % (rama, CARPETA, ruta), check=False)
    if not texto.strip():
        raise SystemExit("La documentación no tiene %s. Vuelve a construirla." % ruta)
    return texto
