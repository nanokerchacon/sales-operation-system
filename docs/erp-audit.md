# ERP Audit

Fecha de auditoria: 2026-03-16

## Objetivo de esta auditoria

Evaluar el estado real del proyecto para preparar una base mantenible hacia un ERP profesional con modulos de dashboard, clientes, pedidos, albaranes, facturas, incidencias y productos, incluyendo control por perfiles de usuario.

Este documento se basa solo en el estado actual del repositorio. No asume funcionalidades que no existan en codigo.

## Resumen ejecutivo

El proyecto ya tiene una base funcional parcial orientada a operaciones comerciales y facturacion documental:

- Backend en FastAPI + SQLAlchemy + PostgreSQL.
- Frontend en React + Vite + Tailwind.
- Modelo de datos base para clientes, productos, pedidos, lineas de pedido, albaranes y facturas.
- Dashboard operativo bastante avanzado para control de pedidos, entregas y cierre documental.
- Vista de trazabilidad de pedido con detalle de lineas, albaranes y facturas.
- Scripts y soporte de importacion para pedidos legacy.

El proyecto todavia no es un ERP generalista. Hoy es mas bien una aplicacion vertical de seguimiento operativo de pedidos/facturacion con un frontend limitado a dos pantallas reales.

Las principales carencias para evolucionar a ERP son:

- No existe autenticacion ni autorizacion.
- No hay modelo de usuarios, roles, permisos ni asignacion de cartera.
- No existen modulos funcionales completos para clientes, pedidos, albaranes, facturas, productos o incidencias en frontend.
- No existe entidad de incidencias.
- La ficha 360 de cliente no existe.
- Hay deuda tecnica relevante en configuracion, persistencia, arquitectura de rutas y consistencia de APIs.

## 1. Stack usado

### Backend

- Framework API: FastAPI
- ORM: SQLAlchemy 2.x
- Base de datos: PostgreSQL 16 via Docker Compose
- Migraciones: Alembic
- Driver: psycopg 3

Observaciones:

- `backend/requirements.txt` no incluye dependencias esenciales para arrancar la API, como `fastapi` y `uvicorn`.
- La conexion a base de datos esta hardcodeada en codigo y no se carga desde variables de entorno.
- El backend usa tanto Alembic como `Base.metadata.create_all()` al arrancar, lo que mezcla dos estrategias de gestion de esquema.

### Frontend

- Framework UI: React 18
- Bundler/dev server: Vite 5
- Estilos: Tailwind CSS 3
- Graficos: Recharts

Observaciones:

- No hay `react-router`.
- El enrutado es manual usando `window.location`, `history.pushState` y escucha de `popstate`.

## 2. Estructura actual del repositorio

### Directorios principales

- `backend/`: API, modelos, esquemas, servicios, migraciones y scripts de importacion/limpieza.
- `frontend/`: aplicacion React, componentes visuales, servicios API y build generado.
- `reconstruction_lab/`: datos historicos, notas y scripts auxiliares de reconciliacion documental.
- `docs/`: documentacion tecnica. Este informe se crea aqui.

### Lectura general

- El repo mezcla codigo de aplicacion con datos historicos y artefactos operativos.
- `frontend/dist` esta versionado en el repo.
- `reconstruction_lab` parece ser un area de trabajo para reconstruccion de historico, no un modulo limpio del producto.

## 3. Backend: estado real

### 3.1 Punto de entrada y configuracion

Punto de entrada:

- `backend/app/main.py`

Comportamiento actual:

- Crea una instancia simple de `FastAPI`.
- Configura CORS solo para `localhost:5173` y `127.0.0.1:5173`.
- En `startup` ejecuta `Base.metadata.create_all(bind=engine)`.
- Registra routers para clientes, dashboard, deliveries, invoices, operations, status, risk, orders y products.

Configuracion de base de datos:

- `backend/app/database/session.py`
- URL fija: `postgresql+psycopg://postgres:postgres@localhost:5432/sales_operation_system`

Conclusiones:

- No existe capa de settings centralizada.
- No hay separacion por entornos.
- La inicializacion de tablas en arranque puede desalinearse con Alembic.

