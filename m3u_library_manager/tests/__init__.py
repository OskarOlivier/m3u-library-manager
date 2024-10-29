# tests/__init__.py
# Empty file to make tests a package

# tests/conftest.py
import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# tests/test_m3u_library.py
import unittest
from pathlib import Path
import os
import tempfile
import shutil
from utils.m3u.parser import read_m3u, write_m3u, convert_path_separators, M3UParseError
from utils.m3u.path_utils import is_absolute_path, make_absolute, make_relative, verify_library_path
from core.playlist.operations import find_missing_files, validate_playlist, clean_playlist

