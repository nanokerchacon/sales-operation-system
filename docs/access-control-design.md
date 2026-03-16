# Access Control Design

Fecha: 2026-03-16

Documento de referencia complementario a [erp-audit.md](C:\Proyectos\sales-operation-system\docs\erp-audit.md).

## Objetivo

Definir la base de seguridad, permisos, alcance de datos y navegación por perfil para evolucionar la aplicación actual hacia un ERP profesional, sin implementar todavía toda la funcionalidad final.

Este diseño se apoya en el estado real del proyecto:

- Backend actual: FastAPI + SQLAlchemy + PostgreSQL
- Frontend actual: React + Vite + Tailwind
- Módulos reales hoy: dashboard, pedidos, albaranes, facturas, clientes, productos
- Sin autenticación ni autorización
- Sin routing robusto en frontend

## 1. Decisión recomendada

### Opción elegida

RBAC con permisos finos + alcance de datos por cartera/equipo.

### Opciones evaluadas

#### 1. RBAC simple

Consiste en asignar un rol y dar acceso fijo por rol.

Ventajas:

- simple de arrancar
- poco coste inicial

Problemas en este proyecto:

- no resuelve que dos comerciales vean carteras distintas
- obliga a meter lógica especial fuera del modelo de permisos
- escala mal cuando aparezcan Operaciones, Administrador y equipos

Conclusión:

Insuficiente para este ERP.

#### 2. RBAC con permisos finos

Consiste en roles que agrupan permisos de módulo y acción.

Ventajas:

- mantenible
- permite controlar lectura, edición, exportación y visibilidad de datos sensibles

Problemas en este proyecto:

- sigue sin resolver bien el alcance comercial por cartera o equipo
- obliga a filtrar datos con reglas ad hoc por endpoint

Conclusión:

Mejor que RBAC simple, pero todavía incompleto.

#### 3. RBAC con permisos finos + alcance por cartera/equipo

Consiste en:

- roles para agrupar capacidades
- permisos finos para acciones
- reglas de alcance para restringir qué datos puede ver cada usuario

Ventajas:

- encaja con Dirección General, Comercial, Finanzas y Admin
- permite crecer a Operaciones sin rehacer el sistema
- separa claramente capacidad funcional y visibilidad de datos
- evita replicar lógica de seguridad en frontend

Coste:

- algo más de diseño inicial
- requiere disciplina en filtros backend

Conclusión:

Es la opción correcta para este proyecto.

## 2. Principios de diseño

### Separación de responsabilidades

El sistema debe distinguir siempre entre:

1. Autenticación

- quién es el usuario

2. Autorización funcional

- qué módulos y acciones puede ejecutar

3. Alcance de datos

- sobre qué clientes, pedidos o documentos puede actuar

4. Sensibilidad de datos

- si puede ver importes, estados financieros, cobros, vencimientos o notas internas

### Reglas clave

1. Nunca confiar solo en el frontend.

2. El backend decide siempre:

- si un usuario puede entrar en un endpoint
- qué registros devuelve ese endpoint
- qué campos sensibles expone

3. El frontend mejora la UX:

- oculta módulos sin acceso
- deshabilita acciones no permitidas
- limpia la navegación por perfil

4. Los roles iniciales deben ser pocos y claros, pero el sistema debe soportar permisos adicionales sin rediseño.

## 3. Modelo conceptual recomendado

### Capas

#### Capa A. Identidad

- usuarios
- credenciales
- estado activo/inactivo

#### Capa B. Roles y permisos

- rol principal
- uno o varios roles asignables
- permisos granulares

#### Capa C. Alcance

- acceso global
- acceso por cartera asignada
- acceso por equipo
- acceso por recursos propios

#### Capa D. Perfil de navegación

- módulos visibles
- acciones visibles
- widgets y KPIs visibles

## 4. Modelo de datos propuesto

### 4.1 Tablas principales

#### `users`

Propósito:

- identidad del usuario del ERP

Campos mínimos recomendados:

