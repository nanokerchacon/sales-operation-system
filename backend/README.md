# Backend

Backend API de `sales-operation-system`.

## Estado actual

Implementado en este backend:

- autenticación real con `POST /auth/login` y `GET /auth/me`
- seed de seguridad saneado con `APP_ENV`
- módulo Clientes fase 1
- módulo Pedidos con listado, detalle y trazabilidad existente

## Versiones fijadas para auth y runtime

- `fastapi==0.116.1`
- `uvicorn==0.35.0`
- `passlib[bcrypt]==1.7.4`
- `bcrypt==4.0.1`
- `psycopg[binary]==3.3.3`

Motivo del pinning de auth:

- `passlib 1.7.4` sigue siendo la version usada por el proyecto para `CryptContext`.
- `passlib` recomienda instalar `bcrypt` mediante el extra `passlib[bcrypt]`.
- `bcrypt 4.1.0` fue retirado en PyPI por incompatibilidad con supuestos internos de `passlib`.
- con `bcrypt >= 4.1.x` sigue apareciendo el warning `error reading bcrypt version` porque `passlib 1.7.4` intenta leer `bcrypt.__about__.__version__`.
- `bcrypt 4.0.1` es el pin minimo seguro y estable para este backend sin cambiar el contrato actual de autenticacion.

Motivo del pinning de PostgreSQL:

- el proyecto usa el dialecto `postgresql+psycopg`.
- `psycopg[binary]` deja una sola dependencia estable y evita mezclar `psycopg` con `psycopg-binary` por separado.

## Instalacion limpia

PowerShell, desde `backend`:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Base de datos local

Desde la raiz del repositorio:

```powershell
docker compose up -d db
```

Variables usadas por defecto:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/sales_operation_system`
- `APP_ENV=development`
- `AUTO_CREATE_SCHEMA=true`
- `AUTH_TOKEN_EXPIRE_HOURS=24`

Si necesitas sobreescribirlas:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/sales_operation_system"
$env:APP_ENV="development"
$env:AUTO_CREATE_SCHEMA="true"
$env:AUTH_TOKEN_EXPIRE_HOURS="24"
```

## Seed de seguridad

Con el entorno virtual activado, desde `backend`:

```powershell
python scripts/seed_security.py
```

Comportamiento del seed:

- siempre crea roles y permisos faltantes de forma idempotente
- solo crea o resetea usuarios de prueba `@local` cuando `APP_ENV` es `development`, `dev` o `local`
- fuera de esos entornos no toca usuarios existentes y solo informa que los usuarios locales de prueba fueron omitidos
- no imprime contraseñas en claro en consola

## Arranque del backend

Con el entorno virtual activado, desde `backend`:

```powershell
uvicorn app.main:app --reload
```

La API queda disponible en:

- `http://127.0.0.1:8000`
- docs Swagger: `http://127.0.0.1:8000/docs`

## Credenciales locales de prueba

Solo para entorno local/development:

- `direccion@local` / `Local123!`
- `comercial@local` / `Local123!`
- `finanzas@local` / `Local123!`
- `admin@local` / `Local123!`

## Comprobacion manual minima

1. Arrancar la base de datos.
2. Instalar dependencias.
3. Ejecutar `python scripts/seed_security.py` con `APP_ENV=development`.
4. Arrancar `uvicorn app.main:app --reload`.
5. Probar `POST /auth/login` con `admin@local` / `Local123!`.
6. Probar `GET /orders` y `GET /orders/{order_id}`.
7. Reutilizar el bearer token en `GET /auth/me`.

## Arranque limpio exacto

Desde la raiz del repo:

```powershell
docker compose up -d db
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:APP_ENV='development'
python scripts/seed_security.py
uvicorn app.main:app --reload
```
