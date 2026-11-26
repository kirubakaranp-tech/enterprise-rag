import hashlib
import json
from pathlib import Path

REGISTRY_FILE = Path("index_registry.json")


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_registry():
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {}


def save_registry(registry):
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def needs_reindex(path, registry):
    entry = registry.get(Path(path).name)
    return entry is None or entry["hash"] != file_hash(path)
