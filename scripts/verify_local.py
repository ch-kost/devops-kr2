"""Record real, secret-free local verification evidence; no VM results are invented."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
out = root / "evidence"
out.mkdir(exist_ok=True)
runtime = root / ".runtime"
runtime.mkdir(exist_ok=True)
summary = {"environment": "Docker Desktop local Linux containers, not devops-vm", "variant": 1,
           "variant_confirmed": False, "vm_ufw_snapshots_old_resources_verified": False}


def run(label, command, expected=0):
    result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    (out / f"{label}.log").write_text("$ " + subprocess.list2cmdline(command) + "\n" + result.stdout + f"\nexit={result.returncode}\n", encoding="utf-8")
    if result.returncode != expected:
        print(f"FAIL {label}: exit={result.returncode}; inspect {out / (label+'.log')}")
        raise SystemExit(1)
    print(f"PASS {label}", flush=True)
    return result.stdout


def lab(label, *arguments):
    return run(label, [sys.executable, "scripts/local_lab.py", "1", *arguments])


mode = sys.argv[1] if len(sys.argv) > 1 else "final"
if mode == "baseline":
    lab("baseline-sync", "sync")
    lab("fresh-build", "build", "--no-cache", "app")
    raise SystemExit(0)

lab("final-sync", "sync")
build = lab("comment-rebuild", "build", "app")
assert "CACHED" in build
lab("start-final", "up", "-d", "--wait", "--wait-timeout", "120")
run("unit-static-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
summary["tests"] = 9
summary["docker_server"] = run("docker-server", ["docker", "version", "--format", "{{.Server.Version}}" ]).strip()
summary["compose"] = run("compose-version", ["docker", "compose", "version"]).strip()
summary["id"] = run("image-uid", ["docker", "run", "--rm", "kr2-app:1.0", "id"]).strip()
assert "uid=10001" in summary["id"]
summary["cmd"] = json.loads(run("image-cmd", ["docker", "inspect", "-f", "{{json .Config.Cmd}}", "kr2-app:1.0"]))
assert summary["cmd"][0] == "gunicorn"
empty = run("image-no-env", ["docker", "run", "--rm", "--user", "root", "kr2-app:1.0", "find", "/", "-xdev", "-name", ".env"])
assert not empty.strip()
lab("container-status", "ps")
lab("process-users", "top")
summary["app_proc_uid"] = run("app-proc-uid", ["docker", "exec", "kr2-chugunov-local-app-1", "sh", "-c", "grep '^Uid:' /proc/1/status"]).strip()
summary["redis_proc_uid"] = run("redis-proc-uid", ["docker", "exec", "kr2-chugunov-local-redis-1", "sh", "-c", "grep '^Uid:' /proc/1/status"]).strip()
assert summary["redis_proc_uid"].split()[1] != "0"
summary["app_port"] = lab("app-publication", "port", "app", "8001").strip()
assert summary["app_port"] == "127.0.0.1:8001"
summary["redis_ports"] = run("redis-no-publication", ["docker", "port", "kr2-chugunov-local-redis-1"]).strip()
assert not summary["redis_ports"]
lab("docker-dns", "exec", "-T", "app", "getent", "hosts", "redis")
noauth = lab("redis-auth-required", "exec", "-T", "redis", "redis-cli", "ping")
assert "NOAUTH" in noauth
lab("secret-check", "secret-check")
curl = "curl.exe" if sys.platform == "win32" else "curl"
health = run("health", [curl, "--noproxy", "*", "-fsS", "http://127.0.0.1:8001/health"])
assert health == "ok\n"
redirect = run("http-redirect", [curl, "--noproxy", "*", "-sS", "-I", "-H", "Host: api.devops.local", "http://127.0.0.1:18080/"])
assert "301" in redirect and "Location: https://api.devops.local/" in redirect
cert = subprocess.check_output(["docker", "run", "--rm", "-v", "kr2-chugunov-local-certs:/certs:ro", "kr2-lab-tools:local", "cat", "/certs/kr2.crt"])
(runtime / "kr2.crt").write_bytes(cert)
run("certificate-san", ["docker", "run", "--rm", "-v", "kr2-chugunov-local-certs:/certs:ro", "kr2-lab-tools:local", "openssl", "x509", "-in", "/certs/kr2.crt", "-noout", "-subject", "-dates", "-ext", "subjectAltName"])
prefix = [curl, "--noproxy", "*", "--resolve", "api.devops.local:18443:127.0.0.1"]
run("https-untrusted", prefix + ["-sS", "https://api.devops.local:18443/health"], expected=60)
trusted = prefix + ["--cacert", str(runtime / "kr2.crt"), "-fsS"]
summary["whoami"] = run("https-whoami", trusted + ["https://api.devops.local:18443/whoami"]).strip()
assert "scheme: https" in summary["whoami"] and "host: api.devops.local" in summary["whoami"]
before = run("counter-before-down", trusted + ["https://api.devops.local:18443/"])
summary["counter_before_down"] = int(re.search(r"hits: (\d+)", before).group(1))
lab("down-preserves-volume", "down")
run("redis-volume-preserved", ["docker", "volume", "inspect", "-f", "{{.Name}}", "kr2-chugunov-local_redis_data"])
lab("up-after-down", "up", "-d", "--wait", "--wait-timeout", "120")
after = run("counter-after-down", trusted + ["https://api.devops.local:18443/"])
summary["counter_after_down"] = int(re.search(r"hits: (\d+)", after).group(1))
assert summary["counter_after_down"] > summary["counter_before_down"]
run("start-stop-test", ["docker", "run", "-d", "--rm", "--name", "kr2-chugunov-stop-test", "-p", "127.0.0.1:19001:8001", "kr2-app:1.0"])
time.sleep(1)
run("stop-test-health", [curl, "--noproxy", "*", "-fsS", "http://127.0.0.1:19001/health"])
start = time.monotonic()
run("graceful-stop", ["docker", "stop", "kr2-chugunov-stop-test"])
summary["stop_seconds"] = round(time.monotonic() - start, 3)
assert summary["stop_seconds"] < 10
summary["all_local_checks_passed"] = True
(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