### 3.2 Modelos de base de datos

Modelos detectados:

- `Client`
- `Product`
- `Order`
- `OrderItem`
- `DeliveryNote`
- `DeliveryItem`
- `Invoice`
- `InvoiceItem`

#### Client

Campos principales:

- `id`
- `name`
- `legacy_code`
- `tax_id`
- `address`
- `phone`
- `email`
- `created_at`

Faltan para ERP:

- comercial asignado
- estado del cliente
- condiciones comerciales
- condiciones de pago
- riesgo financiero
- observaciones internas
- contactos
- direccion fiscal vs envio

#### Product

Campos principales:

- `id`
- `name`
- `sku`
- `legacy_code`
- `description`
- `unit_price`
- `created_at`

Faltan para ERP:

- familia/categoria
- unidad de medida
- coste
- impuestos
- estado activo/inactivo
- stock si se quiere evolucionar a operaciones/inventario

#### Order

Campos principales:

- `client_id`
- `order_date`
- `series`
- `order_number`
- `legacy_client_code`
- `client_name_snapshot`
- `notes`
- `source`
- `subtotal`
- `tax_amount`
- `total_amount`
- `status`

Observaciones:

- Tiene soporte mixto ERP/legacy.
- `status` es string libre; no hay enum ni tabla de estados.
- No hay comercial asignado.
- No hay referencia a usuario creador o responsable.

#### OrderItem

Campos principales:

- `order_id`
- `product_id` nullable
- `line_number`
- `line_type`
- `legacy_article_code`
- `description`
- `quantity`
- `unit_price`
- `line_amount`

Observaciones:

- Se toleran lineas sin `product_id`, util para legacy.
- No hay impuestos por linea, descuentos, unidad, coste, ni trazabilidad comercial.

#### DeliveryNote / DeliveryItem

Campos principales:

- `DeliveryNote.order_id`
- `delivery_date`
- `DeliveryItem.order_item_id`
- `quantity`

Observaciones:

- Modelo suficiente para registrar cantidades entregadas.
- No hay numero de albaran real, serie, estado, transportista, direccion de entrega, firma o documento adjunto.
- El frontend genera un identificador visual simple a partir de `id`.

#### Invoice / InvoiceItem

Campos principales:

- `Invoice.order_id`
- `source_folder`
- `invoice_type`
- `invoice_status`
- `invoice_date`
- `InvoiceItem.order_item_id`
- `quantity`
- `unit_price`

Observaciones:

- Se modela la factura con foco en control documental.
- `invoice_status` distingue aceptada, pendiente de aceptacion y revision rectificativa.
- No hay numero de factura fiscal real, serie, vencimientos, cobros, base imponible, IVA, total, moneda o enlace formal a cliente.

### 3.3 Migraciones y evolucion del esquema

Migraciones detectadas:

- `20260313_01_add_legacy_order_support.py`
- `20260313_02_add_invoice_document_status.py`

Lo que indican:

- El proyecto ya tuvo una evolucion orientada a importar pedidos legacy.
- Se ha incorporado semantica documental en facturas.
- No hay migracion inicial clara del esquema base en el repo; el arranque depende de `create_all`.

Riesgo:

- En entornos nuevos puede haber diferencias entre una base generada por `create_all` y una base generada por migraciones si el historial no se mantiene con disciplina.

### 3.4 Endpoints existentes

#### Base

- `GET /`
- `GET /db-test`

#### Clientes

- `POST /clients`
- `GET /clients`

#### Productos

- `POST /products`
- `GET /products`

#### Pedidos

- `POST /orders`
- `GET /orders`
- `GET /orders/{order_id}/traceability`

#### Albaranes

- `POST /deliveries`
- `GET /deliveries`

#### Facturas

- `POST /invoices`
- `GET /invoices`

#### Dashboard operativo

