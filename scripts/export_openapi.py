"""Write the OpenAPI document. Does not open a database connection."""

import json
import os
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./openapi.sqlite")
os.environ.setdefault("QDRANT_URL", "memory")
os.environ.setdefault("DEV_AUTH", "true")

from app.main import app  # noqa: E402

target = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2))
print(target)
