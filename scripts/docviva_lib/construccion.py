"""Une el análisis con la autoría y escribe data.json, meta.json e index.html."""
import datetime
import json
import os

from .autoria import autoria, commits, modulo_de
from .calidad import avisos_calidad
from .constantes import *  # noqa: F401,F403
from .gitutil import _ruta_worktree, existe_ref, git_ok, nombre_ref, ref_principal, sha
from .indice import escribir as escribir_indice
from .pagina import render


def _cargar(ruta, defecto):
    if os.path.isfile(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return defecto


def _guardar(ruta, obj):
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _contar_autores(detalle, autores_pr):
    cuenta = {}
    for d in detalle:
        nombre = autores_pr.get(str(d["pr"]), d["autor"]) if d.get("pr") is not None else d["autor"]
        cuenta[nombre] = cuenta.get(nombre, 0) + 1
    return [{"nombre": n, "commits": v} for n, v in sorted(cuenta.items(), key=lambda x: (-x[1], x[0]))]


_CAMPOS_VERSION = ("nombre", "ruta", "resumen", "por_que", "como_funciona", "datos", "reglas",
                   "archivos_clave", "cuidados", "ejemplo", "cambio", "depende_de", "verificado")


def _valor(m, campo):
    """Un campo ausente, vacío o lista vacía cuenta igual: no es un cambio de documentación."""
    v = m.get(campo)
    if campo == "verificado":
        return True if v is None else bool(v)
    return None if v in (None, "", [], {}) else v


def _cambio_modulo(a, b):
    """¿La documentación del módulo cambió de verdad? Si no, no se archiva otra versión."""
    def clave(m):
        return json.dumps({k: _valor(m, k) for k in _CAMPOS_VERSION}, sort_keys=True, ensure_ascii=False)
    return clave(a) != clave(b)


def _version(previo):
    """Foto de un módulo antes de que su documentación cambie, con quiénes la tocaron."""
    v = {k: previo.get(k) for k in _CAMPOS_VERSION if k in previo}
    v.update(previo.get("doc") or {})
    return v


def construir(repo, entrada_ruta, ref=None):
    ref = ref_principal(repo, ref)
    wt = _ruta_worktree(repo)
    if not os.path.isdir(wt):
        raise SystemExit("Falta la rama de documentación. Ejecuta primero: preparar-rama")
    with open(entrada_ruta, encoding="utf-8") as f:
        entrada = json.load(f)
    carpeta = os.path.join(wt, *CARPETA.split("/"))
    os.makedirs(carpeta, exist_ok=True)
    data = _cargar(os.path.join(carpeta, "data.json"), {})
    meta = _cargar(os.path.join(carpeta, "meta.json"), {})

    proyecto = dict(data.get("proyecto", {}))
    proyecto.update(entrada.get("proyecto", {}))
    if not proyecto.get("nombre"):
        raise SystemExit("Falta proyecto.nombre en el análisis.")
    viejos = {m["id"]: m for m in data.get("modulos", [])}
    modulos = dict(viejos)
    cambiados = set()
    for m in entrada.get("modulos", []):
        for campo in ("id", "nombre", "ruta", "resumen"):
            if not m.get(campo):
                raise SystemExit("Un módulo no tiene '%s': %s" % (campo, json.dumps(m, ensure_ascii=False)))
        nuevo = {k: v for k, v in m.items() if k not in ("versiones", "doc")}
        previo = viejos.get(m["id"])
        if previo and not _cambio_modulo(previo, nuevo):
            nuevo["doc"] = previo.get("doc")  # sin cambios reales: no se crea otra versión
            nuevo["versiones"] = previo.get("versiones", [])
        else:
            versiones = list(previo.get("versiones", [])) if previo else []
            if previo:
                versiones.insert(0, _version(previo))
            nuevo["versiones"] = versiones[:MAX_VERSIONES]
            cambiados.add(m["id"])
        modulos[m["id"]] = nuevo
    flujos = {f["nombre"]: f for f in data.get("flujos", [])}
    for f in entrada.get("flujos", []):
        flujos[f["nombre"]] = f
    sin_verificar = entrada.get("sin_verificar", data.get("sin_verificar", []))

    ruta_autores = os.path.join(carpeta, "autores.json")
    autores_pr = _cargar(ruta_autores, {})
    autores_pr.update({str(k): v for k, v in entrada.get("autores_pr", {}).items()})
    if autores_pr:
        _guardar(ruta_autores, autores_pr)

    head = sha(repo, ref)
    anterior = meta.get("ultimo_commit")
    if anterior and not existe_ref(repo, anterior):
        anterior = None  # la historia se reescribió: se documenta desde cero
    historial = list(data.get("historial", []))
    nuevos = commits(repo, ref, anterior) if head != anterior else []
    ruta_mods = {mid: m["ruta"] for mid, m in modulos.items()}
    for mid in cambiados:  # quién tocó el código de este módulo en la actividad que se documenta
        detalle = [{"autor": c["autor"], "pr": c["pr"]} for c in nuevos
                   if any(modulo_de(f, ruta_mods) == mid for f, _ in c["archivos"])]
        modulos[mid]["doc"] = {"hasta": head[:7], "fecha": datetime.date.today().isoformat(), "detalle": detalle}
    for m in modulos.values():  # las correcciones de autoría también se aplican a las versiones viejas
        for v in [m.get("doc")] + list(m.get("versiones", [])):
            if v and "detalle" in v:
                v["autores"] = _contar_autores(v["detalle"], autores_pr)
    if head != anterior:
        act = entrada.get("actividad", {})
        historial.insert(0, {
            "fecha": datetime.date.today().isoformat(),
            "titulo": "Actualización" if anterior else "Documentación base",
            "desde": anterior[:7] if anterior else None, "hasta": head[:7],
            "commits": len(nuevos),
            "detalle": [{"autor": c["autor"], "pr": c["pr"]} for c in nuevos],
            "resumen": act.get("resumen", ""),
            "modulos_tocados": act.get("modulos_tocados", [])})
    for h in historial:  # las correcciones de autoría también se aplican al pasado
        if "detalle" in h:
            h["autores"] = _contar_autores(h["detalle"], autores_pr)

    aut = autoria(repo, ref, {mid: m["ruta"] for mid, m in modulos.items()}, autores_pr=autores_pr)
    data = {"proyecto": proyecto, "modulos": list(modulos.values()), "flujos": list(flujos.values()),
            "sin_verificar": sin_verificar, "historial": historial, "autoria": aut,
            "generado": {"commit": head, "fecha": datetime.date.today().isoformat(), "ref": nombre_ref(repo, ref)}}
    meta = {"ultimo_commit": head, "ref": nombre_ref(repo, ref), "version": 1}
    _guardar(os.path.join(carpeta, "data.json"), data)
    _guardar(os.path.join(carpeta, "meta.json"), meta)
    ruta_html = os.path.join(carpeta, "index.html")
    with open(ruta_html, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(data))
    escribir_indice(carpeta, data)  # INDICE.md, indice.json y las fichas por módulo
    avisos = avisos_calidad(entrada.get("modulos", []), set(modulos), set(viejos))
    return {"html": ruta_html, "modulos": len(modulos), "flujos": len(flujos), "commit": head[:7],
            "prs_sin_confirmar": [x["pr"] for x in aut["prs_sin_confirmar"]], "avisos": avisos}
