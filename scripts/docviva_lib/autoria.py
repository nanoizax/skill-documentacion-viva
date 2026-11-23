"""Quién hizo qué, sacado del historial de Git."""
import re

from .constantes import *  # noqa: F401,F403
from .gitutil import git


_PR_AZURE = re.compile(r"^Merged PR (\d+)")


_PR_SQUASH = re.compile(r"\(#(\d+)\)\s*$")


def numero_pr(asunto):
    """(número, tipo) si el commit es un PR integrado en un solo commit; si no, (None, None).

    Azure DevOps ("Merged PR 12: ...") atribuye el commit a quien completó el PR, no a quien
    lo escribió; por eso se marca aparte. El squash de GitHub conserva al autor del PR.
    """
    m = _PR_AZURE.match(asunto)
    if m:
        return int(m.group(1)), "azure"
    m = _PR_SQUASH.search(asunto)
    if m:
        return int(m.group(1)), "squash"
    return None, None


def commits(repo, ref, desde=None):
    """Commits sin merges, del más nuevo al más viejo, con líneas tocadas por archivo."""
    rango = "%s..%s" % (desde, ref) if desde else ref
    fmt = "%x1e%H%x1f%aN%x1f%aE%x1f%aI%x1f%s"
    salida = git(repo, "log", "--no-merges", "--no-renames", "--numstat", "--format=" + fmt, rango)
    res = []
    for bloque in salida.split(SEP_R)[1:]:
        lineas = bloque.split("\n")
        h, autor, correo, fecha, asunto = lineas[0].split(SEP_C, 4)
        archivos = []
        for linea in lineas[1:]:
            partes = linea.split("\t", 2)
            if len(partes) < 3:
                continue
            a, d, ruta = partes
            n = (int(a) if a.isdigit() else 0) + (int(d) if d.isdigit() else 0)
            archivos.append((ruta, n))
        pr, tipo = numero_pr(asunto.strip())
        res.append({"hash": h, "autor": autor.strip(), "correo": correo.strip(),
                    "fecha": fecha[:10], "asunto": asunto.strip(), "archivos": archivos,
                    "pr": pr, "pr_tipo": tipo})
    return res


def modulo_de(ruta, modulos):
    """Módulo cuya ruta es el prefijo más largo del archivo."""
    mejor, largo = SIN_MODULO, -1
    for mid, base in modulos.items():
        base = base.strip("/")
        if base in ("", "."):
            coincide, n = True, 0
        else:
            coincide, n = (ruta == base or ruta.startswith(base + "/")), len(base)
        if coincide and n > largo:
            mejor, largo = mid, n
    return mejor


def _tokens(nombre):
    return {t for t in "".join(c.lower() if c.isalnum() else " " for c in nombre).split() if len(t) > 1}


def posibles_alias(correos_por_autor):
    """Pares de nombres que parecen la misma persona (para sugerir un .mailmap)."""
    nombres = sorted(correos_por_autor)
    pares = []
    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            ta, tb = _tokens(a), _tokens(b)
            mismo_tokens = bool(ta) and bool(tb) and (ta <= tb or tb <= ta)
            local = lambda c: c.split("@")[0].lower()
            mismo_correo = any(local(x) == local(y) for x in correos_por_autor[a] for y in correos_por_autor[b])
            if mismo_tokens or mismo_correo:
                pares.append([a, b])
    return pares


def autoria(repo, ref, modulos, desde=None, autores_pr=None):
    """Quién hizo qué. Los merges no cuentan como autoría; solo los commits reales.

    autores_pr corrige la atribución de los PR integrados en un solo commit: {"916": "Nombre"}.
    """
    autores_pr = {str(k): v for k, v in (autores_pr or {}).items()}
    por_mod, personas, correos, sin_confirmar = {}, {}, {}, {}
    for c in commits(repo, ref, desde):
        autor = c["autor"]
        if c["pr"] is not None and str(c["pr"]) in autores_pr:
            autor = autores_pr[str(c["pr"])]
        else:
            correos.setdefault(autor, set()).add(c["correo"])
            if c["pr_tipo"] == "azure":
                sin_confirmar[c["pr"]] = autor
        p = personas.setdefault(autor, {"commits": 0, "lineas": 0, "primera": c["fecha"],
                                        "ultima": c["fecha"], "modulos": {}, "recientes": []})
        p["commits"] += 1
        p["primera"] = c["fecha"]  # se recorre del más nuevo al más viejo
        if len(p["recientes"]) < 5:
            p["recientes"].append({"fecha": c["fecha"], "asunto": c["asunto"]})
        tocados = set()
        for ruta, n in c["archivos"]:
            m = modulo_de(ruta, modulos)
            d = por_mod.setdefault(m, {"autores": {}, "ultimo": None})
            a = d["autores"].setdefault(autor, {"commits": set(), "lineas": 0})
            a["lineas"] += n
            a["commits"].add(c["hash"])
            p["lineas"] += n
            p["modulos"][m] = p["modulos"].get(m, 0) + n
            if d["ultimo"] is None:
                d["ultimo"] = {"fecha": c["fecha"], "autor": autor, "asunto": c["asunto"]}
            tocados.add(m)
    modulos_out = {}
    for m, d in por_mod.items():
        lista = sorted(({"nombre": n, "commits": len(v["commits"]), "lineas": v["lineas"]}
                        for n, v in d["autores"].items()),
                       key=lambda x: (-x["lineas"], -x["commits"], x["nombre"]))
        modulos_out[m] = {"principal": lista[0]["nombre"],
                          "colaboradores": [x["nombre"] for x in lista[1:]],
                          "autores": lista, "ultimo": d["ultimo"]}
    return {"modulos": modulos_out, "personas": personas,
            "posibles_alias": posibles_alias(correos),
            "prs_sin_confirmar": [{"pr": n, "integrado_por": q}
                                  for n, q in sorted(sin_confirmar.items(), reverse=True)]}
