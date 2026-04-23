from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "unit-test-secret")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:3000"]')
