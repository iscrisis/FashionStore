# FashionStore

Plataforma e-commerce propia (no basada en Shopify/WooCommerce/Magento/PrestaShop).

## Estructura del repositorio

```
fashionstore/
├── backend/            API REST (FastAPI + PostgreSQL) — ver backend/README.md
├── frontend/
│   └── web/            Aplicación web (Angular) — ver frontend/web/README.md
├── docker-compose.yml  Orquesta backend + PostgreSQL + frontend para desarrollo local
├── .env.example        Variables usadas por docker-compose.yml (copiar a .env)
└── .gitignore
```

El backend es la única API central: tanto la web (Angular) como, más adelante, la app móvil
(Flutter) consumirán exactamente el mismo backend — no se duplica lógica de negocio por cliente.

## Ejecutar todo el stack con Docker

```bash
cp .env.example .env
cp backend/.env.example backend/.env
docker compose up -d --build
```

- Web: http://localhost:4200
- API (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

Detener:

```bash
docker compose down
```

## Desarrollo de cada proyecto por separado

Ver las instrucciones específicas en [backend/README.md](backend/README.md) y
[frontend/web/README.md](frontend/web/README.md).
