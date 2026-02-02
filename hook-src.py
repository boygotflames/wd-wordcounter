# PyInstaller hook for src directory
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Get the directory containing the spec file
spec_dir = os.path.dirname(__file__)
src_dir = os.path.join(spec_dir, 'src')

if os.path.exists(src_dir):
    # Add src to Python path during build
    sys.path.insert(0, src_dir)
    
    # Collect all Python modules in src
    hiddenimports = collect_submodules('src')
    
    # Collect data files if any
    datas = collect_data_files('src')
else:
    hiddenimports = []
    datas = []