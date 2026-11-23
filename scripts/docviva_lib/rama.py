"""Estado de la documentación y rama aparte (en un worktree)."""
import json
import os

from .autoria import commits, modulo_de
from .constantes import *  # noqa: F401,F403
from .gitutil import _correr, _ruta_worktree, correr_red, existe_ref, git, git_ok, nombre_ref, ref_principal, sha


def sincronizar_docs(repo):
    """Mira en el remoto si ya existe la rama de documentación y, si existe, la trae (solo esa rama).

    Es lo que evita analizar de nuevo todo el proyecto cuando otra persona ya lo documentó.
    Devuelve (hay_remoto, verificado): verificado es falso si no se pudo preguntar al remoto.
    """
    if not git(repo, "remote", check=False).strip():
        return False, True
    r = correr_red(repo, ["ls-remote", "--exit-code", "--heads", "origin", RAMA])
    if r.returncode == 2:
        return True, True  # el remoto responde y no tiene la rama de documentación
    if r.returncode != 0:
        return True, False  # sin conexión, sin permiso o se agotó la espera
    f = correr_red(repo, ["fetch", "--quiet", "origin", "+refs/heads/%s:refs/remotes/origin/%s" % (RAMA, RAMA)])
    return True, f.returncode == 0


def _rama_con_docs(repo):
    local = existe_ref(repo, "refs/heads/" + RAMA)
    remota = existe_ref(repo, "refs/remotes/origin/" + RAMA)
    if local and remota:
        if git_ok(repo, "merge-base", "--is-ancestor", "refs/heads/" + RAMA, "refs/remotes/origin/" + RAMA):
            return "refs/remotes/origin/" + RAMA
        return "refs/heads/" + RAMA
    if local:
        return "refs/heads/" + RAMA
    if remota:
        return "refs/remotes/origin/" + RAMA
    return None


def _leer_json_de_rama(repo, rama, archivo):
    txt = git(repo, "show", "%s:%s/%s" % (rama, CARPETA, archivo), check=False)
    try:
        return json.loads(txt) if txt.strip() else None
    except ValueError:
        return None


def estado(repo, ref=None):
    ref = ref_principal(repo, ref)
    if not existe_ref(repo, ref):
        raise SystemExit("No hay commits en %s. Haz al menos un commit antes de documentar." % ref)
    head = sha(repo, ref)
    hay_remoto, verificado = sincronizar_docs(repo)  # primero se pregunta al remoto: quizá ya está documentado
    rama = _rama_con_docs(repo)
    meta = _leer_json_de_rama(repo, rama, "meta.json") if rama else None
    local = existe_ref(repo, "refs/heads/" + RAMA)
    remota = existe_ref(repo, "refs/remotes/origin/" + RAMA)
    res = {"ref": nombre_ref(repo, ref), "head": head[:7], "tiene_remoto": hay_remoto,
           "remoto_verificado": verificado,
           "fuente": "local+remota" if local and remota else "local" if local else "remota" if remota else None,
           "documentada": bool(meta), "primera_vez": not meta and verificado,
           "ultimo_commit": None, "commits_nuevos": 0,
           "desactualizada": False, "historia_reescrita": False, "archivos_cambiados": [],
           "total_archivos_cambiados": 0, "modulos_tocados": [], "autores_nuevos": [],
           "docs_actualizada_por": None, "docs_fecha": None,
           "tamano": {"archivos": len(git(repo, "ls-tree", "-r", "--name-only", ref).splitlines()),
                      "commits": int(git(repo, "rev-list", "--count", ref).strip() or 0)}}
    if not meta:
        if verificado:
            res["accion"] = "analisis_completo"
            res["respuesta"] = ("No está documentado: ninguna rama, ni en este equipo ni en el remoto, tiene la "
                                "documentación de esta skill. Puedo crear la rama %s y documentarlo. Queda en tu "
                                "equipo y tú decides si la subes." % RAMA)
            res["mensaje"] = ("Ninguna rama tiene la documentación: es la primera vez. Lee todo el proyecto para "
                              "crear la base, avisando antes del tamaño.")
        else:
            res["accion"] = "confirmar_con_el_usuario"
            res["respuesta"] = ("No pude comprobar si está documentado: el remoto no respondió. Puedo reintentar con "
                                "conexión o crear la documentación igualmente.")
            res["mensaje"] = ("No se pudo preguntar al remoto si ya existe la rama %s. No analices todo el proyecto "
                              "todavía: pregunta al usuario si hay conexión o si quiere crear la base igualmente." % RAMA)
        return res
    ultimo = meta.get("ultimo_commit", "")
    res["ultimo_commit"] = ultimo[:7]
    res["docs_actualizada_por"] = git(repo, "log", "-1", "--format=%aN", rama, "--", CARPETA).strip() or None
    res["docs_fecha"] = git(repo, "log", "-1", "--format=%cs", rama, "--", CARPETA).strip() or None
    if not ultimo or not existe_ref(repo, ultimo):
        res["historia_reescrita"], res["desactualizada"] = True, True
        res["accion"] = "rehacer_base_con_permiso"
        res["respuesta"] = ("Sí está documentado, pero la historia del repositorio cambió y esa documentación ya no "
                            "corresponde al código actual.")
        res["mensaje"] = ("La historia del repositorio cambió y el commit documentado ya no existe. Pregunta al usuario "
                          "si rehaces la base completa (gasta cuota) o si mantienes la documentación actual.")
        return res
    # commits de esta rama que la documentación todavía no vio; sirve aunque se haya
    # documentado desde otra rama
    res["commits_nuevos"] = int(git(repo, "rev-list", "--count", "%s..%s" % (ultimo, ref)).strip() or 0)
    res["desactualizada"] = res["commits_nuevos"] > 0
    if res["desactualizada"]:
        cambiados = git(repo, "diff", "--name-only", "%s...%s" % (ultimo, ref)).splitlines()
        res["total_archivos_cambiados"] = len(cambiados)
        res["archivos_cambiados"] = cambiados[:200]
        data = _leer_json_de_rama(repo, rama, "data.json") or {}
        mods = {m["id"]: m["ruta"] for m in data.get("modulos", [])}
        res["modulos_tocados"] = sorted({modulo_de(f, mods) for f in cambiados})
        res["autores_nuevos"] = sorted({c["autor"] for c in commits(repo, ref, ultimo)})
    donde = {"remota": "en el remoto", "local": "en este equipo", "local+remota": "en este equipo y en el remoto"}[res["fuente"]]
    if res["desactualizada"]:
        res["accion"] = "actualizar"
        res["respuesta"] = ("Sí está documentado (%s, rama %s), pero quedó atrás: el código avanzó %d %s desde el "
                            "commit %s." % (donde, RAMA, res["commits_nuevos"],
                                            "commit" if res["commits_nuevos"] == 1 else "commits", res["ultimo_commit"]))
        res["mensaje"] = ("La documentación ya existe (%s). No releas el proyecto: lee el índice y analiza solo los "
                          "módulos de modulos_tocados." % donde)
    else:
        res["accion"] = "leer_documentacion"
        res["respuesta"] = ("Sí está documentado (%s, rama %s), al día hasta el commit %s. La actualizó %s el %s."
                            % (donde, RAMA, res["ultimo_commit"], res["docs_actualizada_por"] or "alguien",
                               res["docs_fecha"] or "fecha desconocida"))
        res["mensaje"] = ("La documentación ya existe (%s) y está al día. No releas el código: lee el índice con el "
                          "comando indice." % donde)
    return res


