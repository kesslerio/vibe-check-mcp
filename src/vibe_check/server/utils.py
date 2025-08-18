from pathlib import Path
import json

def get_version():
    """Reads the version from VERSION file or package.json."""
    try:
        version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
        package_json = Path(__file__).parent.parent.parent.parent / "package.json"
        
        version = "unknown"
        if version_file.exists():
            version = version_file.read_text().strip()
        elif package_json.exists():
            with open(package_json) as f:
                package_data = json.load(f)
                version = package_data.get("version", "unknown")
        return version
    except Exception:
        return "unknown"
