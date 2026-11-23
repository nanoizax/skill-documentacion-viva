# skill-documentacion-viva

**La documentación de tu proyecto se crea sola la primera vez y se actualiza con cada commit que apruebas. Vive en una rama aparte y dice quién hizo cada módulo.**

Una skill para tu herramienta de desarrollo, con un script que saca la autoría directamente de Git (con 40 pruebas) y genera una página HTML que abres con doble clic.

---

## Para qué fue creada

Esta skill fue creada **para la comunidad**. Casi todos los proyectos llegan a un punto en que nadie sabe cómo funcionan por dentro, ni quién hizo qué. El que llega nuevo tarda semanas en entenderlo, y el documento que alguien escribió una vez ya quedó viejo. Aquí la documentación se genera desde el código y se actualiza cada vez que haces una actividad, sin que nadie tenga que acordarse.

## ¿Qué es esto?

Tres piezas que trabajan juntas:

1. **`SKILL.md`**: el método que sigue tu herramienta: cuándo documentar, cómo pedir permiso y qué analizar.
2. **`scripts/docviva.py`**: lo mecánico y verificable: el estado, la rama de documentación, la autoría desde Git y el HTML. Solo usa Python y Git.
3. **Una rama propia, `docs/documentacion`**, que contiene solo documentos y nunca se mezcla con el código.

## El problema que resuelve

- Nadie entiende el proyecto completo y **las decisiones están en la cabeza de alguien**.
- La documentación existe, pero **quedó vieja** el mismo mes que se escribió.
- No se sabe **quién hizo cada módulo** ni quién tocó algo por última vez.
- En un proyecto de varias personas, **cada quien documenta distinto** o no documenta.
- Leer un proyecto ajeno cuesta días, y el resumen que pide el jefe o el cliente no existe.

## Empezar a trabajar en un proyecto sin explicarlo

Es el primer uso de la skill. Le dices a tu herramienta: "vamos a trabajar este proyecto, descarga el GitHub", y ella sabe qué hacer sola:

- **Si alguien ya lo documentó con esta skill:** va directo a la documentación. Te cuenta en pocas líneas de qué trata el proyecto, qué tecnologías usa, cómo está organizado, dónde está cada cosa, hasta cuándo está al día y cuáles fueron los últimos cambios. Después te pregunta qué vais a hacer. No tienes que explicarle nada, y tampoco lee todo el código.
- **Si nadie lo documentó:** te lo dice y te pide un solo permiso, indicando cuánto tiene que leer. Si aceptas, lee el proyecto completo y deja la documentación en una rama local, sin subirla, para que la siguiente persona (o la siguiente sesión) ya parta de ahí.

Para un junior es entender el proyecto desde el primer minuto. Para un senior es no repetir la misma explicación en cada sesión: solo dice qué hay que hacer.

**Funciona con las frases de siempre**, estés donde estés:

- "Vamos a trabajar este proyecto" o "este es el proyecto" (la carpeta ya está descargada).
- "Descarga este Git, vamos a trabajar en él" (primero lo descarga).
- "¿Está documentado?" Te responde sí o no, con el detalle: dónde está, hasta qué commit está al día, quién la actualizó y cuándo, y cuánto avanzó el código desde entonces. Si no lo está, te ofrece crear la rama.

**Subirla o no es decisión tuya.** Cuando termina de crear la base te pregunta si la subes al remoto o la dejas solo en tu equipo. Mucha gente trabaja con su documentación en local, y funciona igual: solo que nadie más la ve. No sube nada si no se lo dices.

**Además se alimenta sola:** cuando haces commit o push, hace una revisión liviana de lo que subes (solo ese cambio, nunca el proyecto entero) y actualiza la documentación, con el mismo permiso que le diste al commit.

## Para qué sirve

