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
    "data_cache",
    "agent-transcripts",
    "terminals",
    "canvases",
}
SKIP_FILES = {".env", "dev.db", "dev.db-journal", "dev.db-wal", "dev.db-shm"}
SKIP_SUFFIXES = {".pyc", ".log", ".tar", ".tar.gz", ".zip"}


def log(msg: str) -> None:
    print(msg, flush=True)


def make_tarball() -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    tmp.close()
    count = 0
    with tarfile.open(tmp.name, "w:gz") as tar:
        for p in ROOT.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if rel.name in SKIP_FILES:
                continue
            if rel.suffix.lower() in SKIP_SUFFIXES:
                continue
            # Skip local SQLite copies under prisma/
            if rel.suffix == ".db" or str(rel).endswith(".db-journal"):
                continue
            tar.add(p, arcname=str(rel).replace("\\", "/"))
            count += 1
            if count % 500 == 0:
                log(f"  … packed {count} files")
    log(f"Packed {count} files → {tmp.name}")
    return Path(tmp.name)


def run_ssh(client: paramiko.SSHClient, cmd: str, timeout: int = 7200) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, get_pty=True, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def main() -> int:
    host = os.environ.get("DO_HOST", "188.166.214.47")
    user = os.environ.get("DO_USER", "root")
    password = os.environ.get("DO_PASSWORD")
    promote = os.environ.get("DO_PROMOTE_LAB", "1") == "1"
    if not password:
        print("Set DO_PASSWORD (and optionally DO_HOST, DO_USER).", file=sys.stderr)
        return 1

    env_local = ROOT / ".env"
    if not env_local.is_file():
        print("Missing local .env — create from .env.example before deploy.", file=sys.stderr)
        return 1

    log(f"Packaging {ROOT}…")
    tarball = make_tarball()
    size = tarball.stat().st_size
    log(f"Tarball size: {size:,} bytes")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log(f"Connecting to {user}@{host}…")
    client.connect(host, username=user, password=password, timeout=90, banner_timeout=90, auth_timeout=90)

    sftp = client.open_sftp()
    remote_tar = "/tmp/quant-buffet.tar.gz"
    log(f"Uploading {size:,} bytes…")
    sftp.put(str(tarball), remote_tar)
    tarball.unlink(missing_ok=True)
    log("Upload complete.")

    run_ssh(client, f"mkdir -p {APP_DIR}")
    log("Extracting on server…")
    code, out, err = run_ssh(
        client,
        f"tar -xzf {remote_tar} -C {APP_DIR} && rm -f {remote_tar}",
    )
    if code != 0:
        print(out, err, file=sys.stderr)
        return code
    log("Extracted.")

    sftp.put(str(env_local), f"{APP_DIR}/.env")
    log("Uploaded .env")

    log("Running install.sh (npm/prisma/build/pm2)…")
    code, out, err = run_ssh(
        client,
        f"chmod +x {APP_DIR}/deploy/digitalocean/*.sh && QB_DOMAIN=www.quantbuffet.com bash {APP_DIR}/deploy/digitalocean/install.sh",
        timeout=7200,
    )
    print(out, flush=True)
    if err:
        print(err, file=sys.stderr)
    if code != 0:
        client.close()
        return code

    if promote:
        log("Promoting lab strategies on production DB…")
        code, out, err = run_ssh(
            client,
            f"cd {APP_DIR} && chmod +x deploy/digitalocean/promote-lab.sh && "
            f"DATABASE_URL='file:/var/lib/quant-buffet/dev.db' bash deploy/digitalocean/promote-lab.sh",
            timeout=7200,
        )
        print(out, flush=True)
        if err:
            print(err, file=sys.stderr)
        if code != 0:
            client.close()
            return code

    client.close()
    log("Deploy finished OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
