import os

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_config():
    """
    Load configuration from config.toml file.
    
    Returns:
        dict: Configuration dictionary
    """
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(os.path.dirname(current_dir))
    config_path = os.path.join(project_root, "config.toml")
    with open(config_path, "rb") as f:
        return tomllib.load(f)


_config = None


def get_config():
    """
    Get cached configuration instance.
    
    Returns:
        dict: Configuration dictionary
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
