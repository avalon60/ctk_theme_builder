import os
import sys
import tempfile
from pathlib import Path


_TEST_HOME = tempfile.mkdtemp(prefix="ctk-tb-pytest-home-")
os.environ["HOME"] = _TEST_HOME

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