- `GET /dashboard/operations`
- `GET /dashboard/order-status-summary`
- `GET /dashboard/orders-with-incidents`
- `GET /dashboard/risk-orders`
- `GET /dashboard/pending-invoices`
- `GET /dashboard/pending-revenue`
- `GET /dashboard/revenue-at-risk`
- `GET /dashboard/work-queue`
- `GET /dashboard/clients-with-incidents`
- `GET /dashboard/client-risk`
- `GET /dashboard/aging-invoices`

#### Estado operativo auxiliar

- `GET /operations/status`
- `GET /status/summary`

### 3.5 Logica de negocio ya implementada

Piezas relevantes:

- Validacion de cantidades entregadas para no exceder lo pedido.
- Validacion de cantidades facturadas para no exceder lo entregado.
- Calculo de estados operativos por pedido.
- Dashboard agregado de incidencias y facturacion pendiente.
- Trazabilidad de pedido con lineas, albaranes y facturas.
- Soporte de importacion legacy y normalizacion de estados de pedidos.
- Inferencia de metadatos documentales de factura desde carpetas como `FACE`, `N 2026`, `IC 2026`, etc.

Conclusion:

- Hay una base solida en la vertical de operaciones/facturacion documental.
- La logica esta orientada a cantidades y cierre documental, no a un ERP multirol completo.

### 3.6 Sistema actual de autenticacion

No existe autenticacion.

No se detectan:

- usuarios
- login
- sesiones
- JWT
- OAuth
- refresh tokens
- permisos
- middleware de seguridad por usuario

Consecuencia:

- Todo endpoint es publico para quien alcance la API.
- No existe separacion entre Direccion, Comercial, Finanzas u otros perfiles.

## 4. Frontend: estado real

### 4.1 Sistema de rutas

No existe router formal.

Rutas reales implementadas:

- `/` -> dashboard
- `/orders/:id/traceability` -> trazabilidad de pedido

Implementacion actual:

- `frontend/src/App.jsx`
- matching manual mediante regex
- navegacion manual con `history.pushState`

Implicaciones:

- Escala mal a un ERP con muchos modulos, subrutas, proteccion por permisos, layouts anidados y breadcrumbs.
- Complica carga diferida, guards de acceso y navegacion consistente.

### 4.2 Paginas reales

Paginas implementadas:

- `DashboardPage`
- `OrderTraceabilityPage`

No existen paginas reales para:

- clientes
- pedidos como modulo de listado/edicion
- albaranes
- facturas
- incidencias
- productos
- administracion
- operaciones como modulo independiente

### 4.3 Layout y componentes

Layout base:

- `AppLayout`
- `Sidebar`
- `Header`

Navegacion lateral:

- El sidebar ya muestra los modulos esperados a nivel visual.
- Excepto `Dashboard`, el resto tienen `href: null`.

Conclusiones:

- Visualmente ya se intuye la estructura ERP.
- Funcionalmente todavia es un shell parcial.

### 4.4 Servicios y consumo API

Servicios detectados:

- `frontend/src/services/api.js`
- `frontend/src/services/ordersApi.js`

Patron actual:

- `fetch` nativo
- sin capa de auth
- sin interceptores
- sin control centralizado de errores por permisos
- sin cache cliente

### 4.5 Estado de autenticacion y usuario en frontend

No existe.

No se detectan:

- contexto de usuario autenticado
- control de sesion
- proteccion de rutas
- render condicionado por permisos

Ademas, el `Header` muestra un usuario fijo:

- `Alvaro Chacon`
- `Soporte IT`

Eso es solo presentacional; no esta conectado a backend ni a una sesion real.

## 5. Inconsistencias detectadas entre frontend y backend

### Inconsistencias funcionales

1. El frontend anuncia modulos ERP que no existen todavia como pantallas reales.

- Sidebar muestra Pedidos, Albaranes, Facturas, Incidencias, Clientes y Productos.
- Pero solo funcionan Dashboard y trazabilidad de pedido.

2. La necesidad funcional de ficha de cliente 360 no esta soportada.

- Backend no expone endpoint de detalle de cliente con pedidos, albaranes, facturas e incidencias.
- Frontend tampoco tiene pagina ni componentes para ello.

3. El concepto de incidencias existe en dashboard como agregacion derivada, pero no como modulo real.

