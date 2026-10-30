"""Print paths only if the current Redis password leaked; never print the value."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
env = root / ".env"
password = next((s.split("=", 1)[1] for s in env.read_text().splitlines() if s.startswith("REDIS_PASSWORD=")), "") if env.exists() else ""
tracked = [] if "--delivered-only" in sys.argv else subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
bad = [p for p in tracked if p and (Path(p).name == ".env" or Path(p).suffix in (".key", ".pem"))]
if password:
    for path in root.rglob("*"):
        if not path.is_file() or path == env or ".git" in path.parts or ".venv" in path.parts:
            continue
        if password.encode() in path.read_bytes():
            bad.append(str(path.relative_to(root)))
if bad:
    print("Secret-related files found:")
    print("\n".join(sorted(set(bad))))
    raise SystemExit(1)
print("No server .env/key is tracked; current Redis secret not found in delivered files")
