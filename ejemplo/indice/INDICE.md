# Índice de la documentación: Tienda Demo

Tienda en línea de ejemplo. El cliente busca productos en un catálogo, los guarda en un carrito, paga con tarjeta a través de una pasarela externa y recibe una factura en PDF por correo. Después puede consultar su historial de pedidos.

- Tecnologías: Python, HTML, Pasarela de pagos
- Al día hasta el commit `2097894` (2026-11-23, rama `main`).

## Cómo leer esto

Está hecho para que una persona o una herramienta entienda el proyecto sin recorrer todo el código.

1. Lee esta página primero: da el mapa completo.
2. Para entender un módulo, abre su ficha (columna Ficha): explica qué es, por qué existe y cómo funciona.
3. Para saber a qué módulo pertenece un archivo, usa el mapa de rutas.
4. Abre el código fuente solo de los archivos clave del módulo que necesitas.
5. Lo marcado como no verificado no se comprobó: trátalo como una hipótesis.

## Módulos

| Módulo | Ruta | Qué es | Depende de | Principal autor | Última modificación | Verificado | Ficha |
|---|---|---|---|---|---|---|---|
| Catálogo (`catalogo`) | `src/catalogo` | Es la lista de productos que el cliente puede comprar. | ninguno | Lucía Fernández | 2026-10-01 | sí | `modulos/catalogo.md` |
| Carrito (`carrito`) | `src/carrito` | Guarda lo que el cliente quiere comprar mientras sigue navegando. | catalogo | Marcos Díaz | 2026-10-15 | sí | `modulos/carrito.md` |
| Pagos (`pagos`) | `src/pagos` | Cobra el total del carrito a través de la pasarela de pagos y entrega el recibo al cliente. | carrito | Sofía Ortega | 2026-10-28 | no | `modulos/pagos.md` |
| Facturas (`facturas`) | `src/facturas` | Genera la factura en PDF de cada pedido pagado, con los impuestos desglosados línea por línea, y la envía por correo al cliente. | pagos | Lucía Fernández | 2026-10-29 | sí | `modulos/facturas.md` |
| Pedidos (`pedidos`) | `src/pedidos` | Muestra al cliente el historial de lo que ya compró: qué pidió, cuándo, cuánto pagó y el estado de cada pedido. | pagos, facturas | Lucía Fernández | 2026-10-20 | sí | `modulos/pedidos.md` |
| Pantallas web (`web`) | `src/web` | Son las pantallas que ve el cliente: inicio, ficha de producto y pedidos. | catalogo, carrito, pedidos | Sofía Ortega | 2026-10-20 | sí | `modulos/web.md` |

## Mapa de rutas

Qué módulo es dueño de cada carpeta:

- `src/catalogo/` -> Catálogo (`catalogo`)
- `src/carrito/` -> Carrito (`carrito`)
- `src/pagos/` -> Pagos (`pagos`)
- `src/facturas/` -> Facturas (`facturas`)
- `src/pedidos/` -> Pedidos (`pedidos`)
- `src/web/` -> Pantallas web (`web`)

## Dependencias

- carrito -> catalogo
- pagos -> carrito
- facturas -> pagos
- pedidos -> pagos
- pedidos -> facturas
- web -> catalogo
- web -> carrito
- web -> pedidos

## Flujos

### Comprar un producto

1. Cliente -> Pantallas web: elige un producto
2. Pantallas web -> Carrito: lo agrega
3. Carrito -> Carrito: calcula el total
4. Carrito -> Pagos: pide el cobro
5. Pagos -> Pasarela: autoriza el pago
6. Pagos -> Facturas: avisa del pago aprobado
7. Facturas -> Cliente: envía la factura

### Buscar en el catálogo

1. Cliente -> Pantallas web: escribe una búsqueda
2. Pantallas web -> Catálogo: consulta por texto y categoría
3. Catálogo -> Cliente: devuelve los resultados

## Archivos clave

Por dónde entrar al código:

- `src/catalogo/lista.py`: carga y ordena los productos (Catálogo)
- `src/catalogo/busqueda.py`: decide qué productos coinciden con lo que escribió el cliente (Catálogo)
- `src/carrito/carrito.py`: guarda las líneas y las cantidades (Carrito)
- `src/carrito/totales.py`: calcula impuestos, redondeo y total (Carrito)
- `src/pagos/pasarela.py`: habla con la pasarela y define el tiempo máximo de espera (Pagos)
- `src/pagos/reintentos.py`: repite el cobro cuando la pasarela no responde (Pagos)
- `src/pagos/recibo.py`: arma el recibo que ve el cliente (Pagos)
- `src/facturas/numeracion.py`: entrega el siguiente número de factura (Facturas)
- `src/facturas/generar.py`: construye el PDF y desglosa los impuestos (Facturas)
- `src/facturas/envio.py`: envía la factura por correo (Facturas)
- `src/pedidos/historial.py`: consulta y ordena los pedidos del cliente (Pedidos)
- `src/web/inicio.py`: pantalla de inicio con el buscador (Pantallas web)
- `src/web/producto.py`: ficha de un producto (Pantallas web)
- `src/web/pedidos.py`: pantalla del historial de pedidos (Pantallas web)

## Equipo

- Lucía Fernández: principal en Catálogo, Facturas, Pedidos. 5 commits, última actividad 2026-10-29.
- Sofía Ortega: principal en Pagos, Pantallas web. 3 commits, última actividad 2026-10-27.
- Marcos Díaz: principal en Carrito. 4 commits, última actividad 2026-10-28.
- marcos: principal en ninguno. 1 commit, última actividad 2026-10-15.

Posibles duplicados (la misma persona con otro nombre en Git): Marcos Díaz y marcos.

## Últimos cambios

- 2026-11-23, Actualización (commits hasta 2097894). El cobro se reintenta cuando la pasarela no responde y las facturas muestran el impuesto por línea. Módulos: Pagos, Facturas. Hechos por: Lucía Fernández (1), Marcos Díaz (1), Sofía Ortega (1).
- 2026-11-23, Documentación base (commits hasta 8f9872f). Documentación base del proyecto completo. Módulos: Catálogo, Carrito, Pagos, Facturas, Pedidos, Pantallas web. Hechos por: Lucía Fernández (4), Marcos Díaz (3), Sofía Ortega (2), marcos (1).

## Pendiente de comprobar

- No se ejecutó el cobro real con la pasarela; solo se leyó el código del módulo de pagos.
