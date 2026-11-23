/* Buscador de la documentación. Sin librerías y sin internet.
   La lógica (normalizar, raiz, buscar) no toca la página, para poder probarla aparte. */

function normalizar(t) {
  return String(t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

/* "facturas" encuentra "factura", "clientes" encuentra "cliente". */
function raiz(t) {
  return t.length > 4 ? t.replace(/(es|s)$/, "") : t;
}

/* Devuelve los registros que contienen TODOS los términos, los más relevantes primero. */
function buscar(indice, consulta) {
  var terminos = normalizar(consulta).split(/\s+/).filter(Boolean).map(raiz);
  if (!terminos.length) return [];
  var res = [];
  indice.forEach(function (r) {
    var titulo = normalizar(r.titulo), texto = normalizar(r.texto), antiguo = normalizar(r.antiguo || "");
    var puntos = 0, soloAntiguo = false;
    var coincide = terminos.every(function (t) {
      var enT = titulo.indexOf(t) >= 0, enX = texto.indexOf(t) >= 0, enA = antiguo.indexOf(t) >= 0;
      if (!enT && !enX && !enA) return false;
      puntos += (enT ? 10 : 0) + (enX ? 2 : 0) + (enA ? 1 : 0);
      if (!enT && !enX && enA) soloAntiguo = true;
      return true;
    });
    if (coincide) res.push({ registro: r, puntos: puntos, soloAntiguo: soloAntiguo });
  });
  res.sort(function (a, b) { return b.puntos - a.puntos; });
  return res;
}

if (typeof document !== "undefined") {
  (function () {
    var indice = JSON.parse(document.getElementById("indice").textContent);
    var caja = document.getElementById("buscar");
    var lista = document.getElementById("resultados");

    function ir(registro, soloAntiguo) {
      var el = document.getElementById(registro.id);
      if (!el) return;
      if (soloAntiguo) {
        var d = el.querySelector("details.vers");
        if (d) d.open = true;
      }
      lista.hidden = true;
      el.scrollIntoView({ block: "start" });
      el.classList.add("resaltado");
      setTimeout(function () { el.classList.remove("resaltado"); }, 2500);
      history.replaceState(null, "", "#" + registro.id);
    }

    function mensaje(texto) {
      var p = document.createElement("p");
      p.className = "vacio";
      p.textContent = texto;
      lista.appendChild(p);
    }

    function mostrar() {
      var rs = buscar(indice, caja.value);
      lista.textContent = "";
      lista.hidden = !caja.value.trim();
      if (lista.hidden) return;
      if (!rs.length) { mensaje("Sin resultados para esa búsqueda."); return; }
      var ul = document.createElement("ul");
      rs.slice(0, 12).forEach(function (r) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = "#" + r.registro.id;
        var tipo = document.createElement("span");
        tipo.className = "tipo";
        tipo.textContent = r.registro.tipo;
        a.appendChild(tipo);
        a.appendChild(document.createTextNode(" " + r.registro.titulo));
        if (r.soloAntiguo) {
          var nota = document.createElement("span");
          nota.className = "nota";
          nota.textContent = " (coincide en una versión anterior)";
          a.appendChild(nota);
        }
        a.addEventListener("click", function (ev) { ev.preventDefault(); ir(r.registro, r.soloAntiguo); });
        li.appendChild(a);
        ul.appendChild(li);
      });
      lista.appendChild(ul);
      if (rs.length > 12) mensaje("Hay " + (rs.length - 12) + " resultados más. Añade otra palabra para afinar.");
    }

    caja.addEventListener("input", mostrar);
    caja.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        var rs = buscar(indice, caja.value);
        if (rs.length) ir(rs[0].registro, rs[0].soloAntiguo);
      }
      if (ev.key === "Escape") { caja.value = ""; mostrar(); caja.blur(); }
    });
    document.addEventListener("keydown", function (ev) {
      var activo = document.activeElement;
      if (ev.key === "/" && activo !== caja && !/input|textarea/i.test(activo.tagName)) {
        ev.preventDefault();
        caja.focus();
      }
    });
    document.addEventListener("click", function (ev) {
      if (!ev.target.closest(".busca")) lista.hidden = true;
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-buscar-persona]"), function (b) {
      b.addEventListener("click", function () {
        caja.value = b.getAttribute("data-buscar-persona");
        mostrar();
        caja.focus();
        window.scrollTo(0, 0);
      });
    });
    var q = new URLSearchParams(location.search).get("q");
    if (q) { caja.value = q; mostrar(); }
  })();
}