- `id`
- `email` unique
- `password_hash`
- `full_name`
- `is_active`
- `default_role_code`
- `timezone`
- `locale`
- `last_login_at`
- `created_at`
- `updated_at`

Campos útiles a medio plazo:

- `job_title`
- `avatar_url`
- `must_change_password`

#### `roles`

Propósito:

- agrupar permisos funcionales

Campos:

- `id`
- `code` unique
- `name`
- `description`
- `is_system`
- `created_at`

Roles iniciales:

- `direccion_general`
- `comercial`
- `finanzas`
- `admin`
- `operaciones` reservado para futuro

#### `permissions`

Propósito:

- catálogo estable de permisos atómicos

Campos:

- `id`
- `code` unique
- `module`
- `action`
- `description`
- `is_sensitive`

Ejemplos:

- `dashboard.view`
- `clients.view`
- `clients.update`
- `clients.view_sensitive`
- `orders.view`
- `orders.create`
- `orders.update`
- `deliveries.view`
- `invoices.view`
- `finance.view_collections`
- `admin.manage_users`

#### `user_roles`

Propósito:

- permitir uno o varios roles por usuario

Campos:

- `user_id`
- `role_id`
- `assigned_at`
- `assigned_by_user_id`

Recomendación:

- mantener un rol principal visible en UI
- permitir roles adicionales solo si aportan valor real

#### `role_permissions`

Propósito:

- asignar permisos a roles

Campos:

- `role_id`
- `permission_id`
- `granted_at`

### 4.2 Alcance de datos

#### `user_scope_rules`

Propósito:

- definir el tipo de alcance global del usuario

Campos:

- `id`
- `user_id`
- `scope_type`
- `module` nullable
- `allow_sensitive_data`
- `notes`

Valores recomendados de `scope_type`:

- `all`
- `assigned_clients`
- `assigned_documents`
- `team_clients`
- `own_records`
- `none`

Regla:

- el alcance puede ser global o por módulo
- ejemplo: Finanzas puede tener `all` en facturas y cobros, pero no en productos de administración

#### `client_assignments`

Propósito:

- asignar clientes a comerciales

Campos:

- `id`
- `client_id`
- `user_id`
- `assignment_role`
- `is_primary`
- `starts_at`
- `ends_at`

Valores de `assignment_role`:

- `account_owner`
- `support_commercial`

Uso:

- base mínima para cartera comercial

#### `teams`

Propósito:

- preparar alcance por equipo sin activarlo aún en toda la app

Campos:

- `id`
- `code`
- `name`
- `team_type`

Ejemplos:

- `sales_north`
- `finance`
- `operations`

#### `team_members`

Campos:

- `team_id`
- `user_id`
- `member_role`

#### `team_client_assignments`

Opcional para segunda fase.

Propósito:

- asignar carteras a equipos en vez de solo a usuarios

Campos:

- `team_id`
- `client_id`

### 4.3 Relación futura con dominio ERP

Para que el alcance funcione bien, conviene prever estos campos en modelos existentes en segunda fase:

#### `clients`

Añadir después:

- `primary_account_manager_user_id`
- `account_team_id`

#### `orders`

Añadir después:

- `owner_user_id`
- `created_by_user_id`

No es obligatorio para la primera entrega si el filtro se apoya en `client_id`.

## 5. Tipos de permisos

### 5.1 Permisos de módulo

Definen si el usuario puede entrar o no en una sección.

Ejemplos:

- `dashboard.view`
- `clients.view`
- `orders.view`
- `deliveries.view`
- `invoices.view`
- `products.view`
- `incidents.view`
- `admin.view`

Uso:

- muestran u ocultan rutas y entradas del sidebar

### 5.2 Permisos de acción

Definen lo que puede hacer dentro del módulo.

Ejemplos:

- `clients.create`
- `clients.update`
- `clients.archive`
- `orders.create`
- `orders.update`
- `deliveries.create`
- `invoices.create`
- `products.update`
- `incidents.create`
- `admin.manage_users`