- No hay tabla `incidents` o similar.
- "Incidencia" hoy significa desviacion operativa calculada, no expediente de incidencia comercial/administrativa persistido.

### Inconsistencias tecnicas

1. `frontend/README.md` indica `VITE_API_BASE_URL=http://127.0.0.1:8001`, pero el frontend usa por defecto `http://127.0.0.1:8000`.

2. `README.md` raiz dice que el proyecto es solo scaffold inicial, pero el repo contiene bastante logica real en backend y frontend.

3. El repo contiene `frontend/dist` versionado, lo que suele desalinear codigo fuente y artefactos generados.

## 6. Carencias para implementar roles y permisos

### Lo que falta en datos

No existen tablas o modelos para:

- usuarios
- roles
- permisos
- relacion usuario-rol
- relacion rol-permiso
- asignacion comercial-cliente
- ambito de acceso por cartera

### Lo que falta en backend

- autenticacion
- autorizacion por endpoint
- autorizacion por recurso
- dependencias tipo `get_current_user`
- middleware o dependencias de permisos
- filtros por ambito de datos

### Lo que falta en frontend

- login
- sesion
- contexto de usuario
- rutas protegidas
- menu dinamico por permisos
- ocultacion de acciones segun perfil
- filtrado de datos por alcance del usuario

### Lo que falta en dominio

Para cumplir con el objetivo descrito hacen falta al menos estas reglas:

- Direccion General: acceso total
- Comerciales: acceso restringido a su cartera, pedidos, clientes, incidencias comerciales y productos
- Finanzas: acceso a clientes, albaranes, facturas, cobros, vencimientos e incidencias administrativas

Nada de eso existe hoy a nivel de codigo o datos.

## 7. Riesgos tecnicos

### Riesgo alto

1. Ausencia total de autenticacion y autorizacion.

2. Hardcode de configuracion critica.

- URL de base de datos fija.
- CORS fijo a dev local.

3. Mezcla de `create_all` con Alembic.

Puede provocar deriva de esquema y errores dificiles de reproducir entre entornos.

4. Frontend sin router formal.

Escala mal para un ERP con muchos modulos, perfiles y paginas de detalle.

5. Modelo de incidencias inexistente.

El negocio pide incidencias comerciales y administrativas, pero hoy solo hay estados derivados.

### Riesgo medio

6. Repositorio con datos historicos y build generada mezclados con codigo de producto.

7. Sin tests automáticos.

No se detecta suite de tests backend ni frontend.

8. Uso intensivo de consultas por pedido en loops.

Los servicios de dashboard hacen muchas agregaciones por pedido y por linea, lo que puede degradar rendimiento al crecer el volumen.

9. Strings libres para estados.

Puede romper reglas de negocio, filtros y permisos al no existir catalogos controlados.

## 8. Deuda tecnica

1. Configuracion por entorno inexistente.

2. Falta de dependencia compartida para sesion de DB; los routers instancian `SessionLocal()` manualmente.

3. Endpoints duplicados o semanticamente solapados:

- `risk-orders` y `orders-with-incidents`
- `client-risk` y `clients-with-incidents`
- `operations/status` y `status/summary`

4. Documentacion raiz desactualizada.

5. Dependencias Python incompletas en `backend/requirements.txt`.

6. Enrutado frontend artesanal.

7. Ausencia de tipado de dominio mas estricto para estados y permisos.

8. Fuerte acoplamiento entre logica de dashboard y estructura actual de pedidos/albaranes/facturas.

## 9. Piezas que conviene refactorizar antes de seguir

Orden recomendado de refactor tecnico previo:

### 1. Configuracion y arranque

Refactorizar primero:

- settings por entorno
- carga de `DATABASE_URL`, puertos, CORS y API base URL desde env
- eliminar `create_all` del arranque y confiar en migraciones

### 2. Sistema de rutas frontend

Introducir `react-router` antes de ampliar modulos.

Motivo:

- es la base para permisos, layouts por modulo, login, redirecciones y detalle de entidades

### 3. Capa de acceso a datos y dependencias backend

Unificar:

