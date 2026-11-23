import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import docviva  # noqa: E402


def _borrar(func, ruta, _):
    os.chmod(ruta, stat.S_IWRITE)
    func(ruta)


def git(repo, *args, env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       encoding="utf-8", env=e)
    if r.returncode != 0:
        raise AssertionError("git %s: %s" % (" ".join(args), r.stderr))
    return r.stdout


def commit(repo, autor, correo, archivos, msg, fecha="2026-01-10T10:00:00"):
    for ruta, texto in archivos.items():
        p = os.path.join(repo, *ruta.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(texto)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", msg, env={
        "GIT_AUTHOR_NAME": autor, "GIT_AUTHOR_EMAIL": correo, "GIT_AUTHOR_DATE": fecha,
        "GIT_COMMITTER_NAME": autor, "GIT_COMMITTER_EMAIL": correo, "GIT_COMMITTER_DATE": fecha})


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def leer_json(ruta):
    return json.loads(leer(ruta))


def escribir_json(ruta, obj):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


MODULOS = {"api": "src/api", "ui": "src/ui", "raiz": "src"}


class Base(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="docviva-")
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Docs Tester")
        git(self.repo, "config", "user.email", "docs@example.com")
        commit(self.repo, "Ana Perez", "ana@example.com", {"src/api/a.py": "x\n" * 50}, "API inicial")
        commit(self.repo, "Beto Ruiz", "beto@example.com", {"src/ui/u.py": "y\n" * 20}, "UI inicial")
        commit(self.repo, "Beto Ruiz", "beto@example.com", {"src/api/a.py": "z\n"}, "Ajuste en API")

    def tearDown(self):
        wt = docviva._ruta_worktree(self.repo)
        shutil.rmtree(wt, onerror=_borrar, ignore_errors=True)
        shutil.rmtree(self.repo, onerror=_borrar, ignore_errors=True)

    def entrada(self, datos):
        ruta = os.path.join(self.repo, "..", "entrada-%s.json" % os.path.basename(self.repo))
        escribir_json(ruta, datos)
        self.addCleanup(lambda: os.path.exists(ruta) and os.remove(ruta))
        return ruta

    def base(self):
        return {"proyecto": {"nombre": "Proyecto de prueba", "resumen": "Una API y una UI.", "stack": ["Python"]},
                "modulos": [
                    {"id": "api", "nombre": "API", "ruta": "src/api", "resumen": "Expone los datos.", "depende_de": []},
                    {"id": "ui", "nombre": "Interfaz", "ruta": "src/ui", "resumen": "Pantallas.", "depende_de": ["api"]}],
                "flujos": [{"nombre": "Consulta", "pasos": [
                    {"de": "Usuario", "a": "Interfaz", "texto": "abre la pantalla"},
                    {"de": "Interfaz", "a": "API", "texto": "GET /datos"},
                    {"de": "API", "a": "API", "texto": "valida"}]}],
                "actividad": {"resumen": "Primera documentación.", "modulos_tocados": ["api", "ui"]},
                "sin_verificar": ["No se levantó el servidor."]}


class TestAutoria(Base):
    def test_principal_por_lineas_y_prefijo_mas_largo(self):
        a = docviva.autoria(self.repo, "main", MODULOS)
        self.assertEqual(a["modulos"]["api"]["principal"], "Ana Perez")
        self.assertIn("Beto Ruiz", a["modulos"]["api"]["colaboradores"])
        self.assertEqual(a["modulos"]["ui"]["principal"], "Beto Ruiz")
        self.assertEqual(a["modulos"]["api"]["ultimo"]["autor"], "Beto Ruiz")
        self.assertEqual(docviva.modulo_de("src/api/x.py", MODULOS), "api")
        self.assertEqual(docviva.modulo_de("src/otro.py", MODULOS), "raiz")
        self.assertEqual(docviva.modulo_de("README.md", {"api": "src/api"}), docviva.SIN_MODULO)

    def test_un_merge_no_cuenta_como_autoria(self):
        git(self.repo, "checkout", "-q", "-b", "feature")
        commit(self.repo, "Carla Gil", "carla@example.com", {"src/ui/c.py": "c\n"}, "Pantalla nueva")
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "merge", "--no-ff", "-m", "Merged PR 1", "feature",
            env={"GIT_AUTHOR_NAME": "Dani Mora", "GIT_AUTHOR_EMAIL": "dani@example.com",
                 "GIT_COMMITTER_NAME": "Dani Mora", "GIT_COMMITTER_EMAIL": "dani@example.com"})
        a = docviva.autoria(self.repo, "main", MODULOS)
        self.assertIn("Carla Gil", a["personas"])
        self.assertNotIn("Dani Mora", a["personas"])

    def test_alias_probables(self):
        commit(self.repo, "ana", "ana@example.com", {"src/api/b.py": "q\n"}, "Otro")
        a = docviva.autoria(self.repo, "main", MODULOS)
        self.assertTrue(any(set(par) == {"Ana Perez", "ana"} for par in a["posibles_alias"]))
        self.assertFalse(any(set(par) == {"Ana Perez", "Beto Ruiz"} for par in a["posibles_alias"]))

    def test_mailmap_une_los_alias(self):
        commit(self.repo, "ana", "ana@example.com", {"src/api/b.py": "q\n"}, "Otro")
        commit(self.repo, "Ana Perez", "ana@example.com", {".mailmap": "Ana Perez <ana@example.com>\n"}, "mailmap")
        a = docviva.autoria(self.repo, "main", MODULOS)
        self.assertNotIn("ana", a["personas"])


