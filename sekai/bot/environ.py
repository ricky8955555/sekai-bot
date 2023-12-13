import os
from pathlib import Path

working_dir = Path(os.getcwd())

module_path = Path(__file__).parent / "modules"
config_path = working_dir / "config"
