# Security Phase 1

Fecha: 2026-03-16

## Alcance implementado

Esta fase introduce:

- autenticación real por token bearer opaco
- usuarios, roles, permisos y asignación usuario-rol
- `client_assignments` para cartera comercial mínima
- `GET /auth/me`
- `POST /auth/login`
- protección de endpoints principales
- alcance comercial mínimo en clientes, pedidos, albaranes e invoices
- sesión real en frontend
- `react-router`
- `RequireAuth`
- `RequirePermission`
- sidebar dinámico por rol y permisos

## Modelos añadidos

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`
- `client_assignments`
- `auth_sessions`

## Usuarios seed locales

Script:

- `backend/scripts/seed_security.py`

Usuarios creados por defecto en local:

- `direccion@local` / `Local123!`
- `comercial@local` / `Local123!`
- `finanzas@local` / `Local123!`
- `admin@local` / `Local123!`

El usuario comercial recibe asignación automática sobre los primeros clientes existentes, si los hay.

## Endpoints nuevos

- `POST /auth/login`
- `GET /auth/me`

## Endpoints protegidos en esta fase

- `GET/POST /clients`
- `GET/POST /orders`
- `GET /orders/{order_id}/traceability`
- `GET/POST /deliveries`
- `GET/POST /invoices`
- `GET/POST /products`
- endpoints de `dashboard`
- `GET /operations/status`
- `GET /status/summary`

## Alcance aplicado

### Dirección General

- acceso total en esta fase

### Admin

- acceso total en esta fase

### Finanzas

- acceso completo a módulos protegidos en esta fase

### Comercial

- solo ve clientes asignados en `client_assignments`
- solo ve pedidos de esos clientes
- solo ve albaranes y facturas vinculados a esos clientes
- el dashboard se calcula también sobre ese subconjunto

## Cómo arrancar y probar

### Backend

1. Levantar PostgreSQL:

```powershell
docker compose up -d db
```

2. Instalar dependencias del backend.

3. Iniciar la API.

Nota importante:

- El proyecto arrastra deuda técnica histórica entre `create_all` y Alembic.
- Para no romper el arranque actual, esta fase mantiene `AUTO_CREATE_SCHEMA=true` por defecto.
- Se añade migración Alembic para la parte de seguridad, pero la unificación total del esquema sigue pendiente.

4. Ejecutar seed de seguridad:

```powershell
cd backend
python scripts/seed_security.py
```

### Frontend

1. Instalar dependencias del frontend.

Nota:

- se ha añadido `react-router-dom` a `frontend/package.json`
- si el entorno local usa `package-lock.json`, conviene regenerarlo con `npm install`

2. Iniciar frontend.

3. Abrir `/login` y entrar con uno de los usuarios seed.

## Pruebas manuales mínimas

### Login

- acceder a `/login`
- usar `admin@local` / `Local123!`
- comprobar redirección a `/dashboard`

### `/auth/me`

- con token activo debe devolver usuario, rol principal y permisos
- sin token debe devolver `401`

### Rutas protegidas

- abrir `/dashboard` sin login debe redirigir a `/login`
- abrir `/orders/1/traceability` sin login debe redirigir a `/login`

### Sidebar por rol

- `comercial@local` debe ver: Dashboard, Clientes, Pedidos, Incidencias, Productos
- `finanzas@local` debe ver: Dashboard, Clientes, Albaranes, Facturas, Incidencias
- `admin@local` debe ver: Dashboard, Administración
- `direccion@local` debe ver: Dashboard, Clientes, Pedidos, Albaranes, Facturas, Incidencias, Productos, Administración

### Alcance comercial

- `comercial@local` no debe listar clientes fuera de su cartera
- su dashboard debe reflejar solo pedidos de clientes asignados

## Pendientes para fase 2

- unificar completamente Alembic y eliminar `create_all` del arranque
- permisos finos por acción más completos
- permisos de datos sensibles
- equipos y alcance por equipo
- incidencias persistidas reales
- logout explícito y refresh de sesión si se decide
- placeholders de módulos convertidos en módulos funcionales
