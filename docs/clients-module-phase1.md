# Clients Module Phase 1

Fecha: 2026-03-16

## Objetivo

Primer módulo real del ERP sobre la base de seguridad ya implantada.

Incluye:

- listado profesional de clientes
- ficha de cliente
- historial real de pedidos del cliente
- pestañas preparadas para albaranes, facturas e incidencias
- respeto de autenticación, permisos y alcance comercial

## Endpoints

### `GET /clients`

Devuelve listado agregado para el módulo:

- `id`
- `name`
- `tax_id`
- `address`
- `location`
- `email`
- `phone`
- `order_count`
- `total_order_amount`
- `last_order_date`

Acepta búsqueda simple con query param opcional:

- `q`

### `GET /clients/{client_id}`

Devuelve detalle del cliente y resumen agregado:

- datos maestros
- `summary.order_count`
- `summary.total_order_amount`
- `summary.last_order_date`

### `GET /clients/{client_id}/orders`

Devuelve historial real de pedidos visibles para el usuario actual.

## Alcance aplicado

- `comercial`: solo clientes asignados y pedidos relacionados
- `direccion_general`: acceso total
- `admin`: acceso total en esta fase
- `finanzas`: acceso total en esta fase

## Frontend

Rutas añadidas:

- `/clients`
- `/clients/:clientId`

## Decisiones de diseño

- se reutiliza el lenguaje visual del dashboard para mantener coherencia ERP
- el listado de clientes usa agregación backend para evitar lógica duplicada en frontend
- la ficha separa `Resumen`, `Pedidos`, `Albaranes`, `Facturas` e `Incidencias` para dejar preparada la futura vista 360
- solo `Resumen` y `Pedidos` son funcionales en esta fase

## Cómo probar

1. Iniciar sesión con un usuario con permiso `clients.view`
2. Abrir `/clients`
3. Abrir una ficha desde la tabla
4. Verificar la pestaña `Pedidos`
5. Entrar con `comercial@local` y comprobar que solo aparecen clientes de su cartera
