# Facturas (`facturas`)

- Ruta: `src/facturas`
- Verificado: sí
- Depende de: Pagos (`pagos`)
- Principal autor del código: Lucía Fernández
- También lo tocaron: Marcos Díaz
- Última modificación: 2026-10-29, por Lucía Fernández (Desglosa los impuestos en la factura)
- Documentado el 2026-11-23 (commit 2097894). Cambios de esta versión: Lucía Fernández (1)

## En pocas palabras

Genera la factura en PDF de cada pedido pagado, con los impuestos desglosados línea por línea, y la envía por correo al cliente. Cada factura lleva un número correlativo que nunca se repite ni se salta, porque así lo exige la normativa fiscal. Se activa solo cuando el pago ya fue aprobado.

## Por qué existe

La factura es un documento legal. Tenerla en un módulo propio permite cambiar el diseño del PDF sin tocar la numeración, que es la parte que no puede fallar.

## Cómo funciona

1. Cuando Pagos confirma un pago aprobado, avisa a este módulo con el pedido.
2. numeracion.py reserva el siguiente número de factura. Si algo falla después, ese número no se reutiliza.
3. generar.py arma el PDF con los datos del cliente y las líneas del pedido, mostrando el impuesto de cada línea y el total.
4. envio.py manda el PDF al correo del cliente y registra que se envió.

## Datos que maneja

- Factura: número, pedido, fecha, cliente, líneas con su impuesto, total y estado del envío.

## Reglas que cumple

- El número de factura es correlativo y no se reutiliza, aunque la factura falle.
- Solo se factura un pedido pagado.
- La suma de los impuestos por línea debe coincidir con el impuesto total.

## Por dónde empezar a leer el código

- `src/facturas/numeracion.py`: entrega el siguiente número de factura
- `src/facturas/generar.py`: construye el PDF y desglosa los impuestos
- `src/facturas/envio.py`: envía la factura por correo

## Cuidado con

- Si dos pedidos se facturan a la vez, la numeración tiene que seguir siendo única. Cualquier cambio en numeracion.py se debe probar con facturas simultáneas.

## Qué cambió y por qué

- Antes: La factura mostraba un solo total con el impuesto incluido.
- Ahora: La factura muestra el impuesto de cada línea por separado y el total de impuestos.
- Por qué: La descripción del commit era muy breve, así que esto se dedujo del código: el generador ahora calcula el impuesto por línea, lo que suele ser un requisito fiscal.
- El porqué es deducido del código; el autor no lo explicó.

## Versiones anteriores (1)

Texto que tuvo este módulo antes. La versión vigente es la de arriba.

### Versión del 2026-11-23 (commit 8f9872f)

Cambios de: Lucía Fernández (1), Marcos Díaz (1)

Genera la factura en PDF de cada pedido pagado y la envía por correo al cliente. Cada factura lleva un número correlativo que nunca se repite ni se salta, porque así lo exige la normativa fiscal. Se activa solo cuando el pago ya fue aprobado.
