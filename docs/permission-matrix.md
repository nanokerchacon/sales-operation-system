# Permission Matrix

Fecha: 2026-03-16

Documento complementario a [access-control-design.md](C:\Proyectos\sales-operation-system\docs\access-control-design.md).

## Convenciones

Valores usados:

- `full`: acceso total al módulo o acción
- `scoped`: acceso permitido pero filtrado por alcance
- `read`: solo lectura
- `none`: sin acceso
- `future`: reservado para fase posterior

## Roles

- `direccion_general`
- `comercial`
- `finanzas`
- `admin`
- `operaciones` futuro

## 1. Módulos

| Permiso de módulo | direccion_general | comercial | finanzas | admin | operaciones |
| --- | --- | --- | --- | --- | --- |
| `dashboard.view` | full | full | full | full | future |
| `clients.view` | full | scoped | full | full | future |
| `orders.view` | full | scoped | read | full | future |
| `deliveries.view` | full | scoped | full | full | future |
| `invoices.view` | full | scoped | full | full | future |
| `products.view` | full | scoped | read | full | future |
| `incidents.view` | full | scoped | full | full | future |
| `admin.view` | full | none | none | full | none |
| `finance.view` | full | none | full | full | none |
| `operations.view` | full | none | none | full | future |

## 2. Acciones principales

| Permiso de acción | direccion_general | comercial | finanzas | admin | operaciones |
| --- | --- | --- | --- | --- | --- |
| `clients.create` | full | scoped | none | full | future |
| `clients.update` | full | scoped | limited | full | future |
| `orders.create` | full | scoped | none | full | future |
| `orders.update` | full | scoped | none | full | future |
| `deliveries.create` | full | limited | full | full | future |
| `invoices.create` | full | limited | full | full | future |
| `products.create` | full | none | none | full | future |
| `products.update` | full | none | none | full | future |
| `incidents.create_commercial` | full | scoped | none | full | future |
| `incidents.create_admin` | full | none | full | full | future |
| `admin.manage_users` | full | none | none | full | none |
| `admin.manage_roles` | full | none | none | full | none |
| `admin.assign_clients` | full | none | none | full | none |

Notas:

- `limited` significa acceso funcional permitido, pero acotado por workflow o por campos.
- En primera fase se puede simplificar `limited` a `read` o `full` según el coste real.

## 3. Datos sensibles

| Permiso sensible | direccion_general | comercial | finanzas | admin | operaciones |
| --- | --- | --- | --- | --- | --- |
| `clients.view_sensitive` | full | none | full | full | future |
| `orders.view_amounts` | full | scoped | full | full | future |
| `invoices.view_amounts` | full | scoped | full | full | future |
| `finance.view_collections` | full | none | full | full | none |
| `finance.view_due_dates` | full | none | full | full | none |
| `incidents.view_internal_notes` | full | none | full | full | future |

## 4. Alcance de datos

| Recurso | direccion_general | comercial | finanzas | admin | operaciones |
| --- | --- | --- | --- | --- | --- |
| Clientes | all | assigned_clients | all | all | future |
| Pedidos | all | assigned_clients | read_all_or_limited | all | future |
| Albaranes | all | assigned_clients | all | all | future |
| Facturas | all | assigned_clients | all | all | future |
| Productos | all | all_read_or_scoped | all_read | all | future |
| Incidencias comerciales | all | assigned_clients | read_if_related | all | future |
| Incidencias administrativas | all | none | all | all | future |

## 5. Reglas recomendadas por rol

### `direccion_general`

- alcance global
- visibilidad de importes y datos sensibles
- acceso a administración

### `comercial`

- alcance por clientes asignados
- puede ver y operar sobre su cartera
- no debe ver cobros y vencimientos globales
- no debe administrar usuarios ni roles

### `finanzas`

- alcance amplio en clientes y documentos financieros
- acceso a importes, cobros y vencimientos
- sin responsabilidad de administración técnica

### `admin`

- control total del sistema de acceso
- acceso pleno en primera fase por practicidad
- en segunda fase conviene revisar si debe seguir viendo toda la operación

### `operaciones`

- reservado
- no activar en primera entrega

## 6. Catálogo inicial recomendado de permisos

### Dashboard

- `dashboard.view`

### Clientes

- `clients.view`
- `clients.create`
- `clients.update`
- `clients.view_sensitive`

### Pedidos

- `orders.view`
- `orders.create`
- `orders.update`
- `orders.view_amounts`

### Albaranes

- `deliveries.view`
- `deliveries.create`

### Facturas

- `invoices.view`
- `invoices.create`
- `invoices.view_amounts`

### Productos

- `products.view`
- `products.create`
- `products.update`

### Incidencias

- `incidents.view`
- `incidents.create_commercial`
- `incidents.create_admin`
- `incidents.view_internal_notes`

### Finanzas

- `finance.view`
- `finance.view_collections`
- `finance.view_due_dates`

### Administración

- `admin.view`
- `admin.manage_users`
- `admin.manage_roles`
- `admin.assign_clients`

## 7. Recomendación de simplificación para primera fase

Para no complicar en exceso el primer despliegue, el sistema puede arrancar con esta reducción:

### Roles activos

- `direccion_general`
- `comercial`
- `finanzas`
- `admin`

### Alcances activos

- `all`
- `assigned_clients`

### Permisos sensibles activos

- `clients.view_sensitive`
- `orders.view_amounts`
- `invoices.view_amounts`
- `finance.view_collections`
- `finance.view_due_dates`

### Lo que se deja para segunda fase

- equipos
- alcance por equipo
- permisos por campo más finos
- diferenciación avanzada entre incidencias operativas y administrativas
