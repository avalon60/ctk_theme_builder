import os
import tempfile


_TEST_HOME = tempfile.mkdtemp(prefix="ctk-tb-pytest-home-")
os.environ["HOME"] = _TEST_HOME
