# Pagos (`pagos`)

- Ruta: `src/pagos`
- Verificado: no, tratar como hipótesis
- Depende de: Carrito (`carrito`)
- Principal autor del código: Sofía Ortega
- También lo tocaron: Marcos Díaz
- Última modificación: 2026-10-28, por Marcos Díaz (Ajusta el tiempo de espera de la pasarela)
- Documentado el 2026-11-23 (commit 2097894). Cambios de esta versión: Marcos Díaz (1), Sofía Ortega (1)

## En pocas palabras

Cobra el total del carrito a través de la pasarela de pagos y entrega el recibo al cliente. Si la pasarela no responde, reintenta el cobro unas veces antes de rendirse. La tarjeta nunca pasa por nuestro código: se manda directo a la pasarela y aquí solo se recibe si el pago fue aprobado o rechazado.

## Por qué existe

Se delega el cobro a una pasarela externa para no guardar datos de tarjeta, lo que nos ahorra obligaciones de seguridad y riesgos legales.

## Cómo funciona

1. Recibe el total del carrito y la referencia del pedido.
2. pasarela.py manda el cobro a la pasarela y espera su respuesta, hasta un tiempo máximo.
3. Si la pasarela no responde a tiempo, reintentos.py vuelve a intentarlo con una espera cada vez mayor.
4. Si la pasarela aprueba, recibo.py genera el recibo y se marca el pedido como pagado.
5. Si rechaza o se agotan los reintentos, se avisa al cliente y el carrito se conserva.

## Datos que maneja

- Pago: referencia del pedido, monto, estado (aprobado, rechazado o pendiente) y fecha.

## Reglas que cumple

- Nunca se guarda el número de la tarjeta.
- Un pedido no se marca como pagado hasta que la pasarela lo apruebe.
- Un reintento usa la misma referencia de pedido, para que la pasarela no cobre dos veces.

## Por dónde empezar a leer el código

- `src/pagos/pasarela.py`: habla con la pasarela y define el tiempo máximo de espera
- `src/pagos/reintentos.py`: repite el cobro cuando la pasarela no responde
- `src/pagos/recibo.py`: arma el recibo que ve el cliente

## Cuidado con

- Un reintento mal hecho puede cobrar dos veces. Por eso cada intento lleva la misma referencia del pedido.

## Qué cambió y por qué

- Antes: Si la pasarela no respondía, el cobro fallaba de inmediato y el cliente tenía que intentarlo otra vez.
- Ahora: El cobro se reintenta varias veces con espera creciente, y el tiempo máximo de espera de la pasarela se ajustó.
- Por qué: Muchos cobros fallaban por cortes breves de la pasarela, no porque la tarjeta fuera rechazada.
- El porqué es según el mensaje del commit.

## Versiones anteriores (1)

Texto que tuvo este módulo antes. La versión vigente es la de arriba.

### Versión del 2026-11-23 (commit 8f9872f)

Cambios de: Sofía Ortega (1)

Cobra el total del carrito a través de la pasarela de pagos y entrega el recibo al cliente. La tarjeta nunca pasa por nuestro código: se manda directo a la pasarela y aquí solo se recibe si el pago fue aprobado o rechazado.
