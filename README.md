# Sales Operation System

ERP operativo en construcción sobre FastAPI, SQLAlchemy, PostgreSQL y React.

## Estado actual

Implementado en el repo:

- autenticación real con `POST /auth/login` y `GET /auth/me`
- seed de seguridad saneado con `APP_ENV`
- módulo Clientes fase 1
- módulo Pedidos con listado, detalle y enlace a trazabilidad
- dashboard y trazabilidad operativa existente

## Arranque rápido

### Backend

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:APP_ENV='development'
python scripts/seed_security.py
uvicorn app.main:app --reload
```

API local:

- `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend local:

- `http://127.0.0.1:5173`

Por defecto el frontend apunta a `http://127.0.0.1:8000` mediante `VITE_API_BASE_URL`.

## Base de datos local

Desde la raíz del repo:

```powershell
docker compose up -d db
```

## Credenciales locales de prueba

Solo en entorno local/development:

- `direccion@local` / `Local123!`
- `comercial@local` / `Local123!`
- `finanzas@local` / `Local123!`
- `admin@local` / `Local123!`

## Documentación principal

- [Backend](backend/README.md)
- [Frontend](frontend/README.md)
- [ERP Audit](docs/erp-audit.md)
- [Access Control Design](docs/access-control-design.md)
- [Permission Matrix](docs/permission-matrix.md)
- [Security Phase 1](docs/security-phase1.md)
- [Clients Module Phase 1](docs/clients-module-phase1.md)
