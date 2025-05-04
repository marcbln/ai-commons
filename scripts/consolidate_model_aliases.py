import yaml
from pathlib import Path

def consolidate_aliases(source1_path: Path, source2_path: Path, target_path: Path):
    """
    Consolidates model aliases from two source YAML files into a target YAML file.

    Args:
        source1_path: Path to the first source YAML file.
        source2_path: Path to the second source YAML file (takes precedence in conflicts).
        target_path: Path to the target YAML file.
    """
    aliases1 = {}
    aliases2 = {}

    try:
        with source1_path.open('r') as f:
            aliases1 = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Error: Source file not found at {source1_path}")
        return False
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {source1_path}: {e}")
        return False

    try:
        with source2_path.open('r') as f:
            aliases2 = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Error: Source file not found at {source2_path}")
        return False
    except yaml.YAMLError as e:
        print(f"Error parsing YAML from {source2_path}: {e}")
        return False

    # Merge dictionaries, with aliases2 taking precedence
    merged_aliases = {**aliases1, **aliases2}

    try:
        # Ensure the target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open('w') as f:
            yaml.dump(merged_aliases, f, default_flow_style=False)
    except yaml.YAMLError as e:
        print(f"Error writing YAML to {target_path}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while writing to {target_path}: {e}")
        return False

    return True

if __name__ == "__main__":
    source1 = Path("aicoder/config/model-aliases.yaml")
    source2 = Path("ai-git-summarize/config/model-aliases.yaml")
    target = Path("ai-commons/src/ai_commons/data/model-aliases.yaml")

    print(f"Consolidating aliases from {source1} and {source2} into {target}...")
    if consolidate_aliases(source1, source2, target):
        print("Consolidation successful.")
    else:
        print("Consolidation failed.")