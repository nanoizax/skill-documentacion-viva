# Guía de análisis: cómo se arma una buena documentación

Léela antes de escribir el JSON de análisis. Documentar bien es la parte difícil: el script cuida la autoría y la página, pero la calidad de lo que se explica depende de ti.

## 1. Para quién escribes

Escribes para dos personas a la vez: alguien que acaba de llegar y nunca vio el proyecto (un junior, o un senior de otra área) y alguien que lo conoce y busca un dato exacto.

- **Empieza fácil, termina preciso.** El `resumen` debe entenderse sin conocer nada del proyecto. Las demás secciones aportan el detalle técnico.
- **Explica el término la primera vez.** Si usas "cola de mensajes", "idempotente" o "worker", di en la misma frase qué significa en este proyecto.
- **No supongas contexto.** Nunca escribas "como se vio antes" ni "el módulo de siempre". Cada módulo se tiene que poder leer solo.
- **Frases concretas.** "Calcula el total del carrito" es mejor que "gestiona la lógica de totales".

## 2. Cómo estudiar el proyecto

1. Lee primero lo que define el proyecto: README, manifiesto de dependencias (`package.json`, `requirements.txt`, `pom.xml`...), archivo de arranque y rutas.
2. Decide los módulos por **responsabilidad**, no por carpeta. Un módulo es algo que tiene una razón para cambiar. Lo normal son entre 4 y 12; si salen 30, estás cortando demasiado fino.
3. Cada módulo lleva una `ruta` (carpeta) para que el script le asigne quién lo escribió. Usa la carpeta más específica que lo contenga.
4. Anota qué módulo llama a cuál (`depende_de`). Es lo primero que necesita quien va a tocar algo.

## 3. Qué va en cada campo

| Campo | Qué escribir |
|---|---|
| `resumen` | De 2 a 5 frases: qué es, para quién, qué problema resuelve y qué no hace. Mínimo 25 palabras. Sin tope máximo: que quede completo. |
| `por_que` | Por qué existe este módulo o por qué se hizo así. Es lo que el código no dice. |
| `como_funciona` | Pasos en orden, uno por línea, citando el archivo que hace cada cosa. |
| `datos` | Qué información guarda o recibe y con qué forma. |
| `reglas` | Reglas del negocio y validaciones que no se pueden romper. |
| `archivos_clave` | Los 2 a 5 archivos que hay que abrir primero, y para qué sirve cada uno. |
| `cuidados` | Trampas, errores típicos y qué se rompe si se cambia algo. |
| `ejemplo` | Un caso de uso real y corto (una llamada, un comando). |
| `cambio` | Solo en actualizaciones: antes, ahora, por qué y origen (ver sección 4). |
| `depende_de` | Ids de otros módulos documentados. |
| `verificado` | `false` si no ejecutaste ni comprobaste lo que describes. |

Escribe lo que sirva. Un campo que no aplica se omite; un campo relleno por rellenar es peor que uno ausente.

## 4. Actualizaciones: leer el cambio, no solo el título

Cada actualización parte de un commit. Los mensajes de commit varían mucho: un senior suele escribir una buena descripción y un junior a veces deja solo "fix" o "cambios". La documentación no puede depender de eso.

1. **Lee el cambio real.** Para cada módulo tocado: `git diff <ultimo_commit>...<rama> -- <ruta>` y `git log <ultimo_commit>..<rama> --format="%an | %s%n%b" -- <ruta>`.
2. **Reconstruye qué hacía antes y qué hace ahora** mirando las líneas quitadas y las añadidas, no solo los nombres de archivo.
3. **Busca el porqué en este orden:** el cuerpo del commit, el título del commit, comentarios nuevos en el código, nombres de pruebas nuevas.
4. **Marca de dónde sale el porqué** en `cambio.origen`:
   - `"commit"` si lo dijo la persona en el mensaje.
   - `"deducido"` si lo dedujiste del código. Dilo con claridad en el texto, por ejemplo: "el mensaje del commit era muy breve; esto se dedujo del código".
5. **Si no hay forma de saber el porqué, no lo inventes.** Escribe qué cambió y deja el porqué como "no consta en el commit ni en el código".

Cuando el módulo cambia de verdad, el script guarda la versión anterior en el historial. No escribas ni borres versiones.

## 5. Flujos

- Documenta los 3 o 4 recorridos que alguien necesita entender para trabajar en el proyecto, no todos.
- Cada paso es "quién le pide qué a quién". Máximo unos 10 pasos; si hay más, divide el flujo en dos.
- Usa los mismos nombres que los módulos (Carrito, Pagos) para que se vea la relación.
- Un flujo que describes sin haberlo ejecutado se anota en `sin_verificar`.

## 6. Qué no escribir

- Código copiado: se explica, no se pega (salvo el `ejemplo`).
- Claves, tokens, contraseñas, correos o datos de clientes. Si un módulo usa una clave, di que existe y dónde se configura, nunca su valor.
- Adjetivos vacíos ("robusto", "escalable", "potente") y frases de póster.
- Suposiciones presentadas como hechos. Si lo supones, dilo.

## 7. Lo verificable y lo que no

Lo que no ejecutaste ni probaste va en `sin_verificar`, con una frase que diga qué falta comprobar. Es mejor una lista honesta de dudas que una documentación segura de sí misma pero equivocada.

## 8. Ejemplo: débil y bueno

**Débil**, con `resumen` de un módulo de pagos:

> Módulo de pagos. Se encarga de los pagos.

No dice qué hace, ni con qué, ni por qué, ni qué no hace. Un junior sigue sin saber nada.

**Bueno:**

> Cobra el total del carrito a través de la pasarela de pagos y entrega el recibo al cliente. La tarjeta nunca pasa por nuestro código: se manda directo a la pasarela y aquí solo se recibe si el pago fue aprobado o rechazado.

Y en `por_que`: "Se delega el cobro a una pasarela externa para no guardar datos de tarjeta, lo que nos ahorra obligaciones de seguridad y riesgos legales."

**`cambio` bien hecho**, cuando el commit decía solo "reintentos":

> antes: "Si la pasarela no respondía, el cobro fallaba de inmediato."
> ahora: "El cobro se reintenta varias veces con espera creciente."
> por_que: "El mensaje del commit era muy breve; se dedujo del código que el objetivo es soportar cortes breves de la pasarela."
> origen: "deducido"

## 9. Antes de construir

- ¿Lo entendería alguien que nunca vio el proyecto?
- ¿Cada módulo dice qué es, por qué existe y cómo funciona?
- ¿En cada módulo actualizado hay `cambio` con antes, ahora, por qué y origen?
- ¿Marqué como `deducido` todo lo que no dijo el autor?
- ¿Hay claves, correos o datos de clientes? Quítalos.
- ¿Lo que no comprobé está en `sin_verificar`?
