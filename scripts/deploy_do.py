"""Deploy Quant Buffet to DigitalOcean droplet via SSH/SCP.

Usage (never commit passwords):
    set DO_HOST=188.166.214.47
    set DO_USER=root
    set DO_PASSWORD=your-root-password
    python scripts/deploy_do.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Installing paramiko…", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = "/opt/quant-buffet"
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "__pycache__",
    ".env",
}
SKIP_FILES = {".env"}


def make_tarball() -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    tmp.close()
    with tarfile.open(tmp.name, "w:gz") as tar:
        for p in ROOT.rglob("*"):
            if p.is_file():
                rel = p.relative_to(ROOT)
                if any(part in SKIP_DIRS for part in rel.parts):
                    continue
                if rel.name in SKIP_FILES:
                    continue
                if rel.suffix in (".pyc", ".log"):
                    continue
                tar.add(p, arcname=str(rel).replace("\\", "/"))
    return Path(tmp.name)


def run_ssh(client: paramiko.SSHClient, cmd: str) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def main() -> int:
    host = os.environ.get("DO_HOST", "188.166.214.47")
    user = os.environ.get("DO_USER", "root")
    password = os.environ.get("DO_PASSWORD")
    if not password:
        print("Set DO_PASSWORD (and optionally DO_HOST, DO_USER).", file=sys.stderr)
        return 1

    env_local = ROOT / ".env"
    if not env_local.is_file():
        print("Missing local .env — create from .env.example before deploy.", file=sys.stderr)
        return 1

    print(f"Packaging {ROOT}…")
    tarball = make_tarball()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {user}@{host}…")
    client.connect(host, username=user, password=password, timeout=90)

    sftp = client.open_sftp()
    remote_tar = "/tmp/quant-buffet.tar.gz"
    print(f"Uploading {tarball.stat().st_size:,} bytes…")
    sftp.put(str(tarball), remote_tar)
    tarball.unlink(missing_ok=True)

    run_ssh(client, f"mkdir -p {APP_DIR}")
    code, out, err = run_ssh(
        client,
        f"tar -xzf {remote_tar} -C {APP_DIR} && rm -f {remote_tar}",
    )
    if code != 0:
        print(out, err, file=sys.stderr)
        return code

    sftp.put(str(env_local), f"{APP_DIR}/.env")
    print("Uploaded .env (review AUTH_URL and Stripe keys on server).")

    code, out, err = run_ssh(
        client,
        f"chmod +x {APP_DIR}/deploy/digitalocean/*.sh && QB_DOMAIN=www.quantbuffet.com bash {APP_DIR}/deploy/digitalocean/install.sh",
    )
    print(out)
    if err:
        print(err, file=sys.stderr)
    client.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
