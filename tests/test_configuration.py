"""Verify security-relevant invariants and all four variant configurations."""
import json
from pathlib import Path
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def test_application_logic_and_requirements_match_template(self):
        for name in ("app.py", "requirements.txt"):
            original = subprocess.check_output(["git", "show", f"main:{name}"], cwd=ROOT).decode().replace("\r\n", "\n")
            current = (ROOT / name).read_text().replace("\r\n", "\n")
            if current.startswith("# KR2: Chugunov\n"):
                current = current.split("\n", 1)[1]
            self.assertEqual(original, current, name)

    def test_compose_isolation_and_secret_delivery(self):
        cfg = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
        app, redis = (cfg["services"][name] for name in ("app", "redis"))
        self.assertEqual(app["env_file"], ".env")
        self.assertEqual(redis["env_file"], ".env")
        self.assertEqual(app["environment"]["REDIS_HOST"], "redis")
        self.assertTrue(all(p.startswith("127.0.0.1:") for p in app["ports"]))
        self.assertNotIn("ports", redis)
        self.assertEqual(app["depends_on"]["redis"]["condition"], "service_healthy")
        self.assertTrue(cfg["networks"]["backend"]["internal"])
        self.assertEqual(redis["command"][0], "redis-server")
        self.assertIn("${REDIS_PASSWORD:?", redis["command"][-1])
        self.assertIn("$$REDIS_PASSWORD", redis["healthcheck"]["test"][1])
        self.assertEqual(redis["volumes"], ["redis_data:/data"])
        self.assertIn("redis_data", cfg["volumes"])
        for service in (app, redis):
            self.assertEqual(service["networks"], ["backend"])
            self.assertEqual(service["restart"], "unless-stopped")

    def test_dockerfile_exec_user_cache_and_context(self):
        lines = (ROOT / "Dockerfile").read_text().splitlines()
        self.assertEqual(lines[0], "FROM python:3.12-slim")
        self.assertIn("USER 10001:10001", lines)
        cmd = next(line[4:] for line in lines if line.startswith("CMD "))
        self.assertEqual(json.loads(cmd)[0], "gunicorn")
        self.assertLess(next(i for i,l in enumerate(lines) if l.startswith("COPY requirements")), next(i for i,l in enumerate(lines) if l.startswith("COPY --chown")))
        self.assertNotIn("COPY . .", lines)
        self.assertIn(".env", (ROOT / ".dockerignore").read_text().splitlines())
        self.assertIn(".env", (ROOT / ".gitignore").read_text().splitlines())

    def test_four_variants(self):
        names = ("api", "notes", "stats", "kv")
        for number, name in enumerate(names, 1):
            config = (ROOT / "variants" / f"{number}.env").read_text()
            self.assertIn(f"APP_PORT={8000+number}", config)
            self.assertIn(f"APP_DOMAIN={name}.devops.local", config)

    def test_nginx_preserves_forwarded_context_and_tls(self):
        config = (ROOT / "nginx/kr2.conf.template").read_text()
        for fragment in ("return 301 https://$host$request_uri;", "ssl_certificate /etc/ssl/certs/kr2.crt;", "proxy_pass http://127.0.0.1:__PORT__;", "proxy_set_header X-Real-IP $remote_addr;", "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;", "proxy_set_header X-Forwarded-Proto $scheme;", "proxy_set_header Host $host;"):
            self.assertIn(fragment, config)


if __name__ == "__main__":
    unittest.main(verbosity=2)