- **Primera vez en un proyecto que ya existe y tiene Git:** analiza el proyecto y crea la documentación base.
- **Cada commit o push que apruebas:** analiza solo lo que cambió y actualiza la documentación.
- Explica cada módulo **completo y sin recortes**, en un lenguaje que entiende un junior y que le sirve a un senior: qué es, por qué existe, cómo funciona paso a paso, qué datos maneja, qué reglas cumple, por dónde empezar a leer el código y qué cuidado hay que tener.
- Dice **qué cambió y por qué** en cada actualización, leyendo el código y no solo el mensaje del commit. Si el autor no explicó el porqué, la página lo dice y marca que fue deducido.
- Dice **quién fue la persona principal de cada módulo**, quién colaboró y quién fue la última en modificarlo.
- Tiene **buscador**: escribes "facturas" y te lleva al módulo; escribes un nombre y ves todo lo que esa persona tocó.
- Muestra el **historial de actualizaciones** y quién hizo cada una.
- Dibuja los **flujos** (quién habla con quién y en qué orden) como diagramas dentro de la propia página.
- Es **una página HTML** que se abre con doble clic, sin servidor y sin internet.

## Cómo funciona el permiso

Nada se sube sin tu aprobación. La pregunta del commit incluye la documentación:

> ¿Hago commit y push de tu actividad y actualizo la documentación en la rama docs/documentacion?

Un solo "sí" cubre las dos cosas. Si dices que no a la documentación, solo se hace lo que aprobaste. El script **nunca hace push**: eso lo decide la herramienta únicamente si lo aprobaste.

## Cuándo usarla

- Llegas a un proyecto que ya existe y quieres dejarlo explicado.
- Trabajas con más personas y quieren una sola fuente de verdad que se mantenga sola.
- Quieres poder decir en una reunión qué se hizo, dónde y quién.

## Cuándo **no** usarla

