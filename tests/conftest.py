"""Pytest configuration file."""

import sys
from pathlib import Path

# Add the package directory to Python path
package_dir = Path(__file__).parent.parent / "open-llms-play-pokemon"
sys.path.insert(0, str(package_dir))