Uso:

- habilitan o deshabilitan botones, formularios y acciones backend

### 5.3 Permisos de datos sensibles

Definen acceso a información financiera o interna.

Ejemplos:

- `clients.view_sensitive`
- `orders.view_amounts`
- `invoices.view_amounts`
- `finance.view_collections`
- `finance.view_due_dates`
- `incidents.view_internal_notes`

Uso:

- evitar que un comercial vea datos financieros internos que no necesita

### 5.4 Alcance de datos

Define sobre qué registros aplican los permisos.

Ejemplos:

- Dirección General: `all`
- Comercial: `assigned_clients`
- Finanzas: `all` para clientes, albaranes, facturas y finanzas
- Admin: `all` en administración, pero no necesariamente en explotación si así se decide

## 6. Matriz funcional inicial por rol

La matriz detallada está en [permission-matrix.md](C:\Proyectos\sales-operation-system\docs\permission-matrix.md).

Resumen:

### `direccion_general`

- acceso completo a todos los módulos del ERP
- acceso a datos sensibles
- alcance global

### `comercial`

- acceso a dashboard comercial
- acceso a clientes, pedidos, incidencias comerciales y productos
- acceso restringido a su cartera
- sin acceso general a cobros, vencimientos y administración

### `finanzas`

- acceso a clientes, albaranes, facturas, cobros, vencimientos e incidencias administrativas
- acceso a datos sensibles financieros
- alcance amplio sobre clientes y documentos financieros

### `admin`

- acceso al módulo de administración y gestión de usuarios/roles
- capacidad operativa total sobre seguridad
- acceso funcional al resto según se decida

Recomendación:

- para el primer despliegue, `admin` puede heredar permisos amplios
- a medio plazo conviene separar `admin técnico` de `dirección`

### `operaciones`

No implementar aún como módulo completo, pero reservar:

- dashboard operativo
- pedidos
- albaranes
- incidencias operativas

## 7. Diseño backend recomendado

### 7.1 Autenticación

#### Recomendación inicial

JWT con access token corto + refresh token rotatorio o sesión persistida server-side.

Para este proyecto, la opción más pragmática en primera fase es:

- login con email/password
- access token de corta duración
- refresh token almacenado de forma segura

Ventajas:

- encaja bien con FastAPI
- facilita SPA en React
- soporta despliegue futuro con frontend/backend separados

No implementar aún en este paso, solo dejarlo diseñado.

#### Endpoints previstos

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

### 7.2 Autorización

#### Patrón recomendado en FastAPI

Usar dependencias, no middleware genérico para toda la lógica.

Componentes:

- `get_current_user()`
- `require_permission("clients.view")`
- `require_any_permission([...])`
- `build_access_context()`

Razón:

- más explícito en cada endpoint
- más fácil de testear
- mejor trazabilidad de seguridad

#### Ejemplo conceptual

```python
@router.get("/clients")
def list_clients(
    current_user: CurrentUser = Depends(require_permission("clients.view")),
    db: Session = Depends(get_db),
):
    query = db.query(Client)
    query = apply_client_scope(query, current_user)
    return query.all()
```

### 7.3 Filtros por alcance

#### Regla principal

Todo endpoint que devuelva datos de negocio debe pasar por una función de alcance.

Funciones recomendadas:

- `apply_client_scope(query, access_context)`
- `apply_order_scope(query, access_context)`
- `apply_invoice_scope(query, access_context)`
- `apply_delivery_scope(query, access_context)`

#### Estrategia de implementación

1. Resolver primero el `access_context` del usuario:

- permisos efectivos
- tipo de alcance
- clientes asignados
- equipos
- acceso a datos sensibles

2. Aplicar filtro por recurso:

- comercial: solo clientes asignados
- pedidos: por `client_id` asignado
- albaranes/facturas: por documentos derivados de clientes asignados o por permiso de finanzas

3. Filtrar campos sensibles si procede.

#### No confiar en el frontend

