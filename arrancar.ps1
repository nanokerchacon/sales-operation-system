# Ir a la carpeta del proyecto
cd C:\Proyectos\sales-operation-system

# Levantar base de datos
docker compose up -d

# Abrir backend
Start-Process powershell -ArgumentList "cd C:\Proyectos\sales-operation-system\backend; python -m uvicorn app.main:app --reload"

# Abrir frontend
Start-Process powershell -ArgumentList "cd C:\Proyectos\sales-operation-system\frontend; npm run dev"