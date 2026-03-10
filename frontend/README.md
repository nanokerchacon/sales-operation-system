# Nanoker ERP Frontend

Frontend inicial del dashboard de `Nanoker ERP - Sales Operations`, construido con React, Vite y Tailwind CSS.

## Instalacion

```bash
npm install
```

## Ejecucion en desarrollo

```bash
npm run dev
```

La aplicacion quedara disponible en `http://127.0.0.1:5173`.

## Build de produccion

```bash
npm run build
```

## Configuracion del backend

La URL base del backend se configura mediante la variable:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8001
```

Puedes crear un archivo `.env` dentro de `frontend/` partiendo de `.env.example`.