Aunque el frontend oculte botones y rutas:

- el backend debe devolver `403` si no hay permiso
- el backend debe devolver solo registros permitidos
- el backend no debe exponer importes o notas internas si el permiso sensible no existe

### 7.4 Acceso a datos sensibles

En algunos endpoints no bastará con filtrar filas; también habrá que filtrar columnas o secciones del payload.

Estrategias:

- usar esquemas de respuesta distintos por permiso
- o serializar campos sensibles solo si `access_context.allow_sensitive_data` es `True`

Ejemplos:

- importes pendientes
- cobros
- vencimientos
- notas internas administrativas

### 7.5 Auditoría y trazabilidad

No hace falta implementarlo en primera entrega, pero el diseño debe permitir:

- registrar quién crea usuarios
- registrar quién cambia roles
- registrar cambios en clientes asignados

## 8. Diseño frontend recomendado

### 8.1 Routing

Introducir `react-router` antes de ampliar módulos.

Estructura base recomendada:

- `/login`
- `/`
- `/dashboard`
- `/clients`
- `/clients/:clientId`
- `/orders`
- `/orders/:orderId`
- `/orders/:orderId/traceability`
- `/deliveries`
- `/invoices`
- `/products`
- `/incidents`
- `/admin/users`
- `/admin/roles`

Notas:

- muchas rutas pueden existir primero como placeholders protegidos
- no significa que todos los módulos estén implementados funcionalmente desde el día uno

### 8.2 Sesión y estado de autenticación

Recomendación:

- `AuthProvider` o store equivalente
- mantener en memoria:
  - usuario actual
  - roles
  - permisos efectivos
  - scopes efectivos
  - flags de datos sensibles

Estado mínimo:

- `isAuthenticated`
- `user`
- `permissions`
- `scopes`
- `isLoadingSession`

### 8.3 Rutas protegidas

Patrones recomendados:

- `RequireAuth`
- `RequirePermission`

Ejemplo conceptual:

```jsx
<Route
  path="/clients"
  element={
    <RequireAuth>
      <RequirePermission permission="clients.view">
        <ClientsPage />
      </RequirePermission>
    </RequireAuth>
  }
/>
```

### 8.4 Sidebar dinámico

La navegación lateral no debe estar hardcodeada con items visibles para todos.

Cada item del menú debe declararse con:

- `key`
- `label`
- `path`
- `requiredPermissions`
- `featureFlag` opcional

Ejemplo:

- `Clients` visible solo con `clients.view`
- `Admin` visible solo con `admin.view`

### 8.5 Visibilidad de acciones

Los botones también deben depender de permisos.

Ejemplos:

- `Nuevo cliente` requiere `clients.create`
- `Editar producto` requiere `products.update`
- `Ver importes` requiere `orders.view_amounts` o `invoices.view_amounts`

Recomendación:

- crear componentes helper tipo `Can` o hooks tipo `useCan(permission)`

### 8.6 UX por perfil

La limpieza visual debe venir de:

- menú con solo los módulos útiles
- dashboards más relevantes por perfil
- tablas sin columnas sensibles innecesarias
- CTAs adaptados al rol

No hacer:

- esconder solo con CSS
- mostrar elementos inactivos masivamente

Sí hacer:

- una navegación corta y relevante por perfil

## 9. Navegación recomendada por perfil

### 9.1 Dirección General

Menú inicial recomendado:

- Dashboard
- Clientes
- Pedidos
- Albaranes
- Facturas
- Incidencias
- Productos
- Administración

Más adelante:

- Finanzas
- Operaciones

### 9.2 Comercial

Menú inicial recomendado:

- Dashboard
- Clientes
- Pedidos
- Incidencias
- Productos

Opcional más adelante:

- Actividad comercial

No debería ver por defecto:

- administración
- cobros
- vencimientos globales
- configuraciones sensibles

### 9.3 Finanzas

Menú inicial recomendado:

- Dashboard
- Clientes
- Albaranes
- Facturas
- Incidencias

