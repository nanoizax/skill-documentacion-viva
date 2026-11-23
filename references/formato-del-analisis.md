# Formato del análisis y reglas de autoría

Léelo al documentar, no al leer. Aquí está el JSON que se manda a `construir` y cómo se trata la autoría cuando hay varias personas.

## El análisis (JSON de entrada)

```json
{"proyecto": {"nombre": "", "resumen": "", "stack": ["..."]},
 "modulos": [{
   "id": "pagos", "nombre": "Pagos", "ruta": "src/pagos",
   "resumen": "qué es, para quién y qué problema resuelve (2 a 5 frases)",
   "por_que": "por qué existe o por qué se hizo así",
   "como_funciona": ["paso 1 (archivo)", "paso 2"],
   "datos": ["qué información maneja"], "reglas": ["reglas que no se pueden romper"],
   "archivos_clave": [{"ruta": "src/pagos/pasarela.py", "para_que": "habla con la pasarela"}],
   "cuidados": ["trampas y errores típicos"], "ejemplo": "un caso real y corto",
   "cambio": {"antes": "", "ahora": "", "por_que": "", "origen": "commit | deducido"},
   "depende_de": ["carrito"], "verificado": true}],
 "flujos": [{"nombre": "Comprar", "pasos": [{"de": "Cliente", "a": "Carrito", "texto": "lo agrega"}]}],
 "actividad": {"resumen": "qué cambió en esta actualización", "modulos_tocados": ["pagos"]},
 "autores_pr": {"916": "Nombre de quien lo escribió"},
 "sin_verificar": ["lo que no pudiste ejecutar o comprobar"]}
```

Obligatorios por módulo: `id`, `nombre`, `ruta` y `resumen`. El resto de campos se llenan cuando aplican. Detalle de qué escribir en cada uno en la guía.

En una actualización manda solo los módulos y flujos que cambiaron; el resto se conserva. No hay tope de palabras: la documentación tiene que quedar completa. El ahorro de cuota está en analizar solo lo que cambió. Si tocaron más de 8 módulos, avisa al usuario antes de seguir.

**Historial por módulo:** si mandas un módulo con texto distinto al que ya había, el script guarda el anterior en "Versiones anteriores" (máximo 20) con quiénes tocaron ese código en cada versión. Tú no escribes ese historial ni borras versiones. Si el texto no cambió, no lo reenvíes.

## Autoría (varias personas)

- **Los nombres, las fechas y las cifras salen del script, nunca de ti.** No los escribas ni los deduzcas. Sin correos en ninguna parte.
- Los merges no cuentan como autoría. "Principal autor" significa quien más líneas escribió en ese módulo, no quien lo diseñó.
- Si el resultado trae `prs_sin_confirmar` (PR integrados en un solo commit, que Git atribuye a quien los completó), pregunta una vez quién los escribió y mándalo en `autores_pr`. Queda guardado en `autores.json` para todo el equipo.
- Si trae `posibles_alias` (la misma persona con dos nombres), avisa y sugiere un `.mailmap`. No lo crees sin permiso.
