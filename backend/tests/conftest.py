import pytest

# Ensure backend root is importable when tests are run from the tests/ dir
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytest_plugins = []
