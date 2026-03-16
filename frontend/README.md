# Nanoker ERP Frontend

Frontend de la aplicación ERP construido con React, Vite y Tailwind CSS.

## Estado actual

Implementado en este frontend:

- sesión real con auth backend
- rutas protegidas y sidebar dinámico
- dashboard
- módulo Clientes fase 1
- módulo Pedidos con listado, detalle y enlace a trazabilidad

## Instalación

```bash
npm install
```

## Ejecución en desarrollo

```bash
npm run dev
```

La aplicación queda disponible en `http://127.0.0.1:5173`.

## Build de producción

```bash
npm run build
```

## Configuración del backend

La URL base del backend se configura mediante:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Puedes crear un archivo `.env` dentro de `frontend/` partiendo de `.env.example`.
