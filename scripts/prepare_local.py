"""Generate local-only Linux-volume state. Does not claim to configure devops-vm."""
from pathlib import Path
import subprocess
import sys

root = Path("/work")
certs = Path("/certs")
variant = int(sys.argv[1])
if variant not in (1, 2, 3, 4):
    raise SystemExit("Invalid variant")
name = ("api", "notes", "stats", "kv")[variant - 1]
domain = f"{name}.devops.local"
port = str(8000 + variant)
if not (root / ".env").exists():
    subprocess.run(["python3", str(root / "scripts/init_env.py")], check=True)
if not (certs / "kr2.crt").exists():
    subprocess.run(["openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048", "-days", "365",
                    "-keyout", str(certs / "kr2.key"), "-out", str(certs / "kr2.crt"),
                    "-subj", f"/CN={domain}", "-addext", f"subjectAltName=DNS:{domain}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
(certs / "kr2.key").chmod(0o600)
config = (root / "nginx/kr2.conf.template").read_text().replace("__DOMAIN__", domain).replace("__PORT__", port)
config = config.replace("http://127.0.0.1:", "http://app:").replace("/etc/ssl/certs/kr2.crt", "/etc/kr2/kr2.crt").replace("/etc/ssl/private/kr2.key", "/etc/kr2/kr2.key")
(certs / "nginx.conf").write_text("events {}\nhttp {\n" + config + "\n}\n")
print(f"Local lab prepared for provisional variant {variant}: {domain}, application {port}")
print("Secret and private key remain only in Linux Docker volumes")