Más adelante:

- Cobros
- Vencimientos

Opcional:

- Pedidos en modo lectura si el negocio lo necesita

### 9.4 Admin

Menú inicial recomendado:

- Dashboard
- Administración
- Usuarios
- Roles y permisos

Según decisión operativa:

- acceso completo temporal al resto de módulos

Recomendación:

- no usar `admin` como sustituto de Dirección General

### 9.5 Operaciones

Reservado para futuro:

- Dashboard
- Pedidos
- Albaranes
- Incidencias
- Productos

## 10. Qué implementar primero

### 10.1 Primera entrega mínima robusta

Debe incluir:

1. Backend

- modelo de usuarios, roles, permisos y asignación de clientes
- seeds iniciales de roles y permisos
- `auth/me`
- dependencias de permiso
- alcance mínimo por clientes asignados

2. Frontend

- `react-router`
- login básico
- `AuthProvider`
- rutas protegidas
- sidebar dinámico
- adaptación del `Header` al usuario real

3. Integración

- proteger al menos:
  - dashboard
  - clientes
  - pedidos
  - albaranes
  - facturas
  - productos

Aunque algunas páginas sigan siendo placeholders.

### 10.2 Qué aplazar a segunda fase

- equipos completos
- jerarquías de supervisión avanzadas
- permisos por campo ultra granulares
- auditoría detallada de eventos
- SSO
- cobros y vencimientos si aún no existen como módulo real
- incidencias persistidas completas

## 11. Plan exacto del siguiente cambio implementable

El siguiente cambio implementable en código debería ser una primera base técnica, no la funcionalidad final completa.

### Bloque 1. Backend de seguridad mínimo

1. Crear modelos:

- `User`
- `Role`
- `Permission`
- `UserRole`
- `RolePermission`
- `ClientAssignment`

2. Crear migración Alembic inicial de seguridad.

3. Añadir seeds de:

- roles base
- permisos base
- usuario admin inicial

4. Crear capa de auth mínima:

- hashing de password
- `POST /auth/login`
- `GET /auth/me`

5. Crear dependencias:

- `get_current_user`
- `require_permission`
- `get_access_context`

6. Proteger primero endpoints de lectura:

- dashboard
- clients
- orders
- deliveries
- invoices
- products

### Bloque 2. Frontend de acceso mínimo

1. Introducir `react-router`.

2. Crear:

- `LoginPage`
- `AuthProvider`
- `RequireAuth`
- `RequirePermission`

3. Hacer sidebar dinámico.

4. Reemplazar usuario fijo del header por sesión real.

5. Mantener como placeholder protegido los módulos aún no desarrollados.

### Bloque 3. Alcance comercial mínimo

1. Aplicar cartera por `client_assignments`.

2. Filtrar:

- `/clients`
- `/orders`
- `/deliveries`
- `/invoices`
- endpoints de dashboard basados en esos recursos

3. Permitir a Dirección General y Finanzas alcance global.

## 12. Riesgos de implementación

### Riesgo 1

Intentar resolver permisos y scopes solo en frontend.

Mitigación:

- toda comprobación real debe vivir en backend

### Riesgo 2

Diseñar permisos demasiado detallados desde el día uno.

Mitigación:

- empezar con catálogo pequeño y estable

### Riesgo 3

Intentar meter equipos, jerarquías y aprobaciones en primera fase.

Mitigación:

- primero usuarios, roles, permisos y cartera simple

### Riesgo 4

Acoplar demasiado seguridad a los modelos actuales sin capa de acceso.

Mitigación:

- crear helpers reutilizables de permisos y alcance

## 13. Recomendación final

La base correcta para este ERP es:

- autenticación centralizada
- RBAC con permisos finos
- alcance de datos por cartera/equipo
- enforcement real en backend
- routing y navegación por permisos en frontend

No conviene empezar construyendo pantallas nuevas de negocio sin esta base, porque luego habrá que rehacerlas para soportar perfiles, scopes y datos sensibles.
