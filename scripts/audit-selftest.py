"""Test the real audit with command fixtures, without exposing a live host port."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

source = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="kr2-audit-test-") as tmp:
    root = Path(tmp)
    for directory in ("scripts", "variants", "bin"):
        (root / directory).mkdir()
    for name in ("audit-kr2.sh", "compose.sh"):
        shutil.copy2(source / "scripts" / name, root / "scripts" / name)
        (root / "scripts" / name).chmod(0o700)
    shutil.copy2(source / "variants/1.env", root / "variants/1.env")
    (root / ".env").write_text("REDIS_PASSWORD=fixture-only\n")
    (root / ".env").chmod(0o600)
    config = root / "kr2.conf"
    config.write_text("# Audit fixture only\n")
    link = root / "kr2-enabled"
    link.symlink_to(config)
    docker = root / "bin/docker"
    docker.write_text('''#!/usr/bin/env bash
if [[ $1 == inspect ]]; then echo healthy
elif [[ " $* " == *" ps -q redis "* ]]; then echo fixture-redis
elif [[ " $* " == *" port app 8001 "* ]]; then echo "$MOCK_PORT"
else exit 2
fi
''')
    docker.chmod(0o700)
    openssl = root / "bin/openssl"
    openssl.write_text("#!/usr/bin/env bash\necho 'Certificate will not expire (fixture)'\n")
    openssl.chmod(0o700)
    env = dict(os.environ, PATH=str(root / "bin") + ":" + os.environ["PATH"],
               KR2_SITE_LINK=str(link), KR2_SITE_CONFIG=str(config), KR2_CERT_PATH=str(root / "fixture.crt"))
    for label, port, expected in (("positive", "127.0.0.1:8001", 0), ("negative wildcard mapping", "0.0.0.0:8001", 1), ("restored", "127.0.0.1:8001", 0)):
        print(f"\nAudit fixture: {label}", flush=True)
        result = subprocess.run(["bash", str(root / "scripts/audit-kr2.sh"), "1"], env=dict(env, MOCK_PORT=port))
        print(f"exit={result.returncode}; expected={expected}", flush=True)
        if result.returncode != expected:
            raise SystemExit(1)
print("Audit negative-path self-test passed; no live port was exposed")
