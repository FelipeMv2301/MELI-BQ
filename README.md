# MELI-BQ

Integración Mercado Libre para bioquimica.cl: sync de catálogo (stock/precio seleccionado) y
facturación de ventas en SAP. Ver `backlog_proyecto/plan-integracion-mercadolibre.md`.

## Desarrollo local

```powershell
.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

Tailwind (CLI standalone, sin Node/npm):
```powershell
.\tailwindcss.exe -i static/css/tailwind-src.css -o static/css/app.css --minify
```