- Si la carpeta no es un repositorio Git: no se activa.
- Si el código es confidencial y no puedes dejar documentación en el repositorio: la rama de documentación se queda en tu máquina mientras no la subas, pero valóralo antes.
- Si necesitas un manual de usuario con capturas de pantalla: eso lo cubre [`skill-documentacion`](https://github.com/nanoizax/skill-documentacion).

## Cómo instalarla

1. Descarga este repositorio y copia su contenido en una carpeta llamada `documentacion-viva` dentro del directorio de skills de tu herramienta de desarrollo.
2. Necesitas **Python 3.8 o superior** y **Git 2.5 o superior**. En Windows, Mac y Linux funciona igual.
3. Listo. Se activa cuando vas a hacer commit o push de una actividad. También puedes pedirla: "documenta el proyecto" o "abre la documentación".

Cada herramienta guarda sus skills en un sitio distinto; consulta la documentación de la tuya.

## Qué ves al abrirla

Un ejemplo hecho con un proyecto inventado (una tienda, con personas ficticias): [`ejemplo/documentacion-ejemplo.html`](ejemplo/documentacion-ejemplo.html). Descarga el archivo y ábrelo con doble clic. Tiene:

- **Buscador** arriba (atajo: tecla `/`). Encuentra módulos, personas, flujos y actividades, ignora tildes y mayúsculas, entiende plurales ("facturas" encuentra "factura") y también busca en las versiones anteriores, avisándote cuando la coincidencia está ahí.
- **Resumen** del proyecto, tecnologías y hasta qué commit está al día.
- **Equipo:** cada persona con su actividad reciente y los módulos donde es la principal, con un botón para ver todo lo que tocó.
- **Módulos:** un índice y una ficha completa por módulo, con quién lo escribió, quién lo tocó por última vez y de qué depende.
- **Flujos** como diagramas.
- **Historial** de cada actualización y **lo que no se pudo verificar**.

## El proyecto se lee completo una sola vez

Leer todo el código gasta mucha cuota, así que la skill lo hace únicamente cuando hace falta:

- **Primera vez:** si ninguna rama (ni en tu equipo ni en el remoto) tiene la documentación, lee el proyecto completo y crea la base. Te avisa antes del tamaño.
- **Si el repositorio ya tiene la rama de documentación**, aunque la haya subido otra persona y tú todavía no la tengas, la trae y parte de ella. No relee el código: lee el índice.
- **Cuando el código avanza**, analiza solo los módulos que cambiaron.
- **Si no puede preguntar al remoto** (sin conexión o sin permiso), no analiza todo a ciegas: te pregunta.
- **Si la historia del repositorio se reescribió**, te pregunta antes de rehacer la base.

El comando `estado` decide esto y devuelve una `accion` clara: `analisis_completo`, `leer_documentacion`, `actualizar`, `confirmar_con_el_usuario` o `rehacer_base_con_permiso`. Para saber si el remoto ya tiene la rama trae solo esa rama, nunca el resto del repositorio.

## Un índice para leer el proyecto sin recorrer el código

Junto a la página HTML se genera un **índice en texto** que cualquier herramienta de desarrollo entiende al instante, y que también sirve a una persona con prisa. Leerlo cuesta mucho menos que abrir decenas de archivos de código.

- **`INDICE.md`:** el mapa completo en una página. Una tabla con todos los módulos (qué son, de qué dependen, quién los escribió y cuándo se tocaron por última vez), qué carpeta es de cada módulo, las dependencias, los flujos paso a paso, los archivos por donde entrar al código y el equipo.
- **`modulos/<id>.md`:** la ficha completa de cada módulo, para abrir solo la que hace falta.
- **`indice.json`:** lo mismo en formato máquina.
- **Se actualiza solo:** se genera cada vez que se construye la documentación, así que nunca queda atrasado respecto a la página.
- **Sin correos:** igual que la página.

El comando `indice` lo lee directamente de la rama, sin tocar nada ni pedir permiso:

```
python scripts/docviva.py indice                    # el mapa completo
python scripts/docviva.py indice --buscar facturas  # en qué módulo mirar
python scripts/docviva.py indice --modulo pagos     # la ficha completa de un módulo
```

El orden de lectura que sigue la herramienta es: índice, ficha del módulo y, solo si hace falta, el código de los archivos clave de ese módulo. Hay un ejemplo en [`ejemplo/indice/`](ejemplo/indice/INDICE.md).

## Cuando dos personas tocan el mismo código

La página muestra siempre la **versión más actual** de cada módulo. Debajo, un desplegable **Versiones anteriores** guarda los textos que tuvo antes, cada uno con la fecha, el commit hasta el que estaba al día y **quiénes tocaron ese código** en ese momento. Así ves cómo evolucionó un módulo y quién estuvo detrás de cada cambio, sin perder lo que se documentó antes.

- Solo se archiva una versión cuando el texto del módulo cambia de verdad, no en cada commit.
- Se conservan hasta 20 versiones por módulo.
- Las correcciones de autoría (por ejemplo, quién escribió un PR) se aplican también a las versiones viejas.

## Varias personas en el mismo proyecto

- La rama de documentación contiene solo documentos, así que **no choca con los PR del código**.
- Si otra persona ya subió la rama, la tuya se pone al día con la suya antes de actualizar.
- Cada persona documenta la rama donde acaba de trabajar, y la actualización incluye solo lo que esa rama cambió.
- **Los nombres y las fechas salen de Git, no de la herramienta**, así que no se inventan. Los correos no aparecen en ninguna parte.

## Qué incluye

- **`estado`:** dice si hay documentación, si quedó atrás, cuántos commits faltan y qué módulos se tocaron.
- **`preparar-rama`:** crea la rama de documentación en un espacio aparte, sin mover tu rama de trabajo.
- **`construir`:** une el análisis con la autoría y escribe la página. Además devuelve **avisos de calidad** sobre el análisis: resúmenes demasiado cortos o que solo repiten el nombre, falta del porqué, de los pasos o de los archivos clave, y cambios sin explicar qué había antes. La herramienta los corrige antes de confirmar.
- **`confirmar`:** hace el commit de la documentación en su rama, sin push.
- **`abrir`:** abre la página en tu navegador.
- **`indice`:** lee el índice en texto, busca por palabra o da la ficha de un módulo.
- **`references/guia-de-analisis.md`:** la guía de cómo analizar y escribir bien. La herramienta la lee solo cuando documenta.
- **`references/formato-del-analisis.md`:** el formato del análisis y las reglas de autoría con varias personas. También se lee solo al documentar, para que leer un proyecto ya documentado cueste lo menos posible.
- **Ahorro de cuota:** la documentación no tiene tope de palabras, porque tiene que quedar completa. El ahorro está en que la primera pasada te avisa del tamaño antes de empezar y las siguientes analizan solo lo que cambió.

## Cómo está organizado el código

Para quien quiera revisarlo o mejorarlo. El script `scripts/docviva.py` solo recibe los comandos; el trabajo está en `scripts/docviva_lib/`, con una pieza por responsabilidad:

- `gitutil.py`: las llamadas a Git.
- `autoria.py`: quién hizo qué, sacado del historial.
- `rama.py`: el estado de la documentación y la rama aparte.
- `construccion.py`: une el análisis con la autoría y guarda las versiones.
- `calidad.py`: los avisos sobre el análisis.
- `indice.py`: el índice en texto, las fichas por módulo y la búsqueda por palabra.
- `pagina.py` y `plantilla/` (`estilos.css` y `buscador.js`): la página. El diseño y el buscador son archivos normales, no texto dentro del código.

Las pruebas están en `tests/`. La lógica del buscador se prueba con Node si está instalado.

## Límites honestos

- **"Principal autor" significa quien escribió más líneas en ese módulo**, no quien lo diseñó. Git cuenta quién hizo el commit, no quién tuvo la idea.
- **Los PR que se integran en un solo commit** (por ejemplo `Merged PR 21` en Azure DevOps) aparecen a nombre de quien los completó. La skill los detecta, lo avisa en la página y te pide que indiques quién los escribió. Esa corrección se guarda en `autores.json` para todo el equipo.
- **La misma persona con dos nombres o correos** aparece duplicada hasta que añadas un archivo `.mailmap`. La skill lo detecta y lo sugiere, pero no lo crea sin tu permiso.
- **La calidad de la explicación depende del análisis de la herramienta.** El script garantiza la autoría, la rama y la página, y los avisos de calidad señalan lo flojo, pero no pueden juzgar si una explicación es acertada. Léela antes de confiar en ella.
- **El porqué de un cambio a veces se deduce.** Si el autor escribió un commit pobre, la página lo marca como deducido del código. Puede estar equivocado.
- **La herramienta lee el código, no lo ejecuta.** Lo que no se comprobó aparece en la sección "Sin verificar". No sustituye a pruebas ni a revisión.
- **El buscador es de texto, no de significado:** encuentra palabras (con tildes y plurales), no sinónimos.
- **El índice es tan bueno como el análisis que lo alimenta.** Cuánto ahorra leerlo en lugar del código depende del tamaño de tu proyecto y de lo bien documentado que esté. No lo he medido con un proyecto grande real.
- **Si el código avanzó, el índice puede ir atrasado.** El comando `estado` lo dice y señala qué módulos cambiaron; para esos conviene leer el código.
- **La documentación refleja la última actividad documentada**, no necesariamente la rama principal.
- **La primera pasada en un proyecto grande gasta bastante cuota.** Por eso se hace por partes y se avisa antes.
- Si alguien reescribe la historia del repositorio, la documentación se rehace desde cero.

## Skills relacionadas

- [`skill-documentacion`](https://github.com/nanoizax/skill-documentacion): el flujo completo de documentación con manual de usuario y capturas. Esta skill es su versión viva y automática.
- [`skill-decisiones-de-arquitectura`](https://github.com/nanoizax/skill-decisiones-de-arquitectura): el porqué de cada decisión, que esta página puede enlazar.
- [`skill-commits-limpios`](https://github.com/nanoizax/skill-commits-limpios): para que el commit que dispara la documentación salga bien hecho.

## Licencia y autoría

[MIT](LICENSE) · Hecha por Leandro Manuel Perez Montañana.
Más skills y herramientas gratis en **[soytegno.sonholab.com](https://soytegno.sonholab.com)** · TikTok [@soytegno](https://www.tiktok.com/@soytegno)
