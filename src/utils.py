import yaml

def extract_config(
    file_path: str
):
    """
    Extract configuration from a YAML file.

    Args:
        file_path (str): Path to the YAML configuration file.

    Returns:
        dict: Configuration parameters, or an empty dict if file not found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        print(f"Warning: Configuration file {file_path} not found.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}")
        return {}
    