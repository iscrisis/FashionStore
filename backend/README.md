# FashionStore — Backend

API REST central del sistema, construida con **FastAPI** + **PostgreSQL**. Es consumida por el
frontend web en Angular y, en una etapa posterior, por la aplicación móvil en Flutter — ambos
clientes comparten exactamente el mismo backend, no se duplica lógica ni se crean APIs separadas.

Esta es la **base técnica** del proyecto: infraestructura, configuración y arquitectura. Los
casos de uso de negocio (usuarios, productos, sucursales, reservas, pagos, IA, realidad
aumentada, etc.) se implementarán en etapas posteriores siguiendo PUDS y el modelo UML del
dominio.

## Tecnologías

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy 2.x
- PostgreSQL (driver `psycopg` v3, binario)
- Alembic (migraciones)
- Pydantic Settings (configuración)
- Pytest + httpx (pruebas)
- Docker / Docker Compose

## Arquitectura

```
Angular Web  ─┐
              ├──▶  FastAPI  ──▶  PostgreSQL
Flutter Mobile┘
```

Capas internas de la API, de arriba hacia abajo:

```
routers      → endpoints REST
services     → reglas de negocio
repositories → acceso a datos
schemas      → contratos de entrada/salida (Pydantic)
models       → entidades persistentes (SQLAlchemy)
core         → configuración general
integrations → servicios externos (IA, pagos, etc.)
```

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py            # creación de la app FastAPI, CORS, routers
│   ├── core/
│   │   └── config.py       # configuración centralizada (pydantic-settings)
│   ├── db/
│   │   ├── base.py         # Base declarativa de SQLAlchemy
│   │   └── session.py      # engine, SessionLocal, dependency get_db
│   ├── models/              # modelos SQLAlchemy (vacío por ahora)
│   ├── schemas/              # esquemas Pydantic (vacío por ahora)
│   ├── repositories/         # acceso a datos (vacío por ahora)
│   ├── services/              # reglas de negocio (vacío por ahora)
│   ├── routers/
│   │   └── health.py        # GET /api/v1/health
│   ├── integrations/          # integraciones externas (vacío por ahora)
│   └── utils/                 # utilidades (vacío por ahora)
├── alembic/                  # migraciones de base de datos
├── tests/
│   └── test_health.py
├── alembic.ini
├── .env                      # variables de entorno locales (no versionado)
├── .env.example               # plantilla sin credenciales reales
├── Dockerfile
└── requirements.txt
```

`docker-compose.yml` vive en la raíz del repositorio (junto a `frontend/`), ya que orquesta
backend + PostgreSQL + frontend como un solo stack.

## Requisitos

- Python 3.12+ (si se ejecuta sin Docker)
- Docker y Docker Compose (recomendado)

## Configuración (.env)

1. Copia la plantilla:
   ```bash
   cp .env.example .env
   ```
2. Ajusta los valores, especialmente `DATABASE_URL`, `CORS_ORIGINS` y las credenciales de
   PostgreSQL. Nunca subas `.env` al repositorio (ya está en `.gitignore`).

Variables disponibles:

| Variable          | Descripción                                                        |
|-------------------|---------------------------------------------------------------------|
| `APP_NAME`        | Nombre de la aplicación                                             |
| `APP_ENV`         | Entorno (`development`, `production`, ...)                          |
| `API_V1_PREFIX`   | Prefijo de la API versionada (`/api/v1`)                            |
| `DATABASE_URL`    | Cadena de conexión a PostgreSQL (`postgresql+psycopg://...`)        |
| `BACKEND_PORT`    | Puerto donde escucha el backend                                     |
| `CORS_ORIGINS`    | Orígenes permitidos por CORS, separados por coma                    |
| `POSTGRES_DB`     | Nombre de la base de datos (usado por el servicio `db` en Compose)  |
| `POSTGRES_USER`   | Usuario de PostgreSQL (usado por el servicio `db` en Compose)       |
| `POSTGRES_PASSWORD`| Password de PostgreSQL (usado por el servicio `db` en Compose)     |

En producción/nube, estas variables se configuran en el proveedor de hosting/orquestación, no en
el código. `localhost` solo aplica al desarrollo local sin Docker.

## Ejecución con Docker (recomendado)

El `docker-compose.yml` está en la **raíz del repositorio** (no dentro de `backend/`), porque
orquesta el stack completo. Ejecutar desde ahí:

```bash
cd ..   # si estás parado en backend/
docker compose up --build
```

Esto levanta tres servicios:

- `db`: PostgreSQL 16 con volumen persistente (`postgres_data`) y healthcheck.
- `backend`: FastAPI, que espera a que `db` esté saludable antes de iniciar y se conecta a
  través del nombre de servicio `db` (no localhost, no IP fija).
- `frontend`: Angular (Nginx), en `http://localhost:4200`.

Detener los contenedores:

```bash
docker compose down
```

Detener y borrar también el volumen de datos (⚠️ elimina los datos de PostgreSQL):

```bash
docker compose down -v
```

## Ejecución sin Docker

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash) / .venv\Scripts\activate en cmd
pip install -r requirements.txt

# Asegúrate de tener PostgreSQL disponible y DATABASE_URL apuntando a localhost en .env

uvicorn app.main:app --reload --port 8000
```

## Migraciones (Alembic)

Alembic obtiene `target_metadata` desde `app.db.base.Base` y la URL de conexión desde
`DATABASE_URL` (variable de entorno), no desde `alembic.ini`.

```bash
# Generar una nueva migración a partir de los modelos
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones pendientes
alembic upgrade head
```

Dentro de Docker:

```bash
docker compose exec backend alembic upgrade head
```

## Tests

```bash
pytest
```

## API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `GET http://localhost:8000/api/v1/health`

## Próximos pasos

Esta base **no** implementa todavía usuarios, productos, sucursales, reservas, pagos, IA ni
realidad aumentada. Cada caso de uso se desarrollará posteriormente siguiendo PUDS, verificando
primero el modelo UML de dominio correspondiente antes de crear modelos SQLAlchemy y migraciones.
