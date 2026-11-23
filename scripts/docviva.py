#!/usr/bin/env python3
"""docviva: documentación viva de un proyecto, en HTML, con la autoría sacada de Git.

Solo librería estándar. Subcomandos:
  estado         ¿Hay documentación? ¿Quedó atrás respecto al código?
  preparar-rama  Crea la rama de documentación (solo documentos) en un worktree aparte; no toca tu rama.
  autoria        Quién hizo qué, sacado del historial de Git (sin correos).
  construir      Une el análisis (JSON) con la autoría y escribe data.json, meta.json e index.html.
  confirmar      Commit local de la documentación en su rama. Nunca hace push.
  abrir          Abre la documentación en tu navegador.
  indice         Lee el índice de la documentación en texto: el mapa completo del proyecto en una página.
                 Con --modulo <id> da la ficha de un módulo; con --buscar <palabras>, los resultados.
                 Solo lee de la rama de documentación; no cambia nada.

Se usa justo después del commit o push que la persona aprobó: la documentación de esa actividad
se actualiza en su propia rama, con el mismo permiso.

El código vive en docviva_lib/: gitutil (Git), autoria (quién hizo qué), rama (estado y rama aparte),
construccion (une análisis y autoría), calidad (avisos sobre el análisis) y pagina (HTML, con su
plantilla en docviva_lib/plantilla/).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docviva_lib.autoria import autoria, commits, modulo_de, numero_pr, posibles_alias  # noqa: E402,F401
from docviva_lib.calidad import avisos_calidad  # noqa: E402,F401
from docviva_lib.construccion import construir  # noqa: E402,F401
from docviva_lib.constantes import CARPETA, MAX_VERSIONES, RAMA, SIN_MODULO  # noqa: E402,F401
from docviva_lib.gitutil import _ruta_worktree, git_ok, ref_principal  # noqa: E402,F401
from docviva_lib.indice import archivo_id, buscar as buscar_en_indice, generar as generar_indice  # noqa: E402,F401
from docviva_lib.indice import leer as leer_indice  # noqa: E402,F401
from docviva_lib.pagina import render  # noqa: E402,F401
from docviva_lib.rama import abrir, confirmar, estado, preparar_rama  # noqa: E402,F401


def main(argv=None):
    ap = argparse.ArgumentParser(prog="docviva", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=".", help="Carpeta del proyecto (por defecto, la actual)")
    ap.add_argument("--ref", default=None, help="Rama que se documenta (por defecto, la rama donde se trabaja)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("estado")
    sub.add_parser("preparar-rama")
    a = sub.add_parser("autoria")
    a.add_argument("--modulos", default=None, help="JSON {id: ruta} para agrupar por módulo")
    c = sub.add_parser("construir")
    c.add_argument("entrada", help="JSON con el análisis")
    k = sub.add_parser("confirmar")
    k.add_argument("--mensaje", default=None)
    sub.add_parser("abrir")
    i = sub.add_parser("indice")
    i.add_argument("--modulo", default=None, help="id del módulo cuya ficha quieres leer")
    i.add_argument("--buscar", default=None, help="palabras a buscar en toda la documentación")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)
    if not git_ok(repo, "rev-parse", "--git-dir"):
        raise SystemExit("%s no es un repositorio Git." % repo)
    if args.cmd == "estado":
        out = estado(repo, args.ref)
    elif args.cmd == "preparar-rama":
        out = {"worktree": preparar_rama(repo, args.ref), "rama": RAMA}
    elif args.cmd == "autoria":
        mods = {}
        if args.modulos:
            with open(args.modulos, encoding="utf-8") as f:
                mods = json.load(f)
        out = autoria(repo, ref_principal(repo, args.ref), mods)
    elif args.cmd == "construir":
        out = construir(repo, args.entrada, args.ref)
    elif args.cmd == "abrir":
        out = abrir(repo)
    elif args.cmd == "indice":
        out = leer_indice(repo, args.modulo, args.buscar)
        if isinstance(out, str):  # el índice y las fichas se leen como texto, no como JSON
            print(out)
            return
    else:
        out = confirmar(repo, args.mensaje, args.ref)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=list))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
