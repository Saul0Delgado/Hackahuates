"""
Utility functions for Consumption Prediction module
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)
    return logger


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    project_root = Path(__file__).parent.parent
    full_path = project_root / config_path

    with open(full_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def get_project_root() -> Path:
    """
    Get project root directory

    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent


def ensure_dir(directory: Path) -> None:
    """
    Ensure directory exists, create if not

    Args:
        directory: Directory path
    """
    directory.mkdir(parents=True, exist_ok=True)


def get_data_path(relative_path: str) -> Path:
    """
    Get absolute path to data file

    Args:
        relative_path: Relative path from project root

    Returns:
        Absolute path
    """
    return get_project_root() / relative_path


logger = setup_logging()
