import sys
from pathlib import Path
import unittest
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(root / "tests")))
sys.exit(not result.wasSuccessful())
