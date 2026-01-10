import sys
import os
from pathlib import Path

# Get the absolute path of the project root directory
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))