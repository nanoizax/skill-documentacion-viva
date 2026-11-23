---
name: documentacion-viva
description: Mantiene al día la documentación de un proyecto en HTML, en una rama aparte de su Git, con buscador, y dice quién hizo cada módulo, qué cambió y por qué. Se activa cuando el usuario dice "vamos a trabajar este proyecto", "descarga el GitHub" o "ponte al día con el proyecto" (si ya está documentado, lo lee y sabe de qué trata sin que se lo expliquen), cuando va a hacer commit o push de una actividad, o cuando pide "documenta el proyecto", "actualiza la documentación", "quién hizo este módulo", "abre la documentación" o "cómo funciona este proyecto". Incluye un índice en texto para que cualquier herramienta entienda el proyecto sin leer todo el código. La primera vez en un proyecto existente analiza todo y crea la documentación base; después analiza lo que cambió, leyendo el código y no solo el mensaje del commit. Sirve para cualquier lenguaje y para proyectos de varias personas.
---

# Documentación viva

La documentación del proyecto vive en la rama `docs/documentacion` del mismo Git, solo con documentos (nunca mezclada con el código), y se actualiza con cada commit o push que el programador aprueba. Es una página HTML con buscador que se abre con doble clic, sin servidor ni internet. Está escrita para que la entienda tanto un junior como un senior.

El script `scripts/docviva.py` (en la carpeta de esta skill) hace lo mecánico: detecta el estado, prepara la rama, saca la autoría de Git y genera el HTML. Tú haces la parte difícil: analizar el código y explicarlo bien. Se ejecuta con `python` (o `python3`) y `--repo <carpeta del proyecto>`.

## Cuándo se activa

- **Al abrir un proyecto:** "vamos a trabajar este proyecto", "este es el proyecto", "descarga este Git", "ponte al día". Da igual si ya está descargado o si hay que descargarlo primero.
- **Cuando pregunten "¿está documentado?"** o algo parecido.
- **Antes de proponer un commit o push** de una actividad terminada.
- **Cuando lo pidan:** "documenta", "actualiza la documentación", "abre la documentación", "¿dónde está X?", "¿cómo funciona esto?".

Si la carpeta no es un repositorio Git, o no tiene ningún commit, no se activa: dilo en una línea.

## Casos comunes

| El usuario dice | Qué haces |
|---|---|
| "Vamos a trabajar este proyecto" / "este es el proyecto" (carpeta ya descargada) | `estado` y actúa según `accion` (ver incorporación). |
| "Descarga este Git, vamos a trabajar en él" | Clona, entra en la carpeta y haz lo mismo. |
| "¿Está documentado?" | `estado` y responde con su campo `respuesta`: sí o no, con el detalle. Si no, ofrece crearla. |
| "Documéntalo" | Crear la base (un permiso, ver incorporación). |
| "Haz commit" / "sube esto" | Actividad primero, luego la documentación en la misma pregunta. |
| "¿Dónde está lo de X?" | `indice --buscar X`. |
| "Abre la documentación" | `abrir`. |
| "Sube la documentación" / "no la subas" | Solo se sube si lo ordena. Si dice que no, queda en su equipo, y eso es válido. |

## ¿Está documentado?

Ejecuta `estado` y contesta con el campo `respuesta`, sin rodeos. Es la pregunta más común y la respuesta es sí o no:

- **Sí:** dónde está (este equipo, el remoto o ambos), hasta qué commit está al día, quién la actualizó y cuándo; y si el código avanzó, cuánto.
- **No:** dilo y ofrece crear la rama: "No está documentado. ¿Creo la rama docs/documentacion y lo documento?"
- **No se pudo comprobar:** dilo, no supongas.

## Al empezar a trabajar en un proyecto (incorporación)

Es el primer uso, y el más importante. Cuando el usuario diga algo como "vamos a trabajar este proyecto", "descarga el GitHub", "clona este repositorio" o "ponte al día con el proyecto": clona o entra en la carpeta y, **antes de preguntarle nada sobre el proyecto**, ejecuta `estado`. Según `accion`:

- **`leer_documentacion` o `actualizar`:** ya está documentado. Lee el índice con `indice` y cuéntale en pocas líneas lo que ya sabes: de qué trata, tecnologías, módulos y dónde está cada cosa (mapa de rutas), hasta qué fecha está al día y cuáles fueron los últimos cambios. Después pregúntale qué van a hacer. No le pidas que te explique el proyecto: ya lo sabes. Es solo lectura, no pide permiso.
- **`analisis_completo`:** nadie lo documentó. Dile que no hay documentación y pide un solo permiso: "Para crearla tengo que leer todo el proyecto (N archivos, M commits). Queda en una rama local, docs/documentacion, y no se sube sin tu orden. ¿La creo?". Si dice que sí, sigue los pasos de documentación (sin commit de ninguna actividad). Si dice que no, trabaja leyendo solo lo que la tarea necesite.

Al terminar de crear la base, dile dónde quedó y pregunta una sola cosa: **¿la subes al remoto o la dejas solo en tu equipo?** Es decisión suya. Mucha gente trabaja con su documentación en local y es perfectamente válido: todo funciona igual, solo que nadie más la ve. No subas nada si no lo dice.
- **Cualquier otra acción:** pregunta, como indican los pasos.

