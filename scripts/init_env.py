"""Create a new server-only Redis secret without printing it or overwriting it."""
import os
from pathlib import Path
import secrets
import stat

path = Path(__file__).resolve().parents[1] / ".env"
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env already exists; refusing to overwrite the server secret")
with os.fdopen(fd, "w", encoding="ascii", newline="\n") as handle:
    handle.write(f"REDIS_PASSWORD={secrets.token_hex(32)}\n")
if os.name == "posix":
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    print("Created server-only .env with mode 600; password not displayed")
else:
    print("Created local test .env; POSIX mode 600 must be verified on the Linux server")