class TestFlujo(Base):
    def test_estado_sin_documentacion(self):
        s = docviva.estado(self.repo)
        self.assertFalse(s["documentada"])
        self.assertFalse(s["desactualizada"])
        self.assertEqual(s["tamano"]["commits"], 3)
        self.assertEqual((s["tiene_remoto"], s["remoto_verificado"], s["primera_vez"]), (False, True, True))
        self.assertEqual(s["accion"], "analisis_completo")
        self.assertTrue(s["respuesta"].startswith("No está documentado"))  # la respuesta a "¿está documentado?"
        self.assertIn(docviva.RAMA, s["respuesta"])

    def test_ciclo_completo_con_varias_personas(self):
        wt = docviva.preparar_rama(self.repo)
        self.assertTrue(os.path.isdir(wt))
        self.assertEqual(git(self.repo, "branch", "--show-current").strip(), "main")
        self.assertEqual(git(self.repo, "status", "--porcelain").strip(), "")

        r = docviva.construir(self.repo, self.entrada(self.base()))
        self.assertTrue(os.path.isfile(r["html"]))
        pagina = leer(r["html"])
        for texto in ("Proyecto de prueba", "Ana Perez", "Beto Ruiz", "Principal autor del código", "<svg"):
            self.assertIn(texto, pagina)
        self.assertNotIn("@example.com", pagina)
        sin_svg = pagina.replace("http://www.w3.org/2000/svg", "")
        for externo in ("http://", "https://", "<script src", "<link", "@import"):
            self.assertNotIn(externo, sin_svg)
        self.assertEqual(pagina.count("<script"), 2)  # el índice de búsqueda y el buscador, ambos incrustados

        c = docviva.confirmar(self.repo)
        self.assertIsNotNone(c["commit"])
        self.assertNotIn("push", git(self.repo, "log", "-1", "--format=%B", docviva.RAMA).lower().replace("no se hizo push", ""))
        s = docviva.estado(self.repo)
        self.assertTrue(s["documentada"])
        self.assertFalse(s["desactualizada"])
        self.assertEqual(s["docs_actualizada_por"], "Docs Tester")
        self.assertEqual((s["accion"], s["fuente"], s["primera_vez"]), ("leer_documentacion", "local", False))
        self.assertTrue(s["respuesta"].startswith("Sí está documentado"))
        for texto in ("en este equipo", "al día", "Docs Tester"):
            self.assertIn(texto, s["respuesta"])
        self.assertRegex(s["docs_fecha"], r"^\d{4}-\d{2}-\d{2}$")

        commit(self.repo, "Beto Ruiz", "beto@example.com", {"src/api/a.py": "nuevo\n"}, "Valida entradas", "2026-02-01T10:00:00")
        s = docviva.estado(self.repo)
        self.assertTrue(s["desactualizada"])
        self.assertEqual(s["commits_nuevos"], 1)
        self.assertEqual(s["modulos_tocados"], ["api"])
        self.assertEqual(s["autores_nuevos"], ["Beto Ruiz"])
        self.assertEqual(s["accion"], "actualizar")
        self.assertTrue(s["respuesta"].startswith("Sí está documentado"))
        self.assertIn("quedó atrás", s["respuesta"])
        self.assertIn("1 commit ", s["respuesta"])

        docviva.preparar_rama(self.repo)
        parcial = {"actividad": {"resumen": "Se validan las entradas.", "modulos_tocados": ["api"]}}
        docviva.construir(self.repo, self.entrada(parcial))
        data = leer_json(os.path.join(wt, "docs", "documentacion", "data.json"))
        self.assertEqual(len(data["historial"]), 2)
        self.assertEqual(data["historial"][0]["titulo"], "Actualización")
        self.assertEqual(data["historial"][0]["autores"], [{"nombre": "Beto Ruiz", "commits": 1}])
        self.assertEqual(len(data["modulos"]), 2)
        self.assertEqual(len(data["flujos"]), 1)
        docviva.confirmar(self.repo)
        self.assertFalse(docviva.estado(self.repo)["desactualizada"])
        self.assertEqual(git(self.repo, "status", "--porcelain").strip(), "")

    def test_sin_cambios_no_hace_commit_vacio(self):
        docviva.preparar_rama(self.repo)
        docviva.construir(self.repo, self.entrada(self.base()))
        docviva.confirmar(self.repo)
        docviva.construir(self.repo, self.entrada({"actividad": {"resumen": "nada"}}))
        self.assertIsNone(docviva.confirmar(self.repo)["commit"])

    def test_el_html_escapa_el_contenido(self):
        docviva.preparar_rama(self.repo)
        d = self.base()
        d["modulos"][0]["resumen"] = "<script>alert(1)</script>"
        r = docviva.construir(self.repo, self.entrada(d))
        pagina = leer(r["html"])
        self.assertNotIn("<script>alert(1)</script>", pagina)
        self.assertIn("&lt;script&gt;", pagina)

    def test_construir_exige_la_rama(self):
        with self.assertRaises(SystemExit):
            docviva.construir(self.repo, self.entrada(self.base()))

    def test_modulo_incompleto_falla(self):
        docviva.preparar_rama(self.repo)
        d = self.base()
        del d["modulos"][0]["resumen"]
        with self.assertRaises(SystemExit):
            docviva.construir(self.repo, self.entrada(d))

    def test_historia_reescrita(self):
        wt = docviva.preparar_rama(self.repo)
        docviva.construir(self.repo, self.entrada(self.base()))
        meta = os.path.join(wt, "docs", "documentacion", "meta.json")
        datos = leer_json(meta)
        datos["ultimo_commit"] = "0" * 40
        escribir_json(meta, datos)
        docviva.confirmar(self.repo)
        s = docviva.estado(self.repo)
        self.assertTrue(s["historia_reescrita"])
        self.assertTrue(s["desactualizada"])
        self.assertEqual(s["accion"], "rehacer_base_con_permiso")  # nunca relee todo sin preguntar
        self.assertTrue(s["respuesta"].startswith("Sí está documentado, pero la historia"))