def preparar_rama(repo, ref=None):
    """Deja lista la rama de documentación en un worktree aparte, sin tocar tu rama de trabajo.

    La rama solo contiene documentación (nace de un árbol vacío): no mezcla código con nadie y no
    choca con los PR. Si otra persona ya la subió, se pone al día con ella.
    """
    ref = ref_principal(repo, ref)
    correr_red(repo, ["fetch", "--quiet", "origin"])  # si no hay conexión, se sigue con lo que hay en el equipo
    if not existe_ref(repo, ref):
        raise SystemExit("No hay commits en %s." % ref)
    local = existe_ref(repo, "refs/heads/" + RAMA)
    remota = existe_ref(repo, "refs/remotes/origin/" + RAMA)
    if not local:
        if remota:
            git(repo, "branch", RAMA, "origin/" + RAMA)
        else:
            vacio = _correr(repo, ["mktree"], entrada="").stdout.strip()
            inicio = git(repo, "commit-tree", vacio, "-m", "Inicio de la documentación del proyecto").strip()
            git(repo, "branch", RAMA, inicio)
    git(repo, "worktree", "prune", check=False)
    wt = _ruta_worktree(repo)
    if not os.path.isdir(wt):
        git(repo, "worktree", "add", wt, RAMA)
    actual = git(wt, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if actual != RAMA:
        raise SystemExit("El worktree de documentación está en '%s', no en %s." % (actual, RAMA))
    if remota and not git_ok(wt, "merge-base", "--is-ancestor", "origin/" + RAMA, "HEAD"):
        if not git_ok(wt, "merge", "--no-edit", "origin/" + RAMA):
            git(wt, "merge", "--abort", check=False)
            raise SystemExit("Conflicto al unir tu documentación con la de origin/%s. "
                             "Resuélvelo a mano en %s." % (RAMA, wt))
    return wt


def confirmar(repo, mensaje=None, ref=None):
    ref = ref_principal(repo, ref)
    wt = _ruta_worktree(repo)
    if not os.path.isdir(wt):
        raise SystemExit("Falta la rama de documentación. Ejecuta primero: preparar-rama")
    if not git(wt, "config", "user.name", check=False).strip() or not git(wt, "config", "user.email", check=False).strip():
        raise SystemExit("Git no tiene user.name o user.email. Configúralos con tu nombre real y vuelve a intentar.")
    git(wt, "add", CARPETA)
    if git_ok(wt, "diff", "--cached", "--quiet"):
        return {"commit": None, "mensaje": "Sin cambios que confirmar."}
    mensaje = mensaje or "Documentación del proyecto al día hasta %s" % sha(repo, ref)[:7]
    git(wt, "commit", "-m", mensaje)
    return {"commit": sha(wt, "HEAD")[:7], "rama": RAMA,
            "mensaje": "Commit local hecho. No se hizo push: súbela tú cuando quieras."}


def abrir(repo, navegador=True):
    """Abre la documentación en el navegador con doble clic equivalente: sin servidor ni internet."""
    ruta = os.path.join(_ruta_worktree(repo), *CARPETA.split("/"), "index.html")
    if not os.path.isfile(ruta):
        raise SystemExit("Todavía no hay documentación generada. Ejecuta preparar-rama y construir.")
    if navegador:
        import pathlib
        import webbrowser
        webbrowser.open(pathlib.Path(ruta).resolve().as_uri())
    return {"html": ruta, "abierto": bool(navegador)}
