"""Llamadas a Git."""
import os
import subprocess

from .constantes import *  # noqa: F401,F403


def _correr(repo, args, entrada=None):
    return subprocess.run(
        ["git", "-c", "core.quotepath=off", "-C", repo, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", input=entrada,
    )


def correr_red(repo, args, espera=30):
    """Git contra el remoto: nunca pide contraseña ni se queda colgado. Devuelve el proceso (124 si se agotó la espera)."""
    entorno = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        return subprocess.run(["git", "-c", "core.quotepath=off", "-C", repo, *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=entorno, timeout=espera)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, "", "tiempo de espera agotado")


def git(repo, *args, check=True):
    r = _correr(repo, args)
    if check and r.returncode != 0:
        raise SystemExit("git %s falló: %s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r.stdout


def git_ok(repo, *args):
    return _correr(repo, args).returncode == 0


def existe_ref(repo, ref):
    return git_ok(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}")


def ref_principal(repo, pedido=None):
    """Lo que se documenta: lo pedido o, por defecto, la rama donde se está trabajando (HEAD).

    La documentación se dispara con el commit o el push de quien trabaja, así que documenta
    la actividad que esa persona acaba de hacer, esté en la rama que esté.
    """
    return pedido or "HEAD"


def nombre_ref(repo, ref):
    """Nombre legible de la rama (HEAD se traduce al nombre de la rama actual)."""
    if ref == "HEAD":
        return git(repo, "rev-parse", "--abbrev-ref", "HEAD", check=False).strip() or "HEAD"
    return ref


def sha(repo, ref):
    return git(repo, "rev-parse", ref).strip()


def _ruta_worktree(repo):
    comun = git(repo, "rev-parse", "--git-common-dir").strip()
    if not os.path.isabs(comun):
        comun = os.path.join(repo, comun)
    return os.path.normpath(os.path.join(comun, "docviva-wt"))
