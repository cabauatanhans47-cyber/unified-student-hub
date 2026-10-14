from pathlib import Path
from shutil import copytree
root=Path(__file__).resolve().parents[1]
copytree(root/'frontend'/'dist',root/'public',dirs_exist_ok=True)