class TestRamaYRamas(Base):
    def test_la_rama_de_docs_solo_tiene_documentacion_y_no_comparte_historia_con_el_codigo(self):
        docviva.preparar_rama(self.repo)
        docviva.construir(self.repo, self.entrada(self.base()))
        docviva.confirmar(self.repo)
        archivos = git(self.repo, "ls-tree", "-r", "--name-only", docviva.RAMA).split()
        self.assertTrue(archivos)
        self.assertTrue(all(a.startswith("docs/documentacion/") for a in archivos), archivos)
        r = subprocess.run(["git", "-C", self.repo, "merge-base", "main", docviva.RAMA], capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(git(self.repo, "branch", "--show-current").strip(), "main")

    def test_documentar_la_rama_donde_se_trabaja_y_volver_a_main(self):
        docviva.preparar_rama(self.repo)
        docviva.construir(self.repo, self.entrada(self.base()))
        docviva.confirmar(self.repo)
        git(self.repo, "checkout", "-q", "-b", "feature")
        commit(self.repo, "Carla Gil", "carla@example.com", {"src/ui/f.py": "f\n" * 4}, "Pantalla en feature",
               "2026-02-01T10:00:00")
        s = docviva.estado(self.repo)
        self.assertEqual(s["ref"], "feature")
        self.assertEqual((s["desactualizada"], s["commits_nuevos"], s["autores_nuevos"]), (True, 1, ["Carla Gil"]))
        docviva.construir(self.repo, self.entrada({"actividad": {"resumen": "Pantalla nueva.", "modulos_tocados": ["ui"]}}))
        docviva.confirmar(self.repo)
        self.assertFalse(docviva.estado(self.repo)["desactualizada"])
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, "Ana Perez", "ana@example.com", {"src/api/n.py": "n\n"}, "Cambio en main", "2026-02-02T10:00:00")
        s = docviva.estado(self.repo)
        self.assertFalse(s["historia_reescrita"])
        self.assertEqual((s["ref"], s["commits_nuevos"]), ("main", 1))

    def test_abrir_devuelve_el_html(self):
        with self.assertRaises(SystemExit):
            docviva.abrir(self.repo, navegador=False)
        docviva.preparar_rama(self.repo)
        docviva.construir(self.repo, self.entrada(self.base()))
        r = docviva.abrir(self.repo, navegador=False)
        self.assertTrue(os.path.isfile(r["html"]))
        self.assertFalse(r["abierto"])


class TestVersiones(Base):
    def documentar_base(self):
        docviva.preparar_rama(self.repo)
        docviva.construir(self.repo, self.entrada(self.base()))
        docviva.confirmar(self.repo)

    def cambio(self, resumen, **extra):
        m = {"id": "api", "nombre": "API", "ruta": "src/api", "resumen": resumen}
        m.update(extra)
        return {"modulos": [m], "actividad": {"resumen": "x", "modulos_tocados": ["api"]}}

    def api(self):
        wt = docviva._ruta_worktree(self.repo)
        data = leer_json(os.path.join(wt, "docs", "documentacion", "data.json"))
        return next(m for m in data["modulos"] if m["id"] == "api")

    def test_un_cambio_archiva_la_version_anterior_con_sus_autores(self):
        self.documentar_base()
        commit(self.repo, "Carla Gil", "carla@example.com", {"src/api/n.py": "n\n" * 3}, "Nueva ruta",
               "2026-02-01T10:00:00")
        docviva.preparar_rama(self.repo)
        r = docviva.construir(self.repo, self.entrada(self.cambio("Expone los datos y la ruta nueva.")))
        api = self.api()
        self.assertEqual(api["resumen"], "Expone los datos y la ruta nueva.")
        self.assertEqual(len(api["versiones"]), 1)
        v = api["versiones"][0]
        self.assertEqual(v["resumen"], "Expone los datos.")
        self.assertEqual({a["nombre"] for a in v["autores"]}, {"Ana Perez", "Beto Ruiz"})
        self.assertEqual([a["nombre"] for a in api["doc"]["autores"]], ["Carla Gil"])
        pagina = leer(r["html"])
        self.assertIn("<details", pagina)
        self.assertIn("Versiones anteriores (1)", pagina)
        self.assertIn("Expone los datos.", pagina)
        self.assertIn("Expone los datos y la ruta nueva.", pagina)

    def test_si_no_cambio_de_verdad_no_se_crea_otra_version(self):
        self.documentar_base()
        antes = self.api()
        docviva.construir(self.repo, self.entrada(self.cambio("Expone los datos.")))
        despues = self.api()
        self.assertEqual(despues["versiones"], [])
        self.assertEqual(despues["doc"], antes["doc"])

    def test_los_modulos_que_no_cambian_conservan_su_historia(self):
        self.documentar_base()
        docviva.construir(self.repo, self.entrada(self.cambio("Primera mejora.")))
        docviva.construir(self.repo, self.entrada(self.cambio("Segunda mejora.")))
        ui = {"modulos": [{"id": "ui", "nombre": "Interfaz", "ruta": "src/ui", "resumen": "Pantallas nuevas.",
                           "depende_de": ["api"]}], "actividad": {"resumen": "y"}}
        docviva.construir(self.repo, self.entrada(ui))
        api = self.api()
        self.assertEqual([v["resumen"] for v in api["versiones"]], ["Primera mejora.", "Expone los datos."])
        self.assertEqual(api["resumen"], "Segunda mejora.")

    def test_tope_de_versiones(self):
        self.documentar_base()
        for i in range(docviva.MAX_VERSIONES + 3):
            docviva.construir(self.repo, self.entrada(self.cambio("Texto %d." % i)))
        api = self.api()
        self.assertEqual(len(api["versiones"]), docviva.MAX_VERSIONES)
        self.assertEqual(api["versiones"][0]["resumen"], "Texto %d." % (docviva.MAX_VERSIONES + 1))

    def test_la_correccion_de_un_pr_llega_a_las_versiones_viejas(self):
        commit(self.repo, "paula", "paula@example.com", {"src/api/pr.py": "p\n" * 10},
               "Merged PR 40: Ruta de pagos", "2026-02-02T10:00:00")
        self.documentar_base()
        docviva.construir(self.repo, self.entrada(self.cambio("Cambio de texto.")))
        nombres = {a["nombre"] for a in self.api()["versiones"][0]["autores"]}
        self.assertIn("paula", nombres)
        d = self.cambio("Cambio de texto.")
        d["autores_pr"] = {"40": "Lucia Soto"}
        docviva.construir(self.repo, self.entrada(d))
        nombres = {a["nombre"] for a in self.api()["versiones"][0]["autores"]}
        self.assertIn("Lucia Soto", nombres)
        self.assertNotIn("paula", nombres)


