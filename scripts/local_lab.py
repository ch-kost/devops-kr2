"""Host launcher for the isolated Docker Desktop lab; never copies its secrets out."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
variant = sys.argv[1] if len(sys.argv) > 1 else "1"
if variant not in ("1", "2", "3", "4"):
    raise SystemExit("Variant must be 1, 2, 3 or 4")
args = sys.argv[2:] or ["start"]
if args == ["build-tools"]:
    raise SystemExit(subprocess.call(["docker", "build", "-f", "Dockerfile.lab-tools", "-t", "kr2-lab-tools:local", "."], cwd=root))
for volume in ("kr2-chugunov-local-work", "kr2-chugunov-local-certs"):
    subprocess.run(["docker", "volume", "create", volume], check=True, stdout=subprocess.DEVNULL)
command = ["docker", "run", "--rm", "--init", "-e", f"KR2_VARIANT={variant}",
           "--mount", f"type=bind,source={root},target=/src,readonly",
           "--mount", "type=volume,source=kr2-chugunov-local-work,target=/work",
           "--mount", "type=volume,source=kr2-chugunov-local-certs,target=/certs",
           "--mount", "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock",
           "kr2-lab-tools:local", "bash", "/src/scripts/local-lab.sh", *args]
raise SystemExit(subprocess.call(command, cwd=root))
