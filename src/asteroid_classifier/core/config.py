import hydra
from omegaconf import DictConfig
from pathlib import Path
from dotenv import load_dotenv

CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs"
ROOT_DIR = Path(__file__).resolve().parents[3]

# Load variables from root .env before Hydra initializes
load_dotenv(ROOT_DIR / ".env")


def get_config(config_name: str = "config") -> DictConfig:
    """
    Utility to load Hydra configuration programmatically.
    Use this when not using @hydra.main decorator.
    """
    with hydra.initialize_config_dir(config_dir=str(CONFIG_DIR), version_base="1.3"):
        cfg = hydra.compose(config_name=config_name)
        return cfg
