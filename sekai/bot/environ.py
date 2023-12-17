import os
from pathlib import Path

working_dir = Path(os.getcwd())

module_path = Path(__file__).parent / "modules"

config_path = working_dir / "config"
config_path.mkdir(exist_ok=True)

data_path = working_dir / "data"
data_path.mkdir(exist_ok=True)

cache_path = data_path / "cache"
cache_path.mkdir(exist_ok=True)