class TestPrIntegrados(Base):
    def setUp(self):
        super().setUp()
        commit(self.repo, "paula", "paula@example.com", {"src/ui/pr.py": "p\n" * 30},
               "Merged PR 12: TASK #9: pantalla nueva", "2026-03-01T10:00:00")
        commit(self.repo, "Carla Gil", "carla@example.com", {"src/api/c.py": "c\n" * 5},
               "Agrega validacion (#7)", "2026-03-02T10:00:00")

    def test_el_pr_de_azure_queda_sin_confirmar_y_el_squash_de_github_no(self):
        a = docviva.autoria(self.repo, "main", MODULOS)
        self.assertEqual(a["prs_sin_confirmar"], [{"pr": 12, "integrado_por": "paula"}])
        self.assertEqual(docviva.numero_pr("Agrega validacion (#7)"), (7, "squash"))
        self.assertEqual(docviva.numero_pr("Arreglo normal"), (None, None))

    def test_corregir_la_autoria_de_un_pr(self):
        a = docviva.autoria(self.repo, "main", MODULOS, autores_pr={"12": "Leandro Perez"})
        self.assertEqual(a["prs_sin_confirmar"], [])
        self.assertIn("Leandro Perez", a["personas"])
        self.assertNotIn("paula", a["personas"])
        self.assertEqual(a["modulos"]["ui"]["principal"], "Leandro Perez")
        self.assertFalse(any("Leandro Perez" in par for par in a["posibles_alias"]))

    def test_el_html_avisa_y_la_correccion_se_guarda_para_el_equipo(self):
        wt = docviva.preparar_rama(self.repo)
        r = docviva.construir(self.repo, self.entrada(self.base()))
        self.assertEqual(r["prs_sin_confirmar"], [12])
        self.assertIn("Hay cambios que entraron como un solo commit", leer(r["html"]))
        d = self.base()
        d["autores_pr"] = {"12": "Leandro Perez"}
        r = docviva.construir(self.repo, self.entrada(d))
        self.assertEqual(r["prs_sin_confirmar"], [])
        pagina = leer(r["html"])
        self.assertNotIn("Hay cambios que entraron como un solo commit", pagina)
        self.assertIn("Leandro Perez (1)", pagina)       # el historial también se corrige
        self.assertNotIn("paula (1)", pagina)
        self.assertEqual(leer_json(os.path.join(wt, "docs", "documentacion", "autores.json")), {"12": "Leandro Perez"})
        r = docviva.construir(self.repo, self.entrada({"actividad": {"resumen": "x"}}))
        self.assertEqual(r["prs_sin_confirmar"], [])


MODULO_RICO = {
    "id": "api", "nombre": "API", "ruta": "src/api",
    "resumen": ("Es la puerta de entrada de los datos del sistema. Recibe las peticiones de las pantallas, "
                "comprueba que quien pide tenga permiso y devuelve la información ya preparada, para que "
                "ninguna pantalla tenga que hablar directo con la base de datos."),
    "por_que": "Separa la lógica de las pantallas para poder cambiar una sin romper la otra.",
    "como_funciona": ["Recibe la petición", "Valida el permiso", "Consulta los datos", "Devuelve la respuesta"],
    "datos": ["Productos: nombre, precio y existencias"],
    "reglas": ["Un cliente solo ve sus propios pedidos"],
    "archivos_clave": [{"ruta": "src/api/a.py", "para_que": "define las rutas y valida los permisos"}],
    "cuidados": ["Cambiar el formato de la respuesta rompe las pantallas"],
    "ejemplo": "GET /datos?categoria=ropa",
    "cambio": {"antes": "Devolvía todos los datos", "ahora": "Filtra por categoría",
               "por_que": "Las pantallas tardaban en cargar", "origen": "commit"},
}


