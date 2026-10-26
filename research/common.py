"""Configuration, provenance, and immutable run artifacts; standard library only."""
import hashlib
import json
import platform
import subprocess
import time
import uuid
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = "07635fdfb53f6a1a4e9b38488ab48c8febc56e58"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_config(path):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Expected a JSON object with schema_version=1")
    return data


def check_deadline(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("Research time budget exhausted")


def provenance(config):
    def git(*args):
        result = subprocess.run(["git", *args], cwd=ROOT, text=True,
                                capture_output=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    source_paths = [ROOT / "ca.py", *sorted((ROOT / "research").glob("*.py"))]
    return {
        "upstream_commit": UPSTREAM_COMMIT,
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "zlib": zlib.ZLIB_RUNTIME_VERSION,
        "config_sha256": digest(json.dumps(config, sort_keys=True).encode()),
        "source_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes())
                          for p in source_paths},
    }


def save_run(config, results, output_root="runs", max_bytes=8_388_608):
    """A fresh directory per invocation, never overwrite an earlier result."""
    payloads = {
        "config.json": config,
        "manifest.json": provenance(config),
        "results.json": results,
    }
    encoded = {name: (json.dumps(value, indent=2, sort_keys=True,
                                allow_nan=False) + "\n").encode()
               for name, value in payloads.items()}
    if sum(map(len, encoded.values())) > max_bytes:
        raise ValueError("Artifact size exceeds the output budget")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                     + "-" + uuid.uuid4().hex[:10])
    target.mkdir()
    for name, data in encoded.items():
        (target / name).write_bytes(data)
    return target
