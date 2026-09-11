"""Entrypoint que usa el runtime de Python de Vercel para servir la API existente.

Vercel detecta cualquier archivo .py bajo api/ que exponga una variable ASGI
llamada `app` y la sirve como Serverless Function. La app real sigue viviendo
en app/main.py; este archivo solo la importa.
"""

import sys
from pathlib import Path

# Con "Root Directory" = backend/ en Vercel, este archivo corre desde
# backend/api/index.py. Igual que en alembic/env.py, hace falta agregar
# backend/ a sys.path para que "app.*" y "modules.*" se puedan importar.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