class TestFichaYBuscador(Base):
    def indice(self, pagina):
        m = re.search(r'<script type="application/json" id="indice">(.*?)</script>', pagina, re.S)
        return json.loads(m.group(1))

    def construir(self, modulo, extra=None):
        docviva.preparar_rama(self.repo)
        d = {"proyecto": {"nombre": "Proyecto de prueba"}, "modulos": [modulo],
             "actividad": {"resumen": "x", "modulos_tocados": [modulo["id"]]}}
        d.update(extra or {})
        return docviva.construir(self.repo, self.entrada(d))

    def test_la_ficha_muestra_todas_las_secciones_y_no_recorta_el_texto(self):
        r = self.construir(MODULO_RICO)
        pagina = leer(r["html"])
        for texto in ("Por qué existe", "Cómo funciona", "Datos que maneja", "Reglas que cumple",
                      "Por dónde empezar a leer el código", "Cuidado con", "Ejemplo", "Qué cambió y por qué",
                      "según el mensaje del commit", "<ol>", "<pre>", "GET /datos?categoria=ropa",
                      "define las rutas y valida los permisos", "Un cliente solo ve sus propios pedidos"):
            self.assertIn(texto, pagina)
        self.assertIn(MODULO_RICO["resumen"], pagina)  # más de 40 palabras, completo
        self.assertEqual(r["avisos"], [])

    def test_avisos_de_calidad_sobre_el_analisis(self):
        pobre = {"id": "api", "nombre": "API", "ruta": "src/api", "resumen": "API", "depende_de": ["fantasma"]}
        r = self.construir(pobre)
        texto = " | ".join(a["aviso"] for a in r["avisos"])
        for esperado in ("palabras", "solo repite el nombre", "por_que", "como_funciona", "archivos_clave", "fantasma"):
            self.assertIn(esperado, texto)
        # un módulo ya documentado que cambia debe explicar qué cambió
        distinto = dict(MODULO_RICO, resumen=MODULO_RICO["resumen"] + " Ahora también filtra.")
        distinto.pop("cambio")
        r = docviva.construir(self.repo, self.entrada({"modulos": [distinto], "actividad": {"resumen": "y"}}))
        self.assertTrue(any("antes, ahora y por_que" in a["aviso"] for a in r["avisos"]))
        distinto["cambio"] = {"antes": "a", "ahora": "b", "por_que": "c"}
        r = docviva.construir(self.repo, self.entrada({"modulos": [distinto], "actividad": {"resumen": "z"}}))
        self.assertTrue(any("cambio.origen" in a["aviso"] for a in r["avisos"]))

    def test_el_indice_incluye_autores_y_versiones_viejas_y_no_rompe_la_pagina(self):
        self.construir(MODULO_RICO)
        nuevo = dict(MODULO_RICO, resumen="Ahora la API habla con la caché antes de ir a la base de datos. </script><b>x</b>")
        r = docviva.construir(self.repo, self.entrada({"modulos": [nuevo], "actividad": {"resumen": "w"}}))
        pagina = leer(r["html"])
        self.assertEqual(pagina.count("<script"), 2)
        reg = next(x for x in self.indice(pagina) if x["id"] == "m-api")
        self.assertIn("caché", reg["texto"])
        self.assertIn("</script><b>x</b>", reg["texto"])        # llega intacto al buscador
        self.assertIn("puerta de entrada", reg["antiguo"])      # el texto de la versión anterior
        self.assertIn("Ana Perez", reg["texto"])                # quién lo hizo también se busca
        tipos = {x["tipo"] for x in self.indice(pagina)}
        self.assertTrue({"Módulo", "Persona", "Actividad"} <= tipos)

    @unittest.skipUnless(shutil.which("node"), "Node no está instalado")
    def test_la_logica_del_buscador(self):
        carpeta = tempfile.mkdtemp(prefix="docviva-js-")
        self.addCleanup(lambda: shutil.rmtree(carpeta, onerror=_borrar, ignore_errors=True))
        indice = [
            {"id": "m-facturas", "tipo": "Módulo", "titulo": "Facturas",
             "texto": "Genera y envía la factura al cliente. Lucía Fernández", "antiguo": ""},
            {"id": "m-pagos", "tipo": "Módulo", "titulo": "Pagos",
             "texto": "Cobra con tarjeta. Cada factura se concilia", "antiguo": "Antes usaba cheques"},
            {"id": "p-0", "tipo": "Persona", "titulo": "Lucía Fernández", "texto": "Facturas"},
        ]
        consultas = ["facturas", "lucia", "cheques", "factura cliente", "", "zzzz", "FACTURA"]
        ruta_js = os.path.join(os.path.dirname(__file__), "..", "scripts", "docviva_lib", "plantilla", "buscador.js")
        escribir_json(os.path.join(carpeta, "i.json"), indice)
        escribir_json(os.path.join(carpeta, "q.json"), consultas)
        with open(os.path.join(carpeta, "t.js"), "w", encoding="utf-8") as f:
            f.write("const fs=require('fs'),vm=require('vm');const ctx={};vm.createContext(ctx);"
                    "vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);"
                    "const i=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const out={};"
                    "for(const q of JSON.parse(fs.readFileSync(process.argv[4],'utf8')))"
                    "out[q]=ctx.buscar(i,q).map(r=>[r.registro.id,r.soloAntiguo]);"
                    "console.log(JSON.stringify(out));")
        r = subprocess.run(["node", os.path.join(carpeta, "t.js"), ruta_js, os.path.join(carpeta, "i.json"),
                            os.path.join(carpeta, "q.json")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(r.stdout)
        self.assertEqual(res["facturas"][0][0], "m-facturas")                 # coincidencia en el título primero
        self.assertEqual({x[0] for x in res["facturas"]}, {"m-facturas", "m-pagos", "p-0"})
        self.assertEqual({x[0] for x in res["lucia"]}, {"m-facturas", "p-0"})  # sin tildes
        self.assertEqual(res["cheques"], [["m-pagos", True]])                  # solo en una versión anterior
        self.assertEqual([x[0] for x in res["factura cliente"]], ["m-facturas"])  # todos los términos
        self.assertEqual(res[""], [])
        self.assertEqual(res["zzzz"], [])
        self.assertEqual(res["FACTURA"][0][0], "m-facturas")                   # sin distinguir mayúsculas


class TestIndice(Base):
    def carpeta(self):
        return os.path.join(docviva._ruta_worktree(self.repo), "docs", "documentacion")

    def documentar(self, modulos=None, extra=None):
        docviva.preparar_rama(self.repo)
        d = {"proyecto": {"nombre": "Proyecto de prueba", "resumen": "Una API y una UI."},
             "modulos": modulos or [MODULO_RICO,
                                    {"id": "ui", "nombre": "Interfaz", "ruta": "src/ui", "resumen": "Pantallas.",
                                     "depende_de": ["api"]}],
             "flujos": [{"nombre": "Consulta", "pasos": [{"de": "Usuario", "a": "Interfaz", "texto": "abre la pantalla"}]}],
             "actividad": {"resumen": "Base.", "modulos_tocados": ["api", "ui"]},
             "sin_verificar": ["No se levantó el servidor."]}
        d.update(extra or {})
        return docviva.construir(self.repo, self.entrada(d))

    def test_construir_genera_el_indice_y_una_ficha_por_modulo(self):
        self.documentar()
        c = self.carpeta()
        for archivo in ("INDICE.md", "indice.json", "modulos/api.md", "modulos/ui.md"):
            self.assertTrue(os.path.isfile(os.path.join(c, *archivo.split("/"))), archivo)
        indice = leer(os.path.join(c, "INDICE.md"))
        for texto in ("# Índice de la documentación: Proyecto de prueba", "| API (`api`) |", "`src/api/` -> API (`api`)",
                      "## Dependencias", "- ui -> api", "1. Usuario -> Interfaz: abre la pantalla",
                      "`src/api/a.py`: define las rutas y valida los permisos", "Ana Perez",
                      "No se levantó el servidor.", "`modulos/api.md`"):
            self.assertIn(texto, indice)
        self.assertNotIn("@example.com", indice)
        js = leer_json(os.path.join(c, "indice.json"))
        self.assertEqual([m["id"] for m in js["modulos"]], ["api", "ui"])
        self.assertEqual(js["modulos"][0]["ficha"], "modulos/api.md")
        self.assertEqual(js["modulos"][0]["principal"], "Ana Perez")
        self.assertNotIn("@", json.dumps(js))

    def test_el_indice_es_un_mapa_y_la_ficha_tiene_el_detalle(self):
        self.documentar()
        c = self.carpeta()
        indice, ficha = leer(os.path.join(c, "INDICE.md")), leer(os.path.join(c, "modulos", "api.md"))
        self.assertNotIn("Valida el permiso", indice)  # un paso de "cómo funciona" no se repite en el índice
        for texto in ("## Por qué existe", "## Cómo funciona", "1. Recibe la petición", "2. Valida el permiso",
                      "## Reglas que cumple", "## Cuidado con", "```\nGET /datos?categoria=ropa\n```",
                      "## Qué cambió y por qué", "según el mensaje del commit"):
            self.assertIn(texto, ficha)
        self.assertLess(len(indice.split()), len(ficha.split()) + 400)

    def test_la_ficha_incluye_las_versiones_anteriores(self):
        self.documentar()
        nuevo = dict(MODULO_RICO, resumen=MODULO_RICO["resumen"] + " Ahora usa caché.")
        docviva.construir(self.repo, self.entrada({"modulos": [nuevo], "actividad": {"resumen": "y"}}))
        ficha = leer(os.path.join(self.carpeta(), "modulos", "api.md"))
        self.assertIn("## Versiones anteriores (1)", ficha)
        self.assertIn("### Versión del", ficha)
        self.assertIn("Ahora usa caché.", ficha)

    def test_un_id_peligroso_no_escribe_fuera_de_la_carpeta(self):
        self.assertEqual(docviva.archivo_id("../evil"), "evil")
        self.assertEqual(docviva.archivo_id("a/b c"), "a-b-c")
        malo = dict(MODULO_RICO, id="../../evil")
        self.documentar(modulos=[malo])
        c = self.carpeta()
        self.assertTrue(os.path.isfile(os.path.join(c, "modulos", "evil.md")))
        for fuera in (os.path.join(c, "..", "evil.md"), os.path.join(c, "..", "..", "evil.md"),
                      os.path.join(c, "modulos", "..", "evil.md")):
            self.assertFalse(os.path.exists(fuera), fuera)

    def test_las_fichas_viejas_se_borran_y_la_tabla_escapa_las_barras(self):
        self.documentar()
        c = self.carpeta()
        viejo = os.path.join(c, "modulos", "viejo.md")
        with open(viejo, "w", encoding="utf-8") as f:
            f.write("x")
        raro = dict(MODULO_RICO, resumen="Primera parte | segunda parte.\nTercera línea con suficientes palabras para "
                    "no recibir avisos de calidad en esta prueba concreta del índice.")
        docviva.construir(self.repo, self.entrada({"modulos": [raro], "actividad": {"resumen": "z"}}))
        self.assertFalse(os.path.exists(viejo))
        fila = next(l for l in leer(os.path.join(c, "INDICE.md")).splitlines() if l.startswith("| API"))
        self.assertIn("Primera parte / segunda parte.", fila)
        self.assertEqual(fila.count(" | "), 7)  # ocho columnas, ninguna rota por la barra

    def test_el_comando_indice_lee_de_la_rama_sin_tocar_nada(self):
        with self.assertRaises(SystemExit):
            docviva.leer_indice(self.repo)  # todavía no hay documentación
        self.documentar()
        docviva.confirmar(self.repo)
        antes = git(self.repo, "status", "--porcelain")
        indice = docviva.leer_indice(self.repo)
        self.assertEqual(indice, leer(os.path.join(self.carpeta(), "INDICE.md")))
        self.assertIn("# API (`api`)", docviva.leer_indice(self.repo, modulo="api"))
        with self.assertRaises(SystemExit):
            docviva.leer_indice(self.repo, modulo="no-existe")
        res = docviva.leer_indice(self.repo, consulta="permiso")
        self.assertEqual(res[0]["id"], "m-api")
        self.assertEqual(res[0]["ficha"], "modulos/api.md")
        self.assertEqual(git(self.repo, "status", "--porcelain"), antes)

    def test_la_busqueda_de_texto_se_comporta_igual_que_la_de_la_pagina(self):
        indice = [
            {"id": "m-facturas", "tipo": "Módulo", "titulo": "Facturas",
             "texto": "Genera y envía la factura al cliente. Lucía Fernández", "antiguo": ""},
            {"id": "m-pagos", "tipo": "Módulo", "titulo": "Pagos",
             "texto": "Cobra con tarjeta. Cada factura se concilia", "antiguo": "Antes usaba cheques"},
            {"id": "p-0", "tipo": "Persona", "titulo": "Lucía Fernández", "texto": "Facturas"},
        ]
        b = docviva.buscar_en_indice
        res = b(indice, "facturas")
        self.assertEqual(res[0]["id"], "m-facturas")
        self.assertEqual({x["id"] for x in res}, {"m-facturas", "m-pagos", "p-0"})
        self.assertEqual({x["id"] for x in b(indice, "lucia")}, {"m-facturas", "p-0"})
        r = b(indice, "cheques")
        self.assertEqual([(x["id"], x["solo_en_version_anterior"]) for x in r], [("m-pagos", True)])
        self.assertEqual([x["id"] for x in b(indice, "factura cliente")], ["m-facturas"])
        self.assertEqual(b(indice, ""), [])
        self.assertEqual(b(indice, "zzzz"), [])
        self.assertEqual(b(indice, "FACTURA")[0]["id"], "m-facturas")

    def test_la_pagina_apunta_al_indice(self):
        r = self.documentar()
        self.assertIn("INDICE.md", leer(r["html"]))


class TestLecturaCompletaSoloLaPrimeraVez(unittest.TestCase):
    """El proyecto entero se lee una sola vez: si algún remoto ya tiene la documentación, se parte de ella."""

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="docviva-primera-")
        self.addCleanup(self.limpiar)
        self.origen = os.path.join(self.base, "origen.git")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", self.origen], check=True)
        self.a, self.b = os.path.join(self.base, "a"), os.path.join(self.base, "b")
        subprocess.run(["git", "clone", "-q", self.origen, self.a], check=True, capture_output=True)
        git(self.a, "config", "user.name", "Persona A")
        git(self.a, "config", "user.email", "a@example.com")
        commit(self.a, "Persona A", "a@example.com", {"src/api/a.py": "x\n" * 10}, "inicio")
        git(self.a, "push", "-q", "origin", "main")
        # B clona ANTES de que exista la documentación: no tiene ninguna referencia a ella
        subprocess.run(["git", "clone", "-q", self.origen, self.b], check=True, capture_output=True)
        git(self.b, "config", "user.name", "Persona B")
        git(self.b, "config", "user.email", "b@example.com")

    def limpiar(self):
        for r in (self.a, self.b):
            if os.path.isdir(r):
                shutil.rmtree(docviva._ruta_worktree(r), onerror=_borrar, ignore_errors=True)
        shutil.rmtree(self.base, onerror=_borrar, ignore_errors=True)

    def documentar_desde_a(self):
        docviva.preparar_rama(self.a)
        ruta = os.path.join(self.base, "e.json")
        escribir_json(ruta, {"proyecto": {"nombre": "Compartido"}, "modulos": [
            {"id": "api", "nombre": "API", "ruta": "src/api", "resumen": "Datos."}], "actividad": {"resumen": "Base."}})
        docviva.construir(self.a, ruta)
        docviva.confirmar(self.a)
        git(self.a, "push", "-q", "origin", docviva.RAMA)

    def test_primera_vez_de_verdad_pide_el_analisis_completo(self):
        s = docviva.estado(self.b)
        self.assertEqual((s["documentada"], s["primera_vez"], s["remoto_verificado"]), (False, True, True))
        self.assertEqual(s["accion"], "analisis_completo")
        # preguntar no crea nada: la base solo se crea cuando el usuario lo aprueba
        self.assertEqual(git(self.b, "branch", "--list", docviva.RAMA).strip(), "")
        self.assertFalse(os.path.isdir(docviva._ruta_worktree(self.b)))

    def test_si_otra_persona_ya_documento_no_se_vuelve_a_leer_todo(self):
        self.documentar_desde_a()
        self.assertEqual(git(self.b, "branch", "-r", "--list", "origin/" + docviva.RAMA).strip(), "")  # B no la tiene
        s = docviva.estado(self.b)
        self.assertEqual((s["documentada"], s["primera_vez"], s["fuente"]), (True, False, "remota"))
        self.assertEqual(s["accion"], "leer_documentacion")
        self.assertIn("No releas el código", s["mensaje"])
        self.assertTrue(s["respuesta"].startswith("Sí está documentado (en el remoto"))
        self.assertIn("origin/" + docviva.RAMA, git(self.b, "branch", "-r"))  # solo se trajo esa rama
        self.assertIn("# Índice de la documentación: Compartido", docviva.leer_indice(self.b))
        # incorporarse es solo lectura: no crea ramas propias, ni worktrees, ni toca el trabajo
        self.assertEqual(git(self.b, "branch", "--list", docviva.RAMA).strip(), "")
        self.assertFalse(os.path.isdir(docviva._ruta_worktree(self.b)))
        self.assertEqual(git(self.b, "status", "--porcelain").strip(), "")

    def test_el_indice_se_lee_aunque_la_documentacion_solo_este_en_el_remoto(self):
        self.documentar_desde_a()
        indice = docviva.leer_indice(self.b)  # B nunca la había traído
        self.assertIn("API", indice)
        self.assertEqual(git(self.b, "branch", "--show-current").strip(), "main")
        self.assertEqual(git(self.b, "status", "--porcelain").strip(), "")

    def test_con_codigo_nuevo_se_actualiza_sin_releer_el_resto(self):
        self.documentar_desde_a()
        commit(self.a, "Persona A", "a@example.com", {"src/api/n.py": "n\n"}, "ruta nueva", "2026-02-01T10:00:00")
        git(self.a, "push", "-q", "origin", "main")
        git(self.b, "pull", "-q", "origin", "main")
        s = docviva.estado(self.b)
        self.assertEqual((s["accion"], s["modulos_tocados"], s["commits_nuevos"]), ("actualizar", ["api"], 1))

    def test_si_no_se_puede_preguntar_al_remoto_no_se_analiza_todo_a_ciegas(self):
        git(self.b, "remote", "set-url", "origin", os.path.join(self.base, "no-existe.git"))
        s = docviva.estado(self.b)
        self.assertEqual((s["tiene_remoto"], s["remoto_verificado"], s["primera_vez"]), (True, False, False))
        self.assertEqual(s["accion"], "confirmar_con_el_usuario")
        self.assertIn("pregunta al usuario", s["mensaje"])
        self.assertTrue(s["respuesta"].startswith("No pude comprobar"))


class TestRemoto(unittest.TestCase):
    def test_otra_persona_ya_creo_la_rama_de_docs(self):
        base = tempfile.mkdtemp(prefix="docviva-remoto-")
        try:
            origen = os.path.join(base, "origen.git")
            subprocess.run(["git", "init", "-q", "--bare", "-b", "main", origen], check=True)
            a, b = os.path.join(base, "a"), os.path.join(base, "b")
            subprocess.run(["git", "clone", "-q", origen, a], check=True, capture_output=True)
            for r in (a,):
                git(r, "config", "user.name", "Persona A")
                git(r, "config", "user.email", "a@example.com")
            commit(a, "Persona A", "a@example.com", {"src/api/a.py": "x\n" * 10}, "inicio")
            git(a, "push", "-q", "origin", "main")
            git(a, "remote", "set-head", "origin", "main")
            docviva.preparar_rama(a)
            d = {"proyecto": {"nombre": "Compartido"}, "modulos": [
                {"id": "api", "nombre": "API", "ruta": "src/api", "resumen": "Datos."}],
                "actividad": {"resumen": "Base."}}
            ruta = os.path.join(base, "e.json")
            escribir_json(ruta, d)
            docviva.construir(a, ruta)
            docviva.confirmar(a)
            git(a, "push", "-q", "origin", docviva.RAMA)

            subprocess.run(["git", "clone", "-q", origen, b], check=True, capture_output=True)
            git(b, "config", "user.name", "Persona B")
            git(b, "config", "user.email", "b@example.com")
            s = docviva.estado(b)
            self.assertTrue(s["documentada"])
            self.assertFalse(s["desactualizada"])
            docviva.preparar_rama(b)
            self.assertTrue(os.path.isfile(os.path.join(docviva._ruta_worktree(b), "docs", "documentacion", "index.html")))
            self.assertEqual(git(b, "branch", "--show-current").strip(), "main")
        finally:
            for r in (os.path.join(base, "a"), os.path.join(base, "b")):
                if os.path.isdir(r):
                    shutil.rmtree(docviva._ruta_worktree(r), onerror=_borrar, ignore_errors=True)
            shutil.rmtree(base, onerror=_borrar, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