- dependencia `get_db`
- patrones de manejo de sesion
- gestion de errores de negocio

### 4. Catalogos y enums de dominio

Normalizar:

- estados de pedido
- estados documentales
- tipos de incidencia
- roles del sistema

### 5. Separacion entre incidencias derivadas y incidencias persistidas

El ERP necesitara distinguir claramente:

- incidencia calculada operativa
- incidencia comercial registrada por usuario
- incidencia administrativa/financiera registrada por usuario

## 10. Propuesta de arquitectura para roles y permisos

### Principios

1. Autenticacion centralizada.

2. Autorizacion por dos niveles:

- nivel modulo/accion
- nivel dato o ambito de negocio

3. Roles de alto nivel para operativa inicial.

4. Permisos granulares para evolucion futura.

### Modelo recomendado

Entidades nuevas:

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`
- `sales_portfolios` o `client_assignments`

Campos minimos de `users`:

- `id`
- `email`
- `password_hash`
- `full_name`
- `is_active`
- `default_role`
- `created_at`

Campos minimos de `roles`:

- `id`
- `code`
- `name`

Campos minimos de `permissions`:

- `id`
- `code`
- `module`
- `action`

Ejemplos de permisos:

- `dashboard.view`
- `clients.view`
- `clients.edit`
- `orders.view`
- `orders.edit`
- `deliveries.view`
- `invoices.view`
- `incidents.view`
- `incidents.create`
- `products.view`
- `products.edit`
- `admin.manage_users`

### Ambito por datos

Ademas de permisos globales, hace falta un ambito de acceso:

- `all`
- `assigned_clients`
- `assigned_orders`
- `finance_only`

Ejemplo:

- Direccion General: todos los permisos + ambito `all`
- Comercial: permisos de lectura/escritura comercial + ambito `assigned_clients`
- Finanzas: permisos financieros + acceso amplio a clientes y documentos

### En backend

Patron recomendado:

- autenticacion con JWT o sesion server-side
- dependencia `get_current_user`
- dependencia `require_permission("orders.view")`
- filtros de consulta por ambito de usuario

Ejemplo conceptual:

- un comercial no deberia poder consultar `/clients/{id}` si ese cliente no pertenece a su cartera
- finanzas si deberia poder ver facturas y vencimientos aunque no sea comercial del cliente

### En frontend

Necesario:

- contexto de autenticacion
- carga de perfil y permisos al iniciar sesion
- rutas protegidas
- menu lateral filtrado por permisos
- componentes de accion condicionados por permiso

## 11. Propuesta funcional para cliente 360

La ficha de cliente deberia apoyarse en un endpoint agregado y no en muchas llamadas inconexas.

### Endpoint recomendado

- `GET /clients/{client_id}`
- `GET /clients/{client_id}/timeline`
- o una variante unica tipo `GET /clients/{client_id}/erp-summary`

### Datos minimos de la ficha

- datos maestros del cliente
- pedidos
- albaranes
- facturas
- incidencias comerciales
- incidencias administrativas
- resumen de importes pendientes
- ultimo movimiento

### Situacion actual

- No existe ningun endpoint de detalle de cliente.
- No existe el modelo de incidencias.
- No existe la pagina de cliente en frontend.

## 12. Orden recomendado de implementacion por fases

### Fase 0. Saneamiento tecnico minimo

- introducir settings por entorno
- corregir dependencias backend
- definir estrategia unica de schema con Alembic
- introducir `react-router`
- actualizar documentacion basica

### Fase 1. Seguridad y perfiles

- crear modelo de usuarios, roles y permisos
- implementar autenticacion
- proteger backend por permisos
- montar login y contexto de sesion en frontend
- filtrar menu y rutas por perfil

### Fase 2. Maestro de clientes y cartera comercial

- ampliar modelo de cliente
- crear asignacion de clientes a comerciales
- construir listado de clientes
- construir ficha cliente 360 sin incidencias persistidas aun

### Fase 3. Modulos base ERP visibles

- pedidos: listado, detalle, filtros, estados
- albaranes: listado, detalle, relacion con pedido
- facturas: listado, detalle, estado documental
- productos: listado y mantenimiento

### Fase 4. Incidencias reales

- crear entidad `incidents`
- tipificar incidencias comerciales y administrativas
- enlazar incidencia con cliente, pedido, albaran y/o factura
- incorporar vistas por perfil y workflow basico

### Fase 5. Finanzas

- vencimientos
- cobros
- saldo cliente
- aging financiero real, no solo documental

### Fase 6. Operaciones y administracion avanzada

- perfil Operaciones
- perfil Administrador
- auditoria de acciones
- configuracion y catalogos

## 13. Checklist accionable de siguientes pasos

### Inmediatos

- [ ] Crear un modulo de configuracion backend por variables de entorno
- [ ] Eliminar `create_all` del arranque y dejar Alembic como unica fuente de verdad del esquema
- [ ] Completar `backend/requirements.txt` con dependencias reales de ejecucion
- [ ] Introducir `react-router` en frontend
- [ ] Definir mapa inicial de roles y permisos

### Seguridad

- [ ] Crear tablas `users`, `roles`, `permissions`, `user_roles`, `role_permissions`
- [ ] Implementar login y sesion/JWT
- [ ] Proteger endpoints existentes con permisos
- [ ] Definir filtro por cartera comercial

### Dominio ERP

- [ ] Diseñar entidad persistente de incidencias
- [ ] Diseñar endpoint de ficha cliente 360
- [ ] Ampliar entidad cliente con datos comerciales y financieros minimos
- [ ] Definir numeracion real para pedidos, albaranes y facturas

### Frontend

- [ ] Crear rutas reales para Clientes, Pedidos, Albaranes, Facturas, Incidencias y Productos
- [ ] Sustituir usuario fijo del header por usuario autenticado real
- [ ] Filtrar menu lateral por permisos
- [ ] Implementar pantallas de listado antes que formularios complejos

### Calidad

- [ ] Añadir tests backend para reglas de cantidades y permisos
- [ ] Añadir tests frontend para rutas protegidas y visibilidad por perfil
- [ ] Revisar rendimiento de endpoints de dashboard con consultas agregadas mas eficientes

## 14. Que hay hecho

- Base backend funcional con entidades nucleares de operaciones.
- Creacion y listado de clientes, productos, pedidos, albaranes y facturas.
- Reglas de validacion de entrega y facturacion por cantidad.
- Dashboard operativo con varias vistas agregadas.
- Trazabilidad de pedido con lineas, albaranes y facturas.
- Soporte de datos legacy y reconciliacion documental.
- Shell visual de frontend con sidebar y cabecera.

## 15. Que falta

- autenticacion
- roles y permisos
- cartera comercial
- modulos ERP navegables completos
- ficha cliente 360
- incidencias persistidas
- vencimientos y cobros
- administracion de usuarios
- tests
- configuracion profesional por entorno

## 16. Siguiente cambio real recomendado

El siguiente cambio real a implementar deberia ser:

### Implementar la base de seguridad y navegacion sobre la que se apoyara todo lo demas

Concretamente:

1. Backend:

- modelo `users`, `roles`, `permissions`
- autenticacion
- dependencias de autorizacion

2. Frontend:

- `react-router`
- login
- contexto de sesion
- menu y rutas protegidas por perfil

Razon:

Sin esa base, cualquier modulo nuevo de clientes, facturas o incidencias se construira dos veces:

- una sin permisos
- otra despues para adaptar perfiles, cartera y restricciones

Eso generaria retrabajo y acoplamiento innecesario.

## 17. Conclusión

El proyecto ya tiene una base real y util, especialmente en la parte de operaciones, pedidos y control documental. No parte de cero.

Sin embargo, todavia no tiene la arquitectura minima necesaria para convertirse en un ERP profesional multiusuario con perfiles. La prioridad correcta no es añadir pantallas sueltas, sino asegurar primero:

- seguridad
- rutas escalables
- modelo de permisos
- claridad del dominio

Sobre esa base, la siguiente expansion natural es la ficha cliente 360 y los modulos navegables de clientes, pedidos, albaranes, facturas, incidencias y productos.
