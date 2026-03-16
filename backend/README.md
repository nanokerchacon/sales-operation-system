# Backend

Backend API de `sales-operation-system`.

## Versiones fijadas para auth

- `fastapi==0.116.1`
- `uvicorn==0.35.0`
- `passlib[bcrypt]==1.7.4`
- `bcrypt==4.0.1`

Motivo del pinning de auth:

- `passlib 1.7.4` sigue siendo la version usada por el proyecto para `CryptContext`.
- `passlib` recomienda instalar `bcrypt` mediante el extra `passlib[bcrypt]`.
- `bcrypt 4.1.0` fue retirado en PyPI por incompatibilidad con supuestos internos de `passlib`.
- con `bcrypt >= 4.1.x` sigue apareciendo el warning `error reading bcrypt version` porque `passlib 1.7.4` intenta leer `bcrypt.__about__.__version__`.
- `bcrypt 4.0.1` es el pin minimo seguro y estable para este backend sin cambiar el contrato actual de autenticacion.

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
- `AUTO_CREATE_SCHEMA=true`
- `AUTH_TOKEN_EXPIRE_HOURS=24`

Si necesitas sobreescribirlas:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/sales_operation_system"
$env:AUTO_CREATE_SCHEMA="true"
$env:AUTH_TOKEN_EXPIRE_HOURS="24"
```

## Seed de seguridad

Con el entorno virtual activado, desde `backend`:

```powershell
python scripts/seed_security.py
```

El seed es idempotente:

- crea roles y permisos si faltan
- crea usuarios locales si no existen
- asigna rol principal y relaciones faltantes
- asigna al usuario comercial los tres primeros clientes existentes, si los hay

## Arranque del backend

Con el entorno virtual activado, desde `backend`:

```powershell
uvicorn app.main:app --reload
```

La API queda disponible en:

- `http://127.0.0.1:8000`
- docs Swagger: `http://127.0.0.1:8000/docs`

## Credenciales locales de prueba

- `direccion@local` / `Local123!`
- `comercial@local` / `Local123!`
- `finanzas@local` / `Local123!`
- `admin@local` / `Local123!`

## Comprobacion manual minima

1. Arrancar la base de datos.
2. Instalar dependencias.
3. Ejecutar `python scripts/seed_security.py`.
4. Arrancar `uvicorn app.main:app --reload`.
5. Probar `POST /auth/login` con `admin@local` / `Local123!`.
6. Reutilizar el bearer token en `GET /auth/me`.

## Arranque limpio exacto

Desde la raiz del repo:

```powershell
docker compose up -d db
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/seed_security.py
uvicorn app.main:app --reload
```