Esto es lo que ahorra explicar el proyecto en cada sesión: el usuario solo dice qué hay que hacer.

## Entender un proyecto ya documentado (modo lectura)

Cuando te pidan algo sobre un proyecto que ya tiene documentación (`estado` dice `documentada`), **lee el índice antes que el código fuente**. Es mucho más corto que recorrer los archivos y ya trae el mapa, la autoría y el porqué.

1. `indice` imprime `INDICE.md`: módulos, qué carpeta es de cada uno, dependencias, flujos, archivos clave y equipo.
2. `indice --buscar <palabras>` busca en toda la documentación (sin tildes, con plurales) y dice en qué módulo mirar.
3. `indice --modulo <id>` imprime la ficha completa de un módulo.
4. Abre el código fuente solo de los archivos clave del módulo que necesitas.
5. Si `estado` dice `desactualizada`, avisa que el índice puede estar atrasado y lee el código de los `modulos_tocados`.

El modo lectura solo lee la rama de documentación: no pide permiso, no cambia nada y no hace falta que la rama esté en tu carpeta de trabajo.

## El permiso (importante)

Nunca hagas commit ni push sin que el usuario lo apruebe. Tampoco la documentación. Leer la documentación que ya existe no necesita permiso. Crear la base la primera vez se aprueba con una pregunta propia (ver incorporación). Las actualizaciones se aprueban **en la misma pregunta** del commit:

> "¿Hago commit y push de tu actividad y actualizo la documentación en la rama docs/documentacion?"

Un solo "sí" cubre las dos cosas. El push de la rama de documentación se hace solo si ese "sí" incluyó el push. Si dice que no a la documentación, haz solo lo que aprobó. La aprobación vale para esa ocasión, no para las siguientes.

## Pasos

1. `estado` (un comando). Primero pregunta al remoto si ya existe la rama de documentación y, si existe, la trae. Hazle caso a `accion`:
   - `analisis_completo`: ninguna rama tiene la documentación, es la primera vez. **Es el único caso en que lees todo el proyecto.**
   - `leer_documentacion`: ya existe y está al día. No leas el código: usa `indice`.
   - `actualizar`: ya existe y el código avanzó. Parte del índice y analiza solo los `modulos_tocados`.
   - `confirmar_con_el_usuario`: no se pudo preguntar al remoto. No analices todo a ciegas: pregunta.
   - `rehacer_base_con_permiso`: la historia del repositorio cambió. Pregunta antes de rehacer la base.
2. **Antes de escribir el análisis, lee `references/guia-de-analisis.md`** (cómo documentar bien) **y `references/formato-del-analisis.md`** (el JSON de entrada y cómo tratar la autoría con varias personas). Solo hace falta al documentar, no al leer.
3. **Primera vez:** di cuánto hay (`tamano`: archivos y commits) y que la primera pasada gasta más cuota. En proyectos grandes analiza por partes, empezando por lo principal.
4. **Actualización:** analiza solo los módulos de `modulos_tocados`. **Lee el cambio real** (`git diff <ultimo_commit>...<rama> -- <ruta>` y los mensajes de los commits), no solo el título. Un commit de un junior puede traer una descripción pobre: el código manda, y lo que deduzcas lo marcas como deducido.
5. Haz el commit o push que el usuario aprobó (con el flujo de commits habitual). La revisión para la documentación es liviana: solo el cambio de esa actividad, nunca el proyecto entero.
6. `preparar-rama`, escribe el análisis en un JSON (formato en `references/formato-del-analisis.md`) y `construir <json>`.
7. `construir` también genera el índice en texto (`INDICE.md`, `indice.json` y una ficha por módulo) para que cualquier herramienta lea la documentación sin recorrer el código. Revisa `avisos` en su respuesta. Son observaciones de calidad: corrige lo que señalan y vuelve a construir (una vez). Luego `confirmar`.
8. Dile al usuario dónde está y cómo abrirla (`abrir`). Si aprobó el push, sube `docs/documentacion`.

## Reglas

0. **El proyecto completo se lee una sola vez.** Si la documentación existe, esté en este equipo o solo en el remoto, nunca vuelvas a leer todo el repositorio: trabaja desde la documentación y lee solo el código que cambió.
1. Lo que no ejecutaste ni comprobaste va en `sin_verificar` y, si es un módulo, con `verificado: false`. No inventes comportamiento.
2. Sin claves, correos ni datos de clientes en el análisis. Si algo usa una clave, di que existe y dónde se configura, no su valor.
3. Si el porqué de un cambio no lo dijo el autor, `cambio.origen` es `deducido` y el texto lo aclara. Si no hay forma de saberlo, dilo; no lo inventes.
4. No toques la rama de trabajo: el script usa un worktree aparte.
5. Si `historia_reescrita` es verdadero, avisa y pregunta antes de rehacer la base: gasta mucha cuota y puede que el usuario prefiera mantener la documentación actual.
6. Escribe sin muletillas ni frases de póster, en el idioma del usuario, con frases concretas.
